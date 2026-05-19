#!/usr/bin/env python3
"""
Simple TF-IDF indexer and semantic search implemented in pure Python (no external deps).
"""
import math
import json
import re
from pathlib import Path
from collections import defaultdict

TOKEN_RE = re.compile(r"\w+", re.UNICODE)

class TfIdfIndex:
    def __init__(self):
        self.docs = []  # list of {'path':..., 'text':...}
        self.vocab = {}  # term -> id
        self.idf = []
        self.tf_vectors = []  # list of dict termid->tf
        self.norms = []
        self.df = defaultdict(int)

    def load_docs(self, docs_dir: Path):
        docs = []
        for md in docs_dir.rglob('*.md'):
            try:
                text = md.read_text(encoding='utf-8')
            except Exception:
                continue
            docs.append({'path': str(md.relative_to(docs_dir.parent)), 'text': text})
        self.docs = docs
        return len(docs)

    def tokenize(self, text: str):
        return [t.lower() for t in TOKEN_RE.findall(text)]

    def build(self):
        # build vocabulary and term frequencies
        doc_terms = []
        for d in self.docs:
            tokens = self.tokenize(d['text'])
            doc_terms.append(tokens)
        # compute df
        for tokens in doc_terms:
            seen = set()
            for t in tokens:
                if t not in seen:
                    self.df[t] += 1
                    seen.add(t)
        # assign vocab ids
        self.vocab = {t: i for i, t in enumerate(sorted(self.df.keys()))}
        N = len(self.docs)
        # compute idf
        self.idf = [0.0] * len(self.vocab)
        for t, i in self.vocab.items():
            df = self.df[t]
            self.idf[i] = math.log((N + 1) / (df + 1)) + 1.0
        # compute tf vectors
        self.tf_vectors = []
        self.norms = []
        for tokens in doc_terms:
            tf = defaultdict(float)
            for t in tokens:
                if t in self.vocab:
                    tf[self.vocab[t]] += 1.0
            # normalize by length
            length = len(tokens) if tokens else 1
            for k in list(tf.keys()):
                tf[k] = tf[k] / length * self.idf[k]
            norm = math.sqrt(sum(v * v for v in tf.values()))
            self.tf_vectors.append(dict(tf))
            self.norms.append(norm)

    def save(self, path: Path):
        obj = {
            'docs': self.docs,
            'vocab': list(self.vocab.keys()),
            'idf': self.idf,
            'tf_vectors': self.tf_vectors,
            'norms': self.norms,
        }
        # include embeddings if present
        if getattr(self, '_doc_embeddings', None) is not None:
            try:
                import numpy as _np
                obj['embeddings'] = _np.asarray(self._doc_embeddings).tolist()
            except Exception:
                obj['embeddings'] = None
        path.write_text(json.dumps(obj), encoding='utf-8')

    def load(self, path: Path):
        obj = json.loads(path.read_text(encoding='utf-8'))
        self.docs = obj['docs']
        vocab_terms = obj['vocab']
        self.vocab = {t: i for i, t in enumerate(vocab_terms)}
        self.idf = obj['idf']
        self.tf_vectors = [{int(k): v for k, v in tv.items()} for tv in obj['tf_vectors']]
        self.norms = obj['norms']
        # load embeddings if available
        if 'embeddings' in obj and obj['embeddings']:
            try:
                import numpy as _np
                self._doc_embeddings = _np.array(obj['embeddings'])
            except Exception:
                self._doc_embeddings = None
        else:
            self._doc_embeddings = None

    def vectorize_query(self, q: str):
        tokens = self.tokenize(q)
        tf = defaultdict(float)
        for t in tokens:
            if t in self.vocab:
                tf[self.vocab[t]] += 1.0
        length = len(tokens) if tokens else 1
        for k in list(tf.keys()):
            tf[k] = tf[k] / length * self.idf[k]
        norm = math.sqrt(sum(v * v for v in tf.values()))
        return dict(tf), norm

    def semantic_search(self, q: str, topk=10):
        qvec, qnorm = self.vectorize_query(q)
        if qnorm == 0:
            return []
        scores = []
        for i, docvec in enumerate(self.tf_vectors):
            # dot product
            dot = 0.0
            for k, v in qvec.items():
                dot += v * docvec.get(k, 0.0)
            denom = qnorm * (self.norms[i] if self.norms[i] > 0 else 1.0)
            score = dot / denom if denom != 0 else 0.0
            if score > 0:
                snippet = self.get_snippet(self.docs[i]['text'], q)
                scores.append({'path': self.docs[i]['path'], 'score': score, 'snippet': snippet})
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:topk]

    def keyword_search(self, q: str, topk=10):
        ql = q.lower()
        results = []
        for i, d in enumerate(self.docs):
            score = d['text'].lower().count(ql)
            if score > 0:
                snippet = self.get_snippet(d['text'], ql)
                results.append({'path': d['path'], 'score': score, 'snippet': snippet})
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:topk]

    def get_snippet(self, text: str, q: str, radius=120):
        idx = text.lower().find(q.lower())
        if idx == -1:
            return text[:radius].strip().replace('\n', ' ')
        start = max(0, idx - radius)
        end = min(len(text), idx + len(q) + radius)
        return text[start:end].strip().replace('\n', ' ')
