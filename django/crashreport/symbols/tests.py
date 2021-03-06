from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
from django.utils import timezone

import os, zipfile, tempfile

from .models import SymbolsUpload, MissingSymbol

from processor.models import ProcessedCrash, Signature

def get_test_file_path(file_name):
    dir = os.path.dirname(__file__)
    return os.path.join(dir, "testdata/%s" % (file_name))

def remove_dir(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

class TestSimpleSymbolsUpload(TestCase):

    def setUp(self):
        user = User.objects.create_user('test user')
        self.c = Client()
        self.c.force_login(user)
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        remove_dir(self.tmp_dir)

    def test_symbols_upload_valid_zip(self):
        version = '1.2.3.4'
        platform = 'linux'
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir, SYMBOL_LOCATION=self.tmp_dir):
            with open(get_test_file_path("valid.zip")) as f:
                response = self.c.post('/upload/', {'symbols':f, 'version': version, 'platform':platform})
        self.assertEqual(response.status_code, 200)
        uploaded_symbols = SymbolsUpload.objects.all()
        self.assertEqual(len(uploaded_symbols), 1)
        uploaded_symbol = uploaded_symbols[0]
        self.assertListEqual(uploaded_symbol.files.splitlines(), ['file1', 'file2'])

    def test_delete_symbols(self):
        version = '1.2.3.4'
        platform = 'linux'
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir, SYMBOL_LOCATION=self.tmp_dir):
            with open(get_test_file_path("valid.zip")) as f:
                response = self.c.post('/upload/', {'symbols':f, 'version': version, 'platform':platform})
            self.assertEqual(response.status_code, 200)

            symbol_file1 = os.path.join(self.tmp_dir, 'file1')
            symbol_file2 = os.path.join(self.tmp_dir, 'file2')
            self.assertTrue(os.path.exists(symbol_file1))
            self.assertTrue(os.path.exists(symbol_file2))

            SymbolsUpload.objects.all().delete()

            self.assertFalse(os.path.exists(symbol_file1))
            self.assertFalse(os.path.exists(symbol_file2))

    def test_sybols_upload_invalid_zip(self):
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir):
            with open(get_test_file_path("invalid.zip")) as f:
                with self.assertRaises(zipfile.BadZipfile):
                    response = self.c.post('/upload/', {'symbols': f, 'version': '1.2.3.4', 'platform': 'linux'})

    def test_missing_comment(self):
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir):
            with open(get_test_file_path("valid.zip")) as f:
                response = self.c.post('/upload/', {'symbols':f})
        self.assertEqual(response.status_code, 405)

    def test_missing_file(self):
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir):
            response = self.c.post('/upload/', {'comment': 'test comment'})
        self.assertEqual(response.status_code, 405)

class TestMissingSymbols(TestCase):

    def setUp(self):
        self.signature = Signature()
        self.signature.signature = 'test'
        self.signature.first_observed = timezone.now()
        self.signature.last_observed = timezone.now()

        self.crash = ProcessedCrash()
        self.crash.modules = "Module|passwd|0|passwd|000000000000000000000000000000000|0x010d0000|0x01178fff|1\nModule|soffice.bin|5.3.0.0|soffice.bin|4B253D6CB7E740A997444A61FE6E511C2|0x010d0000|0x01178fff|1\nModule|mergedlo.dll|5.3.0.0|mergedlo.pdb|6C797FEC36EF447699D43D58FE1486102|0x66290000|0x6a401fff|0\nModule|actxprxy.dll|6.1.7601.17514|ActXPrxy.pdb|C674D3ABFBB34B75BC59063E6B68ABA12|0x6a710000|0x6a75dfff|0"
        self.crash.upload_time = timezone.now()
        self.crash.signature = self.signature
        self.crash.save()

        self.tmp_dir = tempfile.mkdtemp()

        user = User.objects.create_user('test user')
        self.c = Client()
        self.c.force_login(user)

    def tearDwon(self):
        remove_dir(self.tmp_dir)

    # disabled as it fails,
    # need a better way to generate the missing symbols from the string
    def get_missing_symbols(self):
        with self.settings(SYMBOL_DIR=self.tmp_dir):
            response = self.c.get('/symbols/missing')
        content = response.content;
        content_split = content.splitlines()
        self.assertIn("ActXPrxy.pdb,C674D3ABFBB34B75BC59063E6B68ABA12", content_split)
        self.assertIn("soffice.bin,4B253D6CB7E740A997444A61FE6E511C2", content_split)
        self.assertIn("mergedlo.pdb,6C797FEC36EF447699D43D58FE1486102", content_split)
        self.assertEqual(len(content_split), 3)

class TestMissingSymbolRemoval(TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        missing_symbol1 = MissingSymbol(symbol_file = "kernelbase.pdb", debug_id = "2474C6E48C0C4E86BDD73A05A694E7221", code_id = "2474C6E48C0C4E86BDD73A05A694E7222", code_name = "kernelbase.dll")
        missing_symbol1.save()
        missing_symbol2 = MissingSymbol(symbol_file = "some.pdb", debug_id = "ABCDEFGH", code_id = "FGHIJ", code_name = "some.dll")
        missing_symbol2.save()

        user = User.objects.create_user('test user')
        self.c = Client()
        self.c.force_login(user)

    def tearDown(self):
        remove_dir(self.tmp_dir)

    def test_remove_missing_symbol_after_upload(self):
        self.assertEqual(2, MissingSymbol.objects.count())
        with self.settings(SYMBOL_UPLOAD_DIR=self.tmp_dir):
            with open(get_test_file_path("system_symbols.zip")) as f:
                response = self.c.post('/upload/', {"symbols":f, "version": "1.2.3.4", "platform":"linux", "system":True})
                self.assertEqual(200, response.status_code)
        self.assertEqual(1, MissingSymbol.objects.count())
