# coding=utf-8
import tempfile
import unittest
from pathlib import Path

from bwapi.credentials import CredentialsStore

ACCESS_TOKEN = "00000000-0000-0000-0000-000000000000"


class TestCredentialsStore(unittest.TestCase):
    def with_credential_store(function):
        def wrapper(self):
            with tempfile.TemporaryDirectory() as temp_dir:
                token_path = Path(temp_dir) / "tokens.txt"
                store = CredentialsStore(credentials_path=token_path)
                function(self, store)

        return wrapper

    @with_credential_store
    def test_file_created_on_read(self, store):
        self.assertFalse(store._credentials_path.exists())

        _ = [c for c in store]

        self.assertTrue(store._credentials_path.exists())

    @with_credential_store
    def test_file_created_on_write(self, store):
        self.assertFalse(store._credentials_path.exists())

        store["example@example.com"] = ACCESS_TOKEN

        self.assertTrue(store._credentials_path.exists())

    @with_credential_store
    def test_store(self, store):
        self.assertEqual(len(store), 0)

        store["example@example.com"] = ACCESS_TOKEN

        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)
        self.assertEqual(len(store), 1)

    @with_credential_store
    def test_store_multiple(self, store):
        self.assertEqual(len(store), 0)

        store["example@example.com"] = "10000000-0000-0000-0000-000000000000"
        store["another-example@example.com"] = "20000000-0000-0000-0000-000000000000"

        self.assertEqual(
            store["example@example.com"], "10000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(
            store["another-example@example.com"], "20000000-0000-0000-0000-000000000000"
        )
        self.assertEqual(len(store), 2)

    @with_credential_store
    def test_store_overwrite(self, store):
        self.assertEqual(len(store), 0)

        store["example@example.com"] = "10000000-0000-0000-0000-000000000000"
        store["example@example.com"] = "20000000-0000-0000-0000-000000000000"

        self.assertEqual(
            store["example@example.com"], "20000000-0000-0000-0000-000000000000"
        )

    @with_credential_store
    def test_store_same(self, store):
        self.assertEqual(len(store), 0)

        store["example@example.com"] = ACCESS_TOKEN
        store["example@example.com"] = ACCESS_TOKEN

        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)

    @with_credential_store
    def test_store_case_insensitive(self, store):
        store["example@example.com"] = ACCESS_TOKEN
        store["EXAMPLE@EXAMPLE.COM"] = ACCESS_TOKEN
        store["eXaMpLe@ExAmPlE.cOm"] = ACCESS_TOKEN
        self.assertEqual(len(store), 1)

    @with_credential_store
    def test_store_lower(self, store):
        store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)

    @with_credential_store
    def test_store_upper(self, store):
        store["EXAMPLE@EXAMPLE.COM"] = ACCESS_TOKEN
        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)

    @with_credential_store
    def test_store_mixed(self, store):
        store["eXaMpLe@ExAmPlE.cOm"] = ACCESS_TOKEN
        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)

    @with_credential_store
    def test_get_lower(self, store):
        store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(store["example@example.com"], ACCESS_TOKEN)

    @with_credential_store
    def test_get_upper(self, store):
        store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(store["EXAMPLE@EXAMPLE.COM"], ACCESS_TOKEN)

    @with_credential_store
    def test_get_mixed(self, store):
        store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(store["eXaMpLe@ExAmPlE.cOm"], ACCESS_TOKEN)
