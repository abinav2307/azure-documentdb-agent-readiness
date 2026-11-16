import json
import math
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pymongo.errors import OperationFailure

import catalog
from app import create_app
from seed import load_products, seed_products, wait_for_index


class MemoryCollection:
    """Only for unit tests; not a substitute for live DocumentDB validation."""
    def __init__(self):
        self.docs = {}
        self.writes = 0

    def find_one(self, query):
        return deepcopy(self.docs.get(query["_id"]))

    def replace_one(self, query, document, upsert):
        assert upsert
        self.docs[query["_id"]] = deepcopy(document)
        self.writes += 1


class SampleTests(unittest.TestCase):
    def test_catalog_shape(self):
        products = load_products()
        self.assertEqual(len(products), 20)
        for p in products:
            self.assertIsInstance(p["_id"], str)
            self.assertTrue(p["title"] and p["description"])
            self.assertGreater(p["price"], 0)
            self.assertEqual(p["currency"], "USD")

    def test_embedding_model_and_normalization(self):
        ai = Mock()
        ai.embeddings.create.return_value = SimpleNamespace(data=[SimpleNamespace(embedding=[2.0] * 1536)])
        vector = catalog.embed(ai, "walking boots")
        ai.embeddings.create.assert_called_once_with(model="text-embedding-ada-002", input=["walking boots"])
        self.assertEqual(len(vector), 1536)
        self.assertAlmostEqual(sum(v * v for v in vector), 1.0)
        self.assertTrue(all(isinstance(v, float) for v in vector))

    def test_reject_invalid_vectors(self):
        for vector in ([], [0.0] * 1536, [math.nan] * 1536,
                       [math.inf] * 1536, [True] * 1536, ["x"] * 1536):
            with self.subTest(vector_type=type(vector[0]) if vector else None):
                with self.assertRaises(ValueError):
                    catalog.normalize(vector)

    def test_pipeline_uses_native_top_ten_and_safe_projection(self):
        pipeline = catalog.search_pipeline([1.0] * 1536)
        search = pipeline[0]["$search"]["cosmosSearch"]
        self.assertEqual(search["path"], "embedding")
        self.assertEqual(search["k"], 10)
        self.assertEqual(search["nProbes"], 1)
        projection = pipeline[1]["$project"]
        self.assertEqual(projection["score"], {"$meta": "searchScore"})
        self.assertNotIn("embedding", projection)
        self.assertNotIn("document", projection)

    def test_http_success_and_service_reuse(self):
        collection = Mock()
        collection.aggregate.return_value = [{"_id": f"sku-{i}", "title": "Tent", "score": 0.9} for i in range(10)]
        embed = Mock(return_value=[1.0] * 1536)
        provider = Mock(return_value=(collection, embed))
        client = create_app(provider).test_client()
        for _ in range(2):
            response = client.post("/search", json={"query": "  shelter for camping  "})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json["results"]), 10)
            self.assertNotIn("embedding", response.json["results"][0])
        embed.assert_called_with("shelter for camping")
        self.assertEqual(collection.aggregate.call_count, 2)

    def test_invalid_http_inputs_do_not_call_services(self):
        provider = Mock()
        client = create_app(provider).test_client()
        for payload in ({}, [], None, {"query": " "}, {"query": 123},
                        {"query": "a" * 2001}, {"query": {"$ne": None}}):
            response = client.post("/search", data=json.dumps(payload), content_type="application/json")
            self.assertEqual(response.status_code, 400)
        self.assertEqual(client.post("/search", data="hi").status_code, 415)
        self.assertEqual(client.post("/search", data="{", content_type="application/json").status_code, 400)
        self.assertEqual(client.post("/search", data="x" * 17000, content_type="application/json").status_code, 413)
        self.assertEqual(client.get("/search").status_code, 405)
        provider.assert_not_called()

    def test_upstream_error_does_not_leak_details(self):
        collection = Mock()
        collection.aggregate.side_effect = OperationFailure("sensitive upstream details")
        client = create_app(lambda: (collection, lambda _: [1.0] * 1536)).test_client()
        response = client.post("/search", json={"query": "boots"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive", response.get_data(as_text=True))

    def test_configuration_error(self):
        provider = Mock(side_effect=ValueError("secret must not be exposed"))
        response = create_app(provider).test_client().post("/search", json={"query": "boots"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("secret", response.get_data(as_text=True))

    def test_index_creation_and_idempotency(self):
        collection = Mock(name="collection")
        collection.name = "products"
        collection.list_indexes.return_value = [{"name": "_id_", "key": {"_id": 1}}]
        catalog.ensure_index(collection)
        command = collection.database.command.call_args.args[0]
        self.assertEqual(command["createIndexes"], "products")
        index = command["indexes"][0]
        self.assertEqual(index["key"], {"embedding": "cosmosSearch"})
        self.assertEqual(index["cosmosSearchOptions"], {"kind": "vector-ivf", "dimensions": 1536, "similarity": "COS", "numLists": 1})
        collection.database.command.reset_mock()
        collection.list_indexes.return_value = [{**index, "cosmosSearch": index["cosmosSearchOptions"]}]
        catalog.ensure_index(collection)
        collection.database.command.assert_not_called()

    def test_conflicting_index_is_not_dropped(self):
        collection = Mock()
        collection.list_indexes.return_value = [{"name": "other", "key": {"embedding": "cosmosSearch"}, "cosmosSearch": {"kind": "vector-hnsw"}}]
        with self.assertRaises(ValueError):
            catalog.ensure_index(collection)
        collection.drop_index.assert_not_called()
        collection.database.command.assert_not_called()

    def test_seed_idempotency_and_changed_description(self):
        collection = MemoryCollection()
        products = load_products()[:2]
        embed = Mock(return_value=[2.0] * 1536)
        self.assertEqual(seed_products(collection, embed, products)[:2], (2, 0))
        self.assertEqual(seed_products(collection, embed, products)[:2], (0, 2))
        self.assertEqual(embed.call_count, 2)
        products[0]["description"] = "Revised hiking description"
        seed_products(collection, embed, products)
        self.assertEqual(embed.call_count, 3)
        products[1]["price"] += 1
        seed_products(collection, embed, products)
        self.assertEqual(embed.call_count, 3)
        self.assertEqual(collection.docs[products[1]["_id"]]["price"], products[1]["price"])

    def test_readiness_requires_ten_scored_hits(self):
        collection = Mock()
        collection.aggregate.side_effect = [[], [{"score": 0.9}] * 10]
        wait_for_index(collection, [1.0] * 1536, attempts=2, delay=0)
        self.assertEqual(collection.aggregate.call_count, 2)
        collection.aggregate.side_effect = None
        collection.aggregate.return_value = [{"score": 0.9}] * 9
        with self.assertRaises(ValueError):
            wait_for_index(collection, [1.0] * 1536, attempts=2, delay=0)

    def test_client_singleton_secure_options(self):
        with patch.dict("os.environ", {"DOCUMENTDB_URI": "mongodb+srv://example.invalid/", "OPENAI_API_KEY": "unit-test-placeholder"}), \
             patch.object(catalog, "load_dotenv"), \
             patch.object(catalog, "MongoClient") as mongo, \
             patch.object(catalog, "OpenAI") as ai, \
             patch.object(catalog, "_client", None), patch.object(catalog, "_ai", None):
            first = catalog.get_clients()
            self.assertEqual(first, catalog.get_clients())
            mongo.assert_called_once()
            ai.assert_called_once()
            options = mongo.call_args.kwargs
            self.assertTrue(options["tls"])
            self.assertFalse(options["tlsAllowInvalidCertificates"])
            self.assertFalse(options["tlsAllowInvalidHostnames"])
            self.assertFalse(options["retryWrites"])
            self.assertEqual(options["authMechanism"], "SCRAM-SHA-256")
            catalog.close_clients()


if __name__ == "__main__":
    unittest.main()
