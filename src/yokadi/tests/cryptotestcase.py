# -*- coding: UTF-8 -*-
"""
Crypto functions test cases
@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or later
"""


import unittest

import testutils
import tui

from cryptutils import YokadiCryptoManager

class CryptoTestCase(unittest.TestCase):
    def setUp(self):
        testutils.clearDatabase()
        tui.clearInputAnswers()

    def testEncrypt(self):
        mgr = YokadiCryptoManager()
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)
        decrypted_sentence = mgr.decrypt(encrypted_sentence)
        self.assertEqual(important_sentence, decrypted_sentence)

    def testBadPassphrase(self):
        mgr = YokadiCryptoManager()
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)

        mgr = YokadiCryptoManager() # Define new manager with other passphrase
        tui.addInputAnswers("theWrongSecretPassphrase")
        decrypted_sentence = mgr.decrypt(encrypted_sentence)
        self.assertNotEqual(important_sentence, decrypted_sentence)

    def testIfEncrypted(self):
        mgr = YokadiCryptoManager()
        tui.addInputAnswers("mySecretPassphrase")
        important_sentence = "Don't tell anyone"
        encrypted_sentence = mgr.encrypt(important_sentence)
        self.assertTrue(mgr.isEncrypted(encrypted_sentence))
        self.assertFalse(mgr.isEncrypted(important_sentence))
