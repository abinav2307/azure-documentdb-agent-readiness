"""API-only semantic product search. Run: flask --app app run"""
from flask import Flask, jsonify, request
from openai import OpenAIError
from pymongo.errors import PyMongoError
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge

from catalog import get_services, vector_search


def create_app(service_provider=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    provider = service_provider or get_services

    @app.errorhandler(RequestEntityTooLarge)
    def too_large(_error):
        return jsonify(error="Request body exceeds 16 KiB."), 413

    @app.post("/search")
    def search():
        if not request.is_json:
            return jsonify(error="Send application/json."), 415
        try:
            body = request.get_json()
        except BadRequest:
            return jsonify(error="Malformed JSON."), 400
        query = body.get("query") if isinstance(body, dict) else None
        if not isinstance(query, str) or not query.strip() or len(query) > 2000:
            return jsonify(error="query must be a nonempty string of at most 2000 characters."), 400
        try:
            collection, embed_query = provider()
            results = vector_search(collection, embed_query(query.strip()))
        except (OpenAIError, PyMongoError):
            # Never return or log exception strings: they can include credentials/data.
            return jsonify(error="Search dependency unavailable. Check credentials, networking and index readiness."), 503
        except ValueError:
            return jsonify(error="Search configuration or embedding is invalid."), 503
        return jsonify(results=results)

    return app


app = create_app()
