"""Compare evidence excerpt coverage and context size from saved retrieval traces."""
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def windows(text):
    words = re.findall(r"\w+", text.lower())
    return set(zip(*(words[i:] for i in range(8))))


def main():
    root = Path(__file__).resolve().parents[1]
    chunks = read_jsonl(root / "artifacts/chunks.jsonl")
    by_position = {
        (m["document_id"], m["section"], m["chunk_index"]): chunk
        for chunk in chunks for m in [chunk["metadata"]]
    }
    dev = {row["id"]: row for row in read_jsonl(root / "evaluation/datasets/dev_candidates.jsonl")}
    key_ids = {
        "TEST14": ("d029e2c4de86", "3d36ccd072c7"),
        "TEST26": ("fb9608ab184c",),
        "TEST42": ("1e797ad38fbf",),
        "TEST43": ("2f9438b6c8bc", "e01b30c90f9f"),
        "TEST46": ("85adb5385af3",),
    }
    metrics = defaultdict(list)
    for row in read_jsonl(root / "evaluation/results/retrieval_strategy_local.jsonl"):
        qid, traces = row["id"], row["traces"]
        baseline = {c["chunk_id"]: c["text"] for c in traces["10"]["selected"]}
        adjacent = baseline.copy()
        for c in traces["10"]["selected"]:
            m = c["metadata"]
            for offset in (-1, 1):
                neighbor = by_position.get((m["document_id"], m["section"], m["chunk_index"] + offset))
                if neighbor:
                    adjacent.setdefault(neighbor["id"], neighbor["text"])
        expanded = {c["chunk_id"]: c["text"] for c in traces["20"]["selected"]}
        variants = {"baseline": baseline, "wider": expanded, "neighbors": adjacent}
        if qid in dev:
            gold = set().union(*(windows(e["excerpt"]) for e in dev[qid]["evidence"]))
            assert gold
            for name, context in variants.items():
                found = set().union(*(windows(t) for t in context.values()))
                metrics[name].append((len(found & gold) / len(gold), sum(map(len, context.values()))))
        else:
            print(qid, {
                name: any(chunk_id.startswith(key_ids[qid]) for chunk_id in context)
                for name, context in variants.items()
            })
    for name, values in metrics.items():
        print(name, len(values), *(round(mean(column), 3) for column in zip(*values)))


if __name__ == "__main__":
    main()
