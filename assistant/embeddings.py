#!/usr/bin/env python3
"""
Optional embedding support using sentence-transformers (if installed).
Falls back to a NotAvailable exception so the server can continue using TF-IDF.
"""
from pathlib import Path

class EmbeddingsUnavailable(Exception):
    pass

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    _MODEL = None

    def load_model(name='all-MiniLM-L6-v2'):
        global _MODEL
        if _MODEL is None:
            _MODEL = SentenceTransformer(name)
        return _MODEL

    def embed_texts(texts, model_name='all-MiniLM-L6-v2'):
        m = load_model(model_name)
        embs = m.encode(texts, show_progress_bar=False)
        return np.array(embs)

    def cosine_similarity_matrix(qvec, mat):
        # qvec: (d,), mat: (n,d)
        import numpy as np
        denom = (np.linalg.norm(mat, axis=1) * (np.linalg.norm(qvec) + 1e-12))
        dots = mat.dot(qvec)
        return dots / (denom + 1e-12)

except Exception:
    # sentence-transformers not available
    def load_model(*args, **kwargs):
        raise EmbeddingsUnavailable('sentence-transformers not installed')
    def embed_texts(*args, **kwargs):
        raise EmbeddingsUnavailable('sentence-transformers not installed')
    def cosine_similarity_matrix(*args, **kwargs):
        raise EmbeddingsUnavailable('sentence-transformers not installed')
