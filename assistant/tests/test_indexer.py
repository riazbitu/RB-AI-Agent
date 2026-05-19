import unittest
from assistant.indexer import TfIdfIndex
from pathlib import Path

class TestIndexer(unittest.TestCase):
    def test_tokenize_and_build(self):
        idx = TfIdfIndex()
        # create temp docs
        d1 = {'path':'d1.md','text':'Hello world. This is a test.'}
        d2 = {'path':'d2.md','text':'Another test document. Hello again.'}
        idx.docs = [d1,d2]
        idx.build()
        self.assertTrue(len(idx.vocab)>0)
        res = idx.keyword_search('hello')
        self.assertTrue(len(res)>0)

if __name__ == '__main__':
    unittest.main()
