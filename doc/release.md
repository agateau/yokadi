# Release check list

## In yokadi checkout

Ensure checkout is up to date

Ensure version is OK in "version" file

Ensure NEWS file is up to date with new stuff and correct release date

Series is major.minor (ex: 0.12)
Version is major.minor.patch (ex 0.12.1)

For a new series:

    git checkout -b <series>
    git push origin <series>:<series>

For a new release in an existing series:

    git checkout <series>

Build archives

    ./scripts/mkdist.sh ../yokadi.github.com/download

Tag

    git tag -a <version>
    git push
    git push --tags

Bump version on master

    git checkout master
    vi version
    git commit version
    git push

## In yokadi.github.com checkout

Ensure checkout is up to date

    ./updatedoc.py <path/to/yokadi/checkout> .

Write a blog entry in `_posts/`

Update version in download page (download.markdown)

## Tell the world

- pypi.python.org
