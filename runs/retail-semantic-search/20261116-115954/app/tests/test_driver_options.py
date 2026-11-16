"""Actual driver option parsing, without DNS, authentication, or network operations."""
import secrets
import unittest

from pymongo import MongoClient


class DriverOptionsTests(unittest.TestCase):
    def test_real_pymongo_accepts_tls_and_scram_options(self):
        # In-memory throwaway credential; never saved or sent anywhere.
        client = MongoClient(
            host="localhost", port=27017, connect=False,
            username="offline-test", password=secrets.token_urlsafe(),
            tls=True, tlsAllowInvalidCertificates=False,
            tlsAllowInvalidHostnames=False, authMechanism="SCRAM-SHA-256",
            retryWrites=False, timeoutMS=30000,
        )
        try:
            self.assertFalse(client.options.retry_writes)
        finally:
            client.close()
