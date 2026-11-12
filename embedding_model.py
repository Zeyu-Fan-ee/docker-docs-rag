from functools import lru_cache
from project_config import EMBEDDING_MODEL, MODEL_DEVICE, EMBEDDING_MAX_LENGTH
@lru_cache(maxsize=1)
def get_embedding_model():
    from FlagEmbedding import BGEM3FlagModel
    return BGEM3FlagModel(EMBEDDING_MODEL, use_fp16=False, devices=MODEL_DEVICE)
def encode_texts(texts):
    if not texts:
        raise ValueError('Cannot embed an empty list')
    return get_embedding_model().encode(texts, batch_size=4, max_length=EMBEDDING_MAX_LENGTH,
                                       return_dense=True, return_sparse=False,
                                       return_colbert_vecs=False)['dense_vecs']
