import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from document_processor import parse_markdown, load_document, load_corpus
from ingestion import chunk_records
from evaluation.dataset import read_dataset

class ParsingTests(unittest.TestCase):
    def test_markdown_preserves_code_and_locations(self):
        text = '\n'.join(['---', 'title: Storage', '---', '<!-- hidden -->', '## Example',
                          '```sh', '# not a heading', "docker inspect --format '{{ json .Mounts }}'", '```',
                          '{{< tabs >}}', '{{< tab name="Linux" >}}', 'visible', '{{< /tab >}}', '{{< /tabs >}}'])
        docs = parse_markdown(text, {'filename': 'x.md'})
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata['line_start'], 5)
        self.assertNotIn('hidden', docs[0].page_content)
        self.assertIn("{{ json .Mounts }}", docs[0].page_content)
        self.assertIn('# not a heading', docs[0].page_content)
        self.assertIn('Example: Linux', docs[0].page_content)
        self.assertEqual(docs[0].metadata['parser_warnings'], '[]')

    def test_unknown_template_is_flagged(self):
        docs = parse_markdown('## A\n{{% include "not-present.md" %}}', {'filename': 'x.md'})
        self.assertTrue(json.loads(docs[0].metadata['parser_warnings']))

    def test_docx_tables_and_paragraphs(self):
        from docx import Document
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'x.docx'
            word = Document()
            word.add_paragraph('Intro')
            table = word.add_table(rows=1, cols=2)
            table.cell(0, 0).text = 'Setting'
            table.cell(0, 1).text = 'Value'
            word.add_paragraph('Tail')
            word.save(path)
            result = load_document(path)
            content = '\n'.join(d.page_content for d in result)
            self.assertLess(content.index('Intro'), content.index('Setting'))
            self.assertLess(content.index('Value'), content.index('Tail'))

    def test_real_corpus_checksums_templates_and_conditions(self):
        docs = load_corpus()
        self.assertGreater(len(docs), 500)
        self.assertTrue(all(json.loads(d.metadata.get('parser_warnings', '[]')) == [] for d in docs))
        self.assertTrue(any('Feature conditions:' in d.page_content and '2.22.0' in d.page_content for d in docs))
        self.assertTrue(any('content/includes/compose/secrets.md' in d.metadata['source'] for d in docs))
        self.assertTrue(all('https://github.com/docker/docs/blob/' in d.metadata['source'] for d in docs))

    def test_chunk_ids_stable_when_unrelated_document_added(self):
        from langchain_core.documents import Document
        a = Document(page_content='one', metadata={'document_id': 'A'})
        b = Document(page_content='two', metadata={'document_id': 'B'})
        first = chunk_records([a])[0]['id']
        second = chunk_records([b, a])[1]['id']
        self.assertEqual(first, second)

class EvaluationTests(unittest.TestCase):
    def test_candidates_cannot_be_evaluated_as_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.jsonl'
            row = dict(id='q1', question='What?', category='fact', answerable=True,
                       verification_status='candidate_review_required', split='dev')
            path.write_text(json.dumps(row), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'No verified'):
                read_dataset(path, verified_only=True)

    def test_verified_requires_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.jsonl'
            row = dict(id='q1', question='What?', category='fact', answerable=True,
                       verification_status='verified', split='dev', reference_answer='yes')
            path.write_text(json.dumps(row), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'lacks answer/evidence'):
                read_dataset(path)

class UploadTests(unittest.TestCase):
    def test_path_traversal_rejected_without_db(self):
        from upload_service import upload_and_index
        with self.assertRaisesRegex(ValueError, 'Invalid filename'):
            upload_and_index('../escape.md', b'text')

    def test_duplicate_does_not_load_model(self):
        from upload_service import upload_and_index
        collection = Mock()
        collection.get.return_value = {'ids': ['existing']}
        collection.count.return_value = 1
        with patch('upload_service.get_collection', return_value=collection), patch('upload_service.chunk_documents') as chunk:
            result = upload_and_index('x.md', b'text')
            self.assertEqual(result['status'], 'duplicate')
            chunk.assert_not_called()

    def test_failed_upload_rolls_back_file_and_vectors(self):
        import upload_service
        collection = Mock()
        collection.get.return_value = {'ids': []}
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(upload_service, 'UPLOAD_DIR', Path(tmp)), \
             patch.object(upload_service, 'get_collection', return_value=collection), \
             patch.object(upload_service, 'chunk_documents', side_effect=RuntimeError('model unavailable')):
            with self.assertRaises(RuntimeError):
                upload_service.upload_and_index('x.md', b'## Hello\nSome text')
            self.assertFalse((Path(tmp) / 'x.md').exists())
            collection.delete.assert_called_once()

class RetrievalTests(unittest.TestCase):
    def test_rerank_and_baseline_share_candidates(self):
        import retriever
        raw = dict(documents=[['a', 'b']], metadatas=[[{}, {}]], ids=[['A', 'B']], distances=[[0.1, 0.2]])
        with patch.object(retriever, 'retrieve', return_value=raw), patch.object(retriever, 'get_reranker') as model:
            model.return_value.compute_score.return_value = [0.2, 0.9]
            ranked = retriever.retrieve_trace('question', top_k=2, final_k=1)
            baseline = retriever.retrieve_trace('question', top_k=2, final_k=1, use_reranker=False)
            self.assertEqual(ranked['selected'][0]['chunk_id'], 'B')
            self.assertEqual(baseline['selected'][0]['chunk_id'], 'A')
            self.assertEqual(ranked['candidates'], baseline['candidates'])

class APIContractTests(unittest.TestCase):
    def setUp(self):
        from api import app, sessions
        from fastapi.testclient import TestClient
        sessions.clear()
        self.client = TestClient(app)

    def test_health_and_missing_index(self):
        from vector_store import IndexNotReady
        self.assertEqual(self.client.get('/health').status_code, 200)
        with patch('api.get_collection', side_effect=IndexNotReady('not built')):
            self.assertEqual(self.client.get('/ready').status_code, 503)

    def test_chat_and_session_history(self):
        import api
        result = dict(answer='Answer [1]', search_query='standalone', sources=[dict(citation='[1]', source='test')])
        with patch.object(api.rag_chain, 'invoke', return_value=result):
            response = self.client.post('/chat', json=dict(session_id='s1', question='question'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['answer'], 'Answer [1]')
        self.assertEqual(api.get_history('s1')[-1]['content'], 'Answer [1]')

    def test_sse_event_contract(self):
        import api
        events = [dict(type='metadata', search_query='q'), dict(type='token', content='hello'),
                  dict(type='done', answer='hello', sources=[])]
        with patch.object(api, 'get_collection'), patch.object(api, 'stream_rag', return_value=iter(events)):
            response = self.client.post('/chat/stream', json=dict(session_id='stream', question='q'))
        parsed = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
        self.assertEqual([p['type'] for p in parsed], ['metadata', 'token', 'done'])
        self.assertEqual(api.get_history('stream')[-1]['content'], 'hello')

    def test_upload_route(self):
        with patch('api.upload_and_index', return_value=dict(status='duplicate')):
            response = self.client.post('/upload', files={'file': ('x.md', b'text', 'text/markdown')})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'duplicate')

class IndexContractTests(unittest.TestCase):
    def test_real_chroma_vectors_and_compatibility(self):
        import chromadb
        import vector_store
        from ingestion import index_fingerprint
        with tempfile.TemporaryDirectory() as tmp:
            client = chromadb.PersistentClient(path=tmp)
            collection = client.create_collection('contract_test', embedding_function=None,
                configuration={'hnsw': {'space': 'cosine'}},
                metadata={'status': 'ready', 'index_fingerprint': index_fingerprint()})
            collection.upsert(ids=['A', 'B'], embeddings=[[1., 0.], [0., 1.]], documents=['first', 'second'])
            self.assertEqual(collection.query(query_embeddings=[[1., 0.]], n_results=1)['ids'][0], ['A'])
            with patch.object(vector_store, 'DB_PATH', tmp), patch.object(vector_store, 'COLLECTION_NAME', 'contract_test'), patch.object(vector_store, 'get_client', return_value=client):
                self.assertEqual(vector_store.get_collection().count(), 2)
                collection.modify(metadata=dict(status='ready', index_fingerprint='wrong'))
                with self.assertRaises(vector_store.IndexNotReady):
                    vector_store.get_collection()
            # Chroma may keep handles open on Windows until the client is closed/GC'd.
            client._system.stop()

if __name__ == '__main__':
    unittest.main()
