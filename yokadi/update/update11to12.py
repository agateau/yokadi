"""
Update from version 11 to version 12 of Yokadi DB

- Decrypt all encrypted tasks

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
import base64

from getpass import getpass

from yokadi.update import updateutils
from yokadi.ycli import tui

try:
    from Crypto.Cipher import AES as CRYPTO_ALGO
except ImportError:
    CRYPTO_ALGO = None

CRYPTO_PREFIX = "---YOKADI-ENCRYPTED-MESSAGE---"
KEY_LENGTH = 32

CRYPTO_CHECK_KEY = "CRYPTO_CHECK"
CONFIG_KEYS = "PASSPHRASE_CACHE", CRYPTO_CHECK_KEY


def getPassphrase():
    phrase = getpass(prompt="Enter passphrase: ")
    phrase = phrase[:KEY_LENGTH]
    return phrase.ljust(KEY_LENGTH, " ")


def decryptData(cypher, data):
    if not data:
        return data
    data = data[len(CRYPTO_PREFIX):]  # Remove crypto prefix
    data = base64.b64decode(data)
    return cypher.decrypt(data).rstrip().decode(encoding="utf-8")


def decryptTask(cursor, cypher, row):
    taskId, title, description = row
    title = decryptData(cypher, title)
    description = decryptData(cypher, description)
    cursor.execute("update task set title = ?, description = ? where id = ?",
                   (title, description, taskId))


def getCheckText(cursor):
    sql = "select value from config where name like ?"
    row = cursor.execute(sql, (CRYPTO_CHECK_KEY,)).fetchone()
    return row[0]


def checkPassphrase(cypher, checkText):
    try:
        decryptData(cypher, checkText)
        return True
    except UnicodeDecodeError:
        return False


def decryptEncryptedTasks(cursor):
    sql = "select id, title, description from task where title like ?"

    rows = cursor.execute(sql, (CRYPTO_PREFIX + "%",)).fetchall()
    if not rows:
        return

    if CRYPTO_ALGO is None:
        msg = ("This database contains encrypted data but pycrypto is not"
               " installed.\n"
               "Please install pycrypto and try again.")
        raise updateutils.UpdateError(msg)

    if not tui.confirm("This database contains encrypted tasks, but Yokadi no "
                       "longer supports encryption.\n"
                       "These tasks need to be decrypted to continue using "
                       "Yokadi.\n"
                       "Do you want to decrypt your tasks?"):
        raise updateutils.UpdateCanceledError()

    checkText = getCheckText(cursor)
    while True:
        phrase = getPassphrase()
        cypher = CRYPTO_ALGO.new(phrase)
        if checkPassphrase(cypher, checkText):
            break
        else:
            if not tui.confirm("Wrong passphrase, try again?"):
                raise updateutils.UpdateCanceledError()
    for row in rows:
        decryptTask(cursor, cypher, row)


def removeCryptoConfigKeys(cursor):
    sql = "delete from config where name like ?"
    for key in CONFIG_KEYS:
        cursor.execute(sql, (key,))


def update(cursor):
    decryptEncryptedTasks(cursor)
    removeCryptoConfigKeys(cursor)


if __name__ == "__main__":
    updateutils.main(update)
# vi: ts=4 sw=4 et
