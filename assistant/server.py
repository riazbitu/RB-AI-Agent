#!/usr/bin/env python3
import argparse
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from pathlib import Path
import json
import threading

from assistant.indexer import TfIdfIndex
try:
    from assistant.embeddings import embed_texts, cosine_similarity_matrix, EmbeddingsUnavailable
    import numpy as _np
    _EMBEDDING_AVAILABLE = True
except Exception:
    _EMBEDDING_AVAILABLE = False

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'index.json'
DOCS_DIR = ROOT.parent / 'docs'

index = TfIdfIndex()

def ensure_index():
    if DATA_FILE.exists():
        print('Loading existing index...')
        index.load(DATA_FILE)
    else:
        print('Building index from docs...')
        index.load_docs(DOCS_DIR)
        index.build()
        index.save(DATA_FILE)
        print('Index saved to', DATA_FILE)
    # attempt to compute document embeddings if supported
    if _EMBEDDING_AVAILABLE:
        try:
            docs_texts = [d['text'] for d in index.docs]
            print('Computing document embeddings (may require sentence-transformers)...')
            emb = embed_texts(docs_texts)
            # store in-memory
            index._doc_embeddings = emb
            print('Document embeddings computed')
        except Exception as e:
            print('Embeddings not available:', e)
            index._doc_embeddings = None
    else:
        index._doc_embeddings = None

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/search'):
            q = ''
            if '?' in self.path:
                qs = self.path.split('?',1)[1]
                for kv in qs.split('&'):
                    if '=' in kv:
                        k,v = kv.split('=',1)
                        if k=='q': q = v
            results = index.keyword_search(q)
            payload = json.dumps({'query': q, 'results': results}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path.startswith('/semantic'):
            q = ''
            if '?' in self.path:
                qs = self.path.split('?',1)[1]
                for kv in qs.split('&'):
                    if '=' in kv:
                        k,v = kv.split('=',1)
                        if k=='q': q = v
            results = index.semantic_search(q)
            payload = json.dumps({'query': q, 'results': results}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        elif self.path.startswith('/embed-search'):
            if not getattr(index, '_doc_embeddings', None):
                payload = json.dumps({'error': 'Embeddings not available on this system.'}).encode('utf-8')
                self.send_response(503)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                return
            q = ''
            if '?' in self.path:
                qs = self.path.split('?',1)[1]
                for kv in qs.split('&'):
                    if '=' in kv:
                        k,v = kv.split('=',1)
                        if k=='q': q = v
            try:
                qemb = embed_texts([q])[0]
                sims = cosine_similarity_matrix(qemb, index._doc_embeddings)
                # build results
                order = _np.argsort(sims)[::-1][:20]
                out = []
                for s in order:
                    out.append({'path': index.docs[int(s)]['path'], 'score': float(sims[s]), 'snippet': index.get_snippet(index.docs[int(s)]['text'], q)})
                payload = json.dumps({'query': q, 'results': out}, ensure_ascii=False).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                payload = json.dumps({'error': str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
        else:
            return super().do_GET()


def run_server(port=9001):
    ensure_index()
    print(f'RB Assistant listening on http://127.0.0.1:{port}')
    with TCPServer(('127.0.0.1', port), Handler) as httpd:
        httpd.serve_forever()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=9001)
    args = parser.parse_args()
    run_server(args.port)
