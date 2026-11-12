"""Download a bounded, revision-pinned Docker documentation corpus (no indexing)."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / "data" / "docker_official"
TOPICS = {
    "networking": "content/manuals/engine/network/",
    "storage": "content/manuals/engine/storage/",
    "compose": "content/manuals/compose/how-tos/",
}


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "RAG-document-research"}), timeout=60) as response:
        return response.read()


def main():
    if ROOT.exists():
        raise SystemExit(f"Destination already exists; refusing overwrite: {ROOT}")
    commit = json.loads(fetch("https://api.github.com/repos/docker/docs/commits/main"))["sha"]
    tree = json.loads(fetch(f"https://api.github.com/repos/docker/docs/git/trees/{commit}?recursive=1"))
    if tree.get("truncated"):
        raise RuntimeError("GitHub tree truncated")
    pools = {
        topic: sorted(x["path"] for x in tree["tree"]
                      if x["type"] == "blob" and x["path"].startswith(prefix)
                      and x["path"].endswith(".md"))
        for topic, prefix in TOPICS.items()
    }
    selected = []
    # Round-robin balances the three business areas; cap at 60 source pages.
    while len(selected) < 60 and any(pools.values()):
        for topic, paths in pools.items():
            if paths and len(selected) < 60:
                selected.append((topic, paths.pop(0)))
    records = []
    ROOT.mkdir(parents=True)
    for topic, path in selected:
        data = fetch(f"https://raw.githubusercontent.com/docker/docs/{commit}/{path}")
        data.decode("utf-8-sig")
        target = ROOT / "raw" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append({"topic": topic, "repository_path": path,
                        "local_path": target.relative_to(ROOT).as_posix(),
                        "source_url": f"https://github.com/docker/docs/blob/{commit}/{path}",
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                        "contains_shortcode": b"{{" in data,
                        "contains_html_comment": b"<!--" in data})
    for name in ("LICENSE", "NOTICE"):
        if any(x["path"] == name for x in tree["tree"]):
            (ROOT / name).write_bytes(fetch(f"https://raw.githubusercontent.com/docker/docs/{commit}/{name}"))
    manifest = {"repository": "https://github.com/docker/docs", "commit": commit,
                "selection": "Round-robin sorted Markdown paths from engine/network, engine/storage, compose/how-tos; maximum 60",
                "status": "raw_sources_only_not_parsed_or_indexed", "documents": records}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "README.md").write_text(
        "# Docker official documentation: raw corpus\n\n"
        f"Source: https://github.com/docker/docs\n\nRevision: {commit}\n\n"
        f"Downloaded pages: {len(records)}. Scope: container networking, storage, and Compose how-tos.\n\n"
        "Original Markdown is preserved. These files are not yet parsed or indexed. "
        "Front matter, Hugo shortcodes, includes and links require preprocessing review. "
        "Some included examples may live outside this subset. No reference answers have been validated.\n\n"
        "License: Apache-2.0; see LICENSE and any NOTICE. Preserve upstream attribution and "
        "review any file-specific notices before redistributing. Docker is the upstream author; "
        "this corpus is an independent educational selection, not an official Docker assistant.\n\n"
        "See manifest.json for per-file immutable source URLs, hashes and byte sizes.\n",
        encoding="utf-8")
    counts = {topic: sum(r["topic"] == topic for r in records) for topic in TOPICS}
    print(json.dumps({"commit": commit, "pages": len(records), "topics": counts,
                      "bytes": sum(r["bytes"] for r in records), "directory": str(ROOT)}, indent=2))


if __name__ == "__main__":
    main()
