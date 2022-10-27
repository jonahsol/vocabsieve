from flask import Flask, request
from flask.wrappers import Response
import logging
from http import HTTPStatus
from flask import jsonify
from dictionary.dictionary import *
from db import Record
from dictionary.dictionary import *
from settings import * 
from ext.api_server.failed_request import FailedRequest
from anki_connect import *
from db import *

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def str2bool(v):
    return str(v).lower() in ("yes", "true", "t", "1")

class APIServer():
    def __init__(self, host: str, port: int):
        self.start_api(host, port)

    def start_api(self, host, port):
        """ Main server application """
        self.app = Flask(__name__)

        @self.app.errorhandler(FailedRequest)
        def handle_failed_request(error):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response

        @self.app.route("/healthcheck")
        def healthcheck():
            return "Hello, World!"

        @self.app.route("/version")
        def version():
            return str(1)

        @self.app.route("/define/<string:word>")
        def lookup(word):
            use_lemmatize = str2bool(request.args.get("lemmatize", "True"))
            if use_lemmatize:
                word = apply_lemmatization(
                    word, 
                    settings.get("target_language"), 
                    settings.get("lem_greedily"))

            lookup_res = lookupin(
                word,
                settings.get("target_language"),
                settings.get("dict_source"),
                settings.get("gtrans_lang"),
                settings.get("gtrans_api"))

            rec.recordLookup(
                word,
                lookup_res,
                settings.get("target_language"),
                use_lemmatize,
                settings.get("dict_source"),
                lookup_res != None)

            return lookup_res if lookup_res else Response(status = HTTPStatus.NO_CONTENT)

        @self.app.route("/translate", methods=["POST"])
        def translate():
            lang = request.args.get("src", settings.get("target_language"))
            gtrans_lang = request.args.get("dst", settings.value("gtrans_lang"))

            if not request.json or "text" not in request.json:
                raise FailedRequest(
                    message="Request body should be JSON of form { text: str }"
                )

            translation = googletranslate(
                request.json.get("text"),
                lang,
                gtrans_lang,
                settings.get("gtrans_api"))
            return Response(status = HTTPStatus.INTERNAL_SERVER_ERROR) \
                   if not translation \
                   else {
                       "translation": translation,
                       "src": lang,
                       "dst": gtrans_lang }

        @self.app.route("/createNote", methods=["POST"])
        def createNote():
            if not request.json:
                raise FailedRequest(
                    message="Request body should be JSON of { ...ankiFields }")

            content = default_note_request()

            content["tags"] += getattr(request.json, "tags", "")
            request.json.pop("tags", None)

            content["fields"] = request.json

            def recordNoteAddition(success: bool):
                rec.recordNote(
                    json.dumps(content), 
                    sentence=getattr(content["fields"], "sentence", None),
                    word=getattr(content["fields"], "word", None),
                    definition=getattr(content["fields"], "definition", None),
                    definition2=getattr(content["fields"], "definition2", None),
                    pronunciation=None,
                    image=None,
                    tags=content["tags"],
                    success=success
                )

            try:
                addNote(settings.get("anki_api"), content)
                recordNoteAddition(True)
                return Response(status = HTTPStatus.OK)
            except Exception as e:
                recordNoteAddition(False)
                raise FailedRequest(
                    message=str(e), status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        @self.app.route("/stats")
        def stats():
            rec = Record()
            return f"Today: {rec.countLookupsToday()} lookups, {rec.countNotesToday()} notes"

        @self.app.route("/lemmatize/<string:word>")
        def lemmatize(word):
            return lem_word(word, settings.get("target_language"))

        @self.app.route("/logs")
        def logs():
            rec = Record()
            return "\n".join([" ".join([str(i) for i in item])
                             for item in rec.getAllLookups()][::-1])

        try:
            self.app.run(
                debug=False,
                use_reloader=False,
                host=host,
                port=port)
        except OSError:
            return
