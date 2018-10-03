# coding=utf-8
import tempfile
import unittest
from pathlib import Path

from credentials import CredentialsStore

ACCESS_TOKEN = "00000000-0000-0000-0000-000000000000"


class TestCredentialsStore(unittest.TestCase):

    def setUp(self):
        self.credentials_dir = Path(tempfile.NamedTemporaryFile().name)
        self.credentials_file = self.credentials_dir / 'tokens.txt'
        self.credentials_store = CredentialsStore(credentials_path=self.credentials_file)

    def tearDown(self):
        if self.credentials_file.exists():
            self.credentials_file.unlink()
        if self.credentials_dir.exists():
            self.credentials_dir.rmdir()

    def test_file_created_on_read(self):
        self.assertFalse(self.credentials_file.exists())

        _ = [c for c in self.credentials_store]

        self.assertTrue(self.credentials_file.exists())

    def test_file_created_on_write(self):
        self.assertFalse(self.credentials_file.exists())

        self.credentials_store["example@example.com"] = ACCESS_TOKEN

        self.assertTrue(self.credentials_file.exists())

    def test_store(self):
        self.assertEqual(len(self.credentials_store), 0)

        self.credentials_store["example@example.com"] = ACCESS_TOKEN

        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)
        self.assertEqual(len(self.credentials_store), 1)

    def test_store_multiple(self):
        self.assertEqual(len(self.credentials_store), 0)

        self.credentials_store["example@example.com"] = "10000000-0000-0000-0000-000000000000"
        self.credentials_store["another-example@example.com"] = "20000000-0000-0000-0000-000000000000"

        self.assertEqual(self.credentials_store["example@example.com"], "10000000-0000-0000-0000-000000000000")
        self.assertEqual(self.credentials_store["another-example@example.com"], "20000000-0000-0000-0000-000000000000")
        self.assertEqual(len(self.credentials_store), 2)

    def test_store_overwrite(self):
        self.assertEqual(len(self.credentials_store), 0)

        self.credentials_store["example@example.com"] = "10000000-0000-0000-0000-000000000000"
        self.credentials_store["example@example.com"] = "20000000-0000-0000-0000-000000000000"

        self.assertEqual(self.credentials_store["example@example.com"], "20000000-0000-0000-0000-000000000000")

    def test_store_same(self):
        self.assertEqual(len(self.credentials_store), 0)

        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.credentials_store["example@example.com"] = ACCESS_TOKEN

        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)

    def test_store_case_insensitive(self):
        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.credentials_store["EXAMPLE@EXAMPLE.COM"] = ACCESS_TOKEN
        self.credentials_store["eXaMpLe@ExAmPlE.cOm"] = ACCESS_TOKEN
        self.assertEqual(len(self.credentials_store), 1)

    def test_store_lower(self):
        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)

    def test_store_upper(self):
        self.credentials_store["EXAMPLE@EXAMPLE.COM"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)

    def test_store_mixed(self):
        self.credentials_store["eXaMpLe@ExAmPlE.cOm"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)

    def test_get_lower(self):
        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["example@example.com"], ACCESS_TOKEN)

    def test_get_upper(self):
        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["EXAMPLE@EXAMPLE.COM"], ACCESS_TOKEN)

    def test_get_mixed(self):
        self.credentials_store["example@example.com"] = ACCESS_TOKEN
        self.assertEqual(self.credentials_store["eXaMpLe@ExAmPlE.cOm"], ACCESS_TOKEN)
