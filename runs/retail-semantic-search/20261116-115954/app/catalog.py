"""Shared connection, embedding, and native DocumentDB vector operations."""
import atexit
import math
import os
from pathlib import Path
from threading import Lock

from dotenv import load_dotenv
from openai import OpenAI
from pymongo import MongoClient

MODEL = "text-embedding-ada-002"
DIMENSIONS = 1536
EMBEDDING_VERSION = 1
INDEX_NAME = "embedding_ivf"
INDEX_OPTIONS = {
    "kind": "vector-ivf", "dimensions": DIMENSIONS,
    "similarity": "COS", "numLists": 1,
}
_client = None
_ai = None
_lock = Lock()


def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("<"):
        raise ValueError(f"Set {name} locally before running this sample.")
    return value


def get_clients():
    """One of each client per process; do not preload before forking workers."""
    global _client, _ai
    with _lock:
        if _client is None:
            load_dotenv(Path(__file__).with_name(".env"), override=False)
            uri = required_env("DOCUMENTDB_URI")
            key = required_env("OPENAI_API_KEY")
            if not uri.startswith("mongodb+srv://"):
                raise ValueError("DOCUMENTDB_URI must be the portal-issued mongodb+srv URI.")
            _client = MongoClient(
                uri, tls=True,
                tlsAllowInvalidCertificates=False, tlsAllowInvalidHostnames=False,
                authMechanism="SCRAM-SHA-256", retryWrites=False,
                # Small synchronous demo: bound an entire database operation.
                timeoutMS=30000,
            )
            _ai = OpenAI(api_key=key, timeout=30.0, max_retries=0)
            atexit.register(close_clients)
    return _client, _ai


def close_clients():
    global _client, _ai
    with _lock:
        if _client is not None:
            _client.close()
            _client = None
        if _ai is not None:
            _ai.close()
            _ai = None


def get_services():
    mongo, ai = get_clients()
    database = os.environ.get("DOCUMENTDB_DATABASE", "retail")
    collection = mongo[database]["products"]
    return collection, lambda text: embed(ai, text)


def normalize(vector):
    if len(vector) != DIMENSIONS:
        raise ValueError("Embedding must have 1536 dimensions.")
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) for v in vector):
        raise ValueError("Embedding must contain finite numbers.")
    norm = math.sqrt(sum(v * v for v in vector))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Embedding must have a nonzero finite norm.")
    return [float(v / norm) for v in vector]


def embed(ai, text):
    response = ai.embeddings.create(model=MODEL, input=[text])
    return normalize(response.data[0].embedding)


def product_text(product):
    return f"{product['title']}\n{product['description']}"


def search_pipeline(vector):
    return [
        {"$search": {"cosmosSearch": {
            "vector": vector, "path": "embedding", "k": 10, "nProbes": 1,
        }, "returnStoredSource": True}},
        {"$project": {
            "_id": 1, "title": 1, "description": 1,
            "price": 1, "currency": 1, "category": 1,
            "score": {"$meta": "searchScore"},
        }},
    ]


def vector_search(collection, vector):
    return list(collection.aggregate(search_pipeline(vector)))


def ensure_index(collection):
    """Never drop an existing index implicitly. Fail on a conflicting definition."""
    for index in collection.list_indexes():
        if index.get("name") == INDEX_NAME or index.get("key", {}).get("embedding") == "cosmosSearch":
            options = index.get("cosmosSearchOptions", index.get("cosmosSearch", {}))
            if (index.get("name") != INDEX_NAME
                    or dict(index.get("key", {})) != {"embedding": "cosmosSearch"}
                    or any(options.get(k) != v for k, v in INDEX_OPTIONS.items())):
                raise ValueError("Conflicting embedding index: use a fresh sample database or review it manually.")
            return
    collection.database.command({
        "createIndexes": collection.name,
        "indexes": [{"name": INDEX_NAME, "key": {"embedding": "cosmosSearch"},
                     "cosmosSearchOptions": dict(INDEX_OPTIONS)}],
    })
