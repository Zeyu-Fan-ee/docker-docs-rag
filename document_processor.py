"""Document parsing with source locations and no embedding-model side effects."""
import hashlib
import json
import re
from pathlib import Path
from langchain_core.documents import Document
from project_config import CORPUS_DIR, PARSER_VERSION
SUPPORTED_SUFFIXES = {'.md', '.txt', '.pdf', '.docx'}

def dependency_data():
    path = CORPUS_DIR / 'dependencies.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'files': []}

def dependency_path(repository_path):
    for item in dependency_data()['files']:
        if item['repository_path'] == repository_path:
            path = (CORPUS_DIR / item['local_path']).resolve()
            if not path.is_relative_to(CORPUS_DIR.resolve()):
                raise ValueError('Dependency path escapes corpus directory')
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise ValueError('Dependency checksum mismatch')
            return path
    return None

def clean_text(text):
    return text.replace('\x00', '').replace('\xa0', ' ').strip()

def source_metadata(path):
    path = Path(path).resolve()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = dict(source=str(path), filename=path.name, file_type=path.suffix[1:].lower(),
                document_id=digest, file_sha256=digest, parser_version=PARSER_VERSION)
    manifest = CORPUS_DIR / 'manifest.json'
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding='utf-8'))
        for item in data['documents'] + dependency_data()['files']:
            if (CORPUS_DIR / item['local_path']).resolve() == path:
                if digest != item['sha256']:
                    raise ValueError(f'Corpus checksum mismatch: {path.name}')
                meta.update(source=item['source_url'], local_path=str(path),
                            repository_path=item['repository_path'], revision=data['commit'], topic=item.get('topic', 'compose'))
                break
    return meta

def parse_markdown(text, metadata):
    lines, title = text.splitlines(), ''
    if lines and lines[0].strip() == '---':
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
        if end is None:
            raise ValueError('Unclosed Markdown front matter')
        for line in lines[1:end]:
            if line.startswith('title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
        lines[:end + 1] = [''] * (end + 1)
    fence, comment, cleaned, warnings = None, False, [], []
    for number, line in enumerate(lines, 1):
        match = re.match(r'^\s*(`{3,}|~{3,})', line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            cleaned.append((number, line, False))
            continue
        if fence:
            cleaned.append((number, line, False))
            continue
        while True:
            if comment:
                close = line.find('-->')
                if close < 0:
                    line = ''
                    break
                line, comment = line[close + 3:], False
            start = line.find('<!--')
            if start < 0:
                break
            close = line.find('-->', start + 4)
            if close >= 0:
                line = line[:start] + line[close + 3:]
            else:
                line, comment = line[:start], True
                break
        def shortcode(m):
            tag = m.group(0)
            name = re.sub(r'^\{\{[<%]\s*', '', tag).split()[0].strip('>}%')
            if name == 'tab':
                label = re.search(r'name="([^"]+)"', tag)
                return ('Example: ' + label.group(1)) if label else ''
            if name.lstrip('/') in {'tabs', 'tab'}:
                return ''
            if name.lstrip('/') == 'accordion':
                label = re.search(r'title="([^"]+)"', tag)
                return label.group(1) if label else ''
            if name == 'include':
                match = re.search(r'include\s+"([^"]+)"', tag)
                if match and dependency_path('content/includes/' + match.group(1)):
                    return '[Supporting document: ' + match.group(1) + ']'
            if name == 'param':
                match = re.search(r'param\s+"([^"]+)"', tag)
                config = dependency_path('hugo.yaml')
                if match and config:
                    import yaml
                    value = yaml.safe_load(config.read_text(encoding='utf-8')).get('params', {}).get(match.group(1))
                    if value is not None:
                        return str(value)
            if name == 'summary-bar':
                match = re.search(r'feature_name="([^"]+)"', tag)
                config = dependency_path('data/summary.yaml')
                if match and config:
                    import yaml
                    feature = yaml.safe_load(config.read_text(encoding='utf-8')).get(match.group(1))
                    if feature:
                        return 'Feature conditions: ' + json.dumps(feature, ensure_ascii=False)
            warnings.append(f'line {number}: {tag}')
            return '[Source template content requires review]'
        line = re.sub(r'\{\{[<%].*?[%>]\}\}', shortcode, line)
        cleaned.append((number, line, True))
    sections, parts, headings = [], [], []
    def flush():
        content = clean_text('\n'.join(line for _, line in parts))
        if content:
            meta = dict(metadata, title=title or metadata.get('filename', ''),
                        section=' > '.join(h[1] for h in headings) or title or 'Introduction',
                        line_start=parts[0][0], line_end=parts[-1][0],
                        parser_warnings=json.dumps(warnings, ensure_ascii=False))
            sections.append(Document(page_content=content, metadata=meta))
    for number, line, outside in cleaned:
        heading = re.match(r'^(#{1,6})\s+(.+)', line) if outside else None
        if heading:
            flush()
            parts = []
            level, label = len(heading.group(1)), heading.group(2).strip()
            headings = [h for h in headings if h[0] < level] + [(level, label)]
        parts.append((number, line))
    flush()
    return sections

def load_document(path):
    path = Path(path)
    meta = source_metadata(path)
    suffix = path.suffix.lower()
    if suffix == '.md':
        return parse_markdown(path.read_text(encoding='utf-8-sig'), meta)
    if suffix == '.txt':
        text = clean_text(path.read_text(encoding='utf-8-sig'))
        return [Document(page_content=text, metadata=meta)] if text else []
    if suffix == '.pdf':
        import pymupdf
        with pymupdf.open(str(path)) as pdf:
            return [Document(page_content=clean_text(page.get_text('text')), metadata=dict(meta, page=i))
                    for i, page in enumerate(pdf) if page.get_text('text').strip()]
    if suffix == '.docx':
        from docx import Document as WordDocument
        from docx.oxml.ns import qn
        from docx.text.paragraph import Paragraph
        from docx.table import Table
        word = WordDocument(str(path))
        docs, parts, start = [], [], 0
        for i, element in enumerate(word.element.body):
            if element.tag == qn('w:p'):
                text = Paragraph(element, word).text
            elif element.tag == qn('w:tbl'):
                text = '\n'.join(' | '.join(c.text for c in row.cells) for row in Table(element, word).rows)
            else:
                continue
            if not text.strip():
                continue
            if parts and sum(map(len, parts)) + len(text) > 2500:
                docs.append(Document(page_content='\n'.join(parts), metadata=dict(meta, block_start=start)))
                parts = []
            if not parts:
                start = i
            parts.append(text)
        if parts:
            docs.append(Document(page_content='\n'.join(parts), metadata=dict(meta, block_start=start)))
        return docs
    raise ValueError(f'Unsupported format: {suffix}')

def load_all_documents(folder):
    docs = []
    for path in sorted(Path(folder).rglob('*')):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            docs.extend(load_document(path))
    return docs

def load_corpus():
    manifest = json.loads((CORPUS_DIR / 'manifest.json').read_text(encoding='utf-8'))
    docs = []
    for item in manifest['documents']:
        path = (CORPUS_DIR / item['local_path']).resolve()
        if not path.is_relative_to(CORPUS_DIR.resolve()):
            raise ValueError('Corpus path escapes corpus directory')
        parsed = load_document(path)
        if not parsed and path.name != '_index.md':
            raise ValueError(f'No text extracted: {path}')
        docs.extend(parsed)
    for item in dependency_data()['files']:
        if item['repository_path'].startswith('content/includes/'):
            docs.extend(load_document(dependency_path(item['repository_path'])))
    return docs
