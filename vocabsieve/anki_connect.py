import json
import urllib.request
from typing import List
from settings import *

def make_anki_connect_request(action, **params):
    return {'action': action, 'params': params, 'version': 6}

requestTimeout = 2
def invoke(action, server, **params):
    requestJson = json.dumps(make_anki_connect_request(action, **params)).encode('utf-8')
    response = json.load(
        urllib.request.urlopen(
            urllib.request.Request(
                server, requestJson), timeout=requestTimeout))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def getDeckList(server) -> list:
    result = invoke('deckNames', server)
    return list(result)


def getNoteTypes(server) -> list:
    result = invoke('modelNames', server)
    return list(result)


def getFields(server, name) -> list:
    result = invoke('modelFieldNames', server, modelName=name)
    return list(result)


def addNote(server, content) -> int:
    result = invoke('addNote', server, note=content)
    return int(result)


def addNotes(server, content) -> List[int]:
    result = invoke('addNotes', server, notes=content)
    return list(result)


def getVersion(server) -> str:
    result = invoke('version', server)
    return str(result)

def default_note_request():
    return {
        "deckName": settings.get("deck_name"),
        "modelName": settings.get("note_type"),
        "tags": settings.get("tags").strip(),
        "fields": {}
    }