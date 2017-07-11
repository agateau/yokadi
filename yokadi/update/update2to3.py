# -*- coding: UTF-8 -*-
"""
Update from version 2 to version 3 of Yokadi DB

@author: Sébastien Renard <Sebastien.Renard@digitalfox.org>
@license: GPL v3 or newer
"""


def createProjectKeywordTable(cursor):
    cursor.execute("""
create table project_keyword (
    id integer not null,
    project_id integer,
    keyword_id integer,
    primary key (id),
    unique (project_id, keyword_id),
    foreign key(project_id) references project (id),
    foreign key(keyword_id) references keyword (id)
)
""")


def update(cursor):
    createProjectKeywordTable(cursor)


if __name__ == "__main__":
    import updateutils
    updateutils.main(update)
# vi: ts=4 sw=4 et
