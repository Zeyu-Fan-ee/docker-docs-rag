
import re
import numpy as np
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embedding_model import encode_texts


# 1. 拆分句子和段落
def split_sentences(text):

    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=0
    )

    sentences = []

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if len(part) > 400:
            sentences.extend(splitter.split_text(part))
        else:
            sentences.append(part)

    return sentences


# 2. 语义切分
def semantic_split(
    doc,
    min_chars=350,
    target_chars=650,
    max_chars=900,
    overlap_chars=100
):

    sentences = split_sentences(doc.page_content)

    if not sentences:
        return []

    embeddings = encode_texts(sentences)

    # 计算相邻句子的相似度
    similarities = []

    for i in range(len(sentences) - 1):

        a = embeddings[i]
        b = embeddings[i + 1]

        similarity = np.dot(a, b) / (
            np.linalg.norm(a) * np.linalg.norm(b) + 1e-9
        )

        similarities.append(float(similarity))

    # 以相似度最低的20%作为候选语义边界
    threshold = (
        float(np.percentile(similarities, 20))
        if similarities else 0
    )

    chunks = []
    start = 0
    n = len(sentences)

    while start < n:

        end = start
        length = 0
        best_end = None
        best_score = float("inf")

        # 寻找合适的切分位置
        while end < n:

            new_length = length + len(sentences[end]) + 1

            if new_length > max_chars and end > start:
                break

            length = new_length
            end += 1

            # 当前段落之后的语义边界
            if min_chars <= length <= max_chars and end < n:

                score = similarities[end - 1]

                if score < best_score:
                    best_score = score
                    best_end = end

                if length >= target_chars and score <= threshold:
                    break

        # 若已达到最大长度，选择已有的最佳语义边界
        if end < n and best_end is not None:
            end = best_end

        text = "\n".join(sentences[start:end])

        chunks.append(Document(
            page_content=text,
            metadata=doc.metadata.copy()
        ))

        if end >= n:
            break

        # 3. 保留完整文本单元作为Overlap
        next_start = end
        overlap_length = 0

        for j in range(end - 1, start, -1):

            size = len(sentences[j]) + 1

            if overlap_length + size > overlap_chars:
                break

            next_start = j
            overlap_length += size

        start = next_start

    return chunks
