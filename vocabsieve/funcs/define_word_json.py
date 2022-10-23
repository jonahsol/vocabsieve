import json
from typing import TypedDict, Optional

class DefineWordJson(TypedDict):
    word: str
    sentence: str

def parse_define_word_json(s: str) -> Optional[DefineWordJson]:
    if not s.startswith("{"):
        return None

    obj = None
    try:
        obj = json.loads(s)
    except ValueError:
        return None

    return obj if "word" in obj and "sentence" in obj else None

def is_oneword(s) -> bool:
    return len(s.split()) == 1