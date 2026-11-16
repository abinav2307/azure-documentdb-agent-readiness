"""User-authorized writes only: python seed.py. Never clears unrelated documents."""
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

from openai import OpenAIError
from pymongo.errors import PyMongoError

from catalog import (DIMENSIONS, EMBEDDING_VERSION, MODEL, close_clients,
                     ensure_index, get_services, normalize, product_text, vector_search)


def load_products():
    products = json.loads(Path(__file__).with_name("data").joinpath("products.json").read_text(encoding="utf-8"))
    ids = [p["_id"] for p in products]
    if len(products) < 10 or len(set(ids)) != len(ids):
        raise ValueError("Catalog must contain at least 10 unique products.")
    return products


def seed_products(collection, embed_text, products):
    updated = skipped = 0
    probe = None
    for product in products:
        text = product_text(product)
        fingerprint = hashlib.sha256(text.encode("utf-8")).hexdigest()
        existing = collection.find_one({"_id": product["_id"]})
        reusable = bool(existing and existing.get("embeddingHash") == fingerprint
                        and existing.get("embeddingModel") == MODEL
                        and existing.get("embeddingDims") == DIMENSIONS
                        and existing.get("embeddingVersion") == EMBEDDING_VERSION)
        if reusable:
            try:
                normalize(existing["embedding"])  # Validate; preserve cached float values.
                vector = existing["embedding"]
            except (KeyError, TypeError, ValueError):
                reusable = False
        if not reusable:
            vector = normalize(embed_text(text))
        document = {**product, "schemaVersion": 1, "embedding": vector,
                    "embeddingModel": MODEL, "embeddingDims": DIMENSIONS,
                    "embeddingVersion": EMBEDDING_VERSION, "embeddingHash": fingerprint}
        # Update metadata even when title/description (and embedding) are unchanged.
        if existing != document:
            collection.replace_one({"_id": product["_id"]}, document, upsert=True)
            updated += 1
        else:
            skipped += 1
        probe = vector
    return updated, skipped, probe


def wait_for_index(collection, vector, attempts=60, delay=3):
    """A scored top-10 query is the readiness check; no assumed training semantics."""
    for attempt in range(attempts):
        hits = vector_search(collection, vector)
        if len(hits) == 10 and all(isinstance(h.get("score"), (int, float))
                                   and math.isfinite(h["score"]) for h in hits):
            return
        if attempt + 1 < attempts:
            time.sleep(delay)
    raise ValueError("Index did not return 10 scored products in time. Wait and rerun seed.py or check the index.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        products = load_products()
        collection, embed_text = get_services()
        updated, skipped, probe = seed_products(collection, embed_text, products)
        ensure_index(collection)
        wait_for_index(collection, probe)
        print(f"Ready: {updated} products updated, {skipped} unchanged; top-10 scored vector query passed.")
        return 0
    except (OpenAIError, PyMongoError):
        print("Seed failed: check provider access, database permissions, network and index configuration. Rerunning is safe.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    finally:
        close_clients()


if __name__ == "__main__":
    sys.exit(main())
