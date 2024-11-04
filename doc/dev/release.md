# Release check list

## Introduction

This doc assumes there is a checkout of yokadi.github.com next to the checkout
of yokadi.

## In yokadi checkout

    export version=<version>

Check dev is clean

    git checkout dev
    git pull
    git status

Update `CHANGELOG.md` file (add changes, check release date)

Ensure `yokadi/__init__.py` file contains $version

Build archives

    ./scripts/mkdist.sh ../yokadi.github.com/download

Push changes

    git push

When CI has checked the branch, merge changes in master

    git checkout master
    git pull
    git merge dev
    git push

Tag the release

    git tag -a $version -m "Releasing $version"
    git push --tags

## In yokadi.github.com checkout

Ensure checkout is up to date

Update documentation

    ./updatedoc.py ../yokadi .

Update version in download page (`download.md`)

Write a blog entry in `_posts/`

Test it:

    jekyll serve

Upload archives on PyPI

    cd download/
    twine upload yokadi-<version>.*

Publish blog post

    git add .
    git commit -m "Releasing $version"
    git push
