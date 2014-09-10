# -*- coding: UTF-8 -*-
"""
Crypto functions test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""

import unittest

import testutils

from yokadi.ycli import tui
from yokadi.core.cryptutils import YokadiCryptoManager
from yokadi.core.yokadiexception import YokadiException
from yokadi.core import db
from yokadi.core.db import setDefaultConfig


class CryptoTestCase(unittest.TestCase):
    def setUp(self):
        db.connectDatabase("", memoryDatabase=True)
        setDefaultConfig()
        self.session = db.getSession()
        tui.clearInputAnswers()

    def testEncrypt(self):
        mgr = YokadiCryptoManager()
        mgr.force_decrypt = True  # Simulate user ask for decryption
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)
        decrypted_sentence = mgr.decrypt(encrypted_sentence)
        self.assertEqual(important_sentence, decrypted_sentence)
        # Enter again same passphrase and check it is ok
        mgr = YokadiCryptoManager()
        tui.addInputAnswers("mySecretPassphrase")

    def testEncryptLongSentence(self):
        mgr = YokadiCryptoManager()
        mgr.force_decrypt = True  # Simulate user ask for decryption
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = '''This sentence is long long long long
                                This sentence is long
                                This sentence is long
                                This sentence is long
                                This sentence is long long long'''
        encrypted_sentence = mgr.encrypt(important_sentence)
        decrypted_sentence = mgr.decrypt(encrypted_sentence)
        self.assertEqual(important_sentence, decrypted_sentence)

    def testBadPassphrase(self):
        mgr = YokadiCryptoManager()
        mgr.force_decrypt = True  # Simulate user ask for decryption
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)

        mgr = YokadiCryptoManager()  # Define new manager with other passphrase
        mgr.force_decrypt = True  # Simulate user ask for decryption
        tui.addInputAnswers("theWrongSecretPassphrase")
        self.assertRaises(YokadiException, mgr.decrypt, encrypted_sentence)

    def testIfEncrypted(self):
        mgr = YokadiCryptoManager()
        mgr.force_decrypt = True  # Simulate user ask for decryption
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)
        self.assertTrue(mgr.isEncrypted(encrypted_sentence))
        self.assertFalse(mgr.isEncrypted(important_sentence))

        # Should not fail with empty data
        self.assertFalse(mgr.isEncrypted(None))
