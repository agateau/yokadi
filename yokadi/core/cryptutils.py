# coding:utf-8
"""
Cryptographic functions for encrypting and decrypting text.
Temporary file are used by only contains encrypted data.

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3
"""

import base64
from random import Random

from yokadi.ycli import tui
from yokadi.core import db
from yokadi.core.yokadiexception import YokadiException

from sqlalchemy.orm.exc import NoResultFound

# Prefix used to recognise encrypted message
CRYPTO_PREFIX = "---YOKADI-ENCRYPTED-MESSAGE---"
# AES Key length
KEY_LENGTH = 32

try:
    from Crypto.Cipher import AES as Cypher
    CRYPT = True
except ImportError:
    tui.warning("Python Cryptographic Toolkit module not found. You will not be able to use cryptographic function")
    tui.warning("like encrypting or decrypting task title or description")
    tui.warning("You can find pycrypto here http://www.pycrypto.org")
    CRYPT = False

# TODO: add unit test


class YokadiCryptoManager(object):
    """Manager object for Yokadi cryptographic operation"""
    def __init__(self):
        # Cache encryption passphrase
        self.passphrase = None
        # Force decryption (and ask passphrase) instead of decrypting only when passphrase was
        # previously provided
        self.force_decrypt = False
        try:
            self.crypto_check = db.getConfigKey(u"CRYPTO_CHECK", environ=False)
        except NoResultFound:
            # Ok, set it to None. It will be setup after user defined passphrase
            self.crypto_check = None

    def encrypt(self, data):
        """Encrypt user data.
        @return: encrypted data"""
        if not CRYPT:
            tui.warning("Crypto functions not available")
            return data
        self.askPassphrase()
        return self._encrypt(data)

    def _encrypt(self, data):
        """Low level encryption interface. For internal usage only"""
        # Complete data with blanck
        data_length = (1 + (len(data) / KEY_LENGTH)) * KEY_LENGTH
        data = adjustString(data, data_length)
        cypher = Cypher.new(self.passphrase)
        return CRYPTO_PREFIX + base64.b64encode(cypher.encrypt(data))

    def decrypt(self, data):
        """Decrypt user data.
        @return: decrypted data"""
        if not self.isEncrypted(data):
            # Just return data as is if it's not encrypted
            return data

        if not CRYPT:
            tui.warning("Crypto functions not available")
            return data

        if not self.force_decrypt:
            # No flag to force decryption, just return fixed string to indicate
            # data is encrypted
            return "<... encrypted data...>"

        # Ask passphrase if needed and decrypt data
        self.askPassphrase()
        if self.passphrase:
            data = self._decrypt(data)
        else:
            data = "<...Failed to decrypt data...>"
        return data

    def _decrypt(self, data):
        """Low level decryption interface. For internal use only"""
        data = data[len(CRYPTO_PREFIX):]  # Remove crypto prefix
        data = base64.b64decode(data)
        cypher = Cypher.new(self.passphrase)
        return cypher.decrypt(data).rstrip()

    def askPassphrase(self):
        """Ask user for passphrase if needed"""
        cache = bool(int(db.getConfigKey("PASSPHRASE_CACHE", environ=False)))
        if self.passphrase and cache:
            return
        self.passphrase = tui.editLine("", prompt="passphrase> ", echo=False)
        self.passphrase = adjustString(self.passphrase, KEY_LENGTH)
        if not self.isPassphraseValid() and cache:
            self.passphrase = None
            self.force_decrypt = False  # As passphrase is invalid, don't force decrypt for next time
            raise YokadiException("Passphrase differ from previous one."
                        "If you really want to change passphrase, "
                        "you should blank the  CRYPTO_CHECK parameter "
                        "with c_set CRYPTO_CHECK '' "
                        "Note that you won't be able to retrieve previous tasks you "
                        "encrypted with your lost passphrase")
        else:
            # Now that passphrase is valid, we will always decrypt encrypted data
            self.force_decrypt = True

    def isEncrypted(self, data):
        """Check if data is encrypted
        @return: True is the data seems encrypted, else False"""
        return data is not None and data.startswith(CRYPTO_PREFIX)

    def isPassphraseValid(self):
        """Check if user passphrase is valid.
        ie. : if it can decrypt the check crypto word"""
        if not self.passphrase:
            # If no passphrase has been defined, it is definitively not valid !
            return False
        if self.crypto_check:
            try:
                int(self._decrypt(self.crypto_check))
                return True
            except ValueError:
                return False
        else:
            # First time that user enter a passphrase. Store the crypto check
            # for next time usage
            # We use a long string composed of int that we encrypt
            check_word = str(Random().getrandbits(KEY_LENGTH * KEY_LENGTH))
            check_word = adjustString(check_word, 10 * KEY_LENGTH)
            self.crypto_check = self._encrypt(check_word)

            # Save it to database config
            db.getSession().add(db.Config(name="CRYPTO_CHECK", value=self.crypto_check, system=True,
                      desc="Cryptographic check data of passphrase"))
            return True


def adjustString(string, length):
    """Adjust string to meet cipher requirement length"""
    string = string[:length]  # Shrink if key is too large
    string = string.ljust(length, " ")  # Complete if too short
    return string
