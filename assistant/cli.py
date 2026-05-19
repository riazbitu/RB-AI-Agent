#!/usr/bin/env python3
from assistant.indexer import TfIdfIndex
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'index.json'

def main():
    idx = TfIdfIndex()
    if DATA_FILE.exists():
        idx.load(DATA_FILE)
    else:
        idx.load_docs(ROOT.parent / 'docs')
        idx.build()
        idx.save(DATA_FILE)
    print('RB Assistant CLI. Type exit to quit.')
    while True:
        q = input('search> ').strip()
        if q in ('exit','quit'):
            break
        res = idx.semantic_search(q)
        for r in res[:10]:
            print(f"{r['path']} (score={r['score']:.4f})")
            print(f"  {r['snippet'][:300]}\n")

if __name__ == '__main__':
    main()
