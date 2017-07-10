"""
Update from version 11 to version 12 of Yokadi DB

- No db change, but update sync dump from version 1 to version 2

@author: Aurélien Gâteau <mail@agateau.com>
@license: GPL v3 or newer
"""
from yokadi.update import updateutils


def update(cursor):
    pass


if __name__ == "__main__":
    updateutils.main(update)
# vi: ts=4 sw=4 et
