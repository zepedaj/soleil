"""
Taken/modified from https://github.com/pytorch/examples/blob/main/word_language_model/data.py
"""

import os
from io import open
from pathlib import Path
import torch

from urllib.request import urlretrieve


class _Paths:
    _urls = {
        f"{name}.txt": f"https://github.com/pytorch/examples/raw/main/word_language_model/data/wikitext-2/{name}.txt"
        for name in ["train", "test", "valid"]
    }

    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(exist_ok=True)

    def get(self, name):
        assert name in self._urls, f"Invalid file name {name}"
        if not (target := self.root / name).exists():
            urlretrieve(self._urls[target], target)
        return target


class Dictionary(object):
    def __init__(self):
        self.word2idx = {}
        self.idx2word = []

    def add_word(self, word):
        if word not in self.word2idx:
            self.idx2word.append(word)
            self.word2idx[word] = len(self.idx2word) - 1
        return self.word2idx[word]

    def __len__(self):
        return len(self.idx2word)


class Corpus(object):
    def __init__(self, path):
        self.paths = _Paths(path)
        self.dictionary = Dictionary()
        self.train = self.tokenize(self.paths.get("train.txt"))
        self.valid = self.tokenize(self.paths.get("valid.txt"))
        self.test = self.tokenize(self.paths.get("test.txt"))

    def tokenize(self, path):
        """Tokenizes a text file."""
        assert os.path.exists(path)
        # Add words to the dictionary
        with open(path, "r", encoding="utf8") as f:
            for line in f:
                words = line.split() + ["<eos>"]
                for word in words:
                    self.dictionary.add_word(word)

        # Tokenize file content
        with open(path, "r", encoding="utf8") as f:
            idss = []
            for line in f:
                words = line.split() + ["<eos>"]
                ids = []
                for word in words:
                    ids.append(self.dictionary.word2idx[word])
                idss.append(torch.tensor(ids).type(torch.int64))
            ids = torch.cat(idss)

        return ids
