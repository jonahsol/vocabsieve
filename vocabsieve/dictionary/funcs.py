import os
from db import *
from pystardict import Dictionary
from dictionary.dictionary import dictdb
from dictionary.dictformats import *
from xdxftransform import xdxf2html

def dictimport(path, dicttype, lang, name) -> None:
    "Import dictionary from file to database"
    if dicttype == "stardict":
        stardict = Dictionary(os.path.splitext(path)[0], in_memory=True)
        d = {}
        if stardict.ifo.sametypesequence == 'x':
            for key in stardict.idx.keys():
                d[key] = xdxf2html(stardict.dict[key])
        else:
            for key in stardict.idx.keys():
                d[key] = stardict.dict[key]
        dictdb.importdict(d, lang, name)
    elif dicttype == "json":
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
            dictdb.importdict(d, lang, name)
    elif dicttype == "migaku":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            d = {}
            for item in data:
                d[item['term']] = item['definition']
            dictdb.importdict(d, lang, name)
    elif dicttype == "freq":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            d = {}
            for i, word in enumerate(data):
                d[word] = str(i + 1)
            dictdb.importdict(d, lang, name)
    elif dicttype == "audiolib":
        # Audios will be stored as a serialized json list
        filelist = []
        d = {}
        for root, dirs, files in os.walk(path):
            for item in files:
                filelist.append(
                    os.path.relpath(
                        os.path.join(
                            root, item), path))
        for item in filelist:
            headword = os.path.basename(os.path.splitext(item)[0]).lower()
            if not d.get(headword):
                d[headword] = [item]
            else:
                d[headword].append(item)
        for word in d.keys():
            d[word] = json.dumps(d[word])
        dictdb.importdict(d, lang, name)
    elif dicttype == 'mdx':
        d = parseMDX(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "dsl":
        d = parseDSL(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "csv":
        d = parseCSV(path)
        dictdb.importdict(d, lang, name)
    elif dicttype == "tsv":
        d = parseTSV(path)
        dictdb.importdict(d, lang, name)

def dictdelete(name) -> None:
    dictdb.deletedict(name)

# There is a str.removeprefix function, but it is implemented
# only in python 3.9. Copying the implementation here
def removeprefix(self: str, prefix: str, /) -> str:
    if self.startswith(prefix):
        return self[len(prefix):]
    else:
        return self[:]

