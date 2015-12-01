# Release check list

## Introduction

A series is major.minor (ex: 0.12). There is a branch for each series.

A version is major.minor.patch (ex 0.12.1). There is a tag for each version.

This doc assumes there is a checkout of yokadi.github.com next to the checkout
of yokadi.

## In yokadi checkout

    export version=<version>
    export series=<series>

### For a new series

Update `NEWS` file (add changes, check release date)

Ensure `version` file contains $version

Create branch:

    git checkout -b $series
    git push -u origin $series

The version in master should always be bigger than the version in release
branches, so update version in master:

    git checkout master
    vi version
    git commit version -m "Bump version number"
    git push
    git checkout -

### For a new release in an existing series

    git checkout <series>

Update `NEWS` file (add changes, check release date)

Bump version number

    echo $version > version
    git commit version -m "Getting ready for $version"

### Common

Build archives

    ./scripts/mkdist.sh ../yokadi.github.com/download

Tag

    git tag -a $version -m "Releasing $version"

Push changes

    git push
    git push --tags

Merge changes in master (so that future forward merges are simpler). Be careful
to keep version to its master value.

    git checkout master
    git merge --no-ff $series
    git push
    git checkout -

## Post on PyPI

    twine upload ../yokadi.github.com/download/yokadi-$version.*

## In yokadi.github.com checkout

Ensure checkout is up to date

Update documentation

    ./updatedoc.py ../yokadi .

Write a blog entry in `_posts/`

Update version in download page (`download.md`)

Publish

    git add .
    git commit
    git push
