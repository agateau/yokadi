# Release check list

## Introduction

This doc assumes there is a checkout of yokadi.github.com next to the checkout
of yokadi.

## In yokadi checkout

- [ ] Define version

  ```
  export version=<version>
  ```

- [ ] Check dev is clean

  ```
  git checkout dev
  git pull
  git status
    ```

- [ ] Update `CHANGELOG.md` file (add changes, check release date)

- [ ] Ensure `yokadi/__init__.py` file contains $version

- [ ] Build archives

  ```
  ./scripts/mkdist.sh ../yokadi.github.com/download
  ```

- [ ] Push changes

  ```
  git push
  ```

- [ ] Open PR to merge in master

  ```
  gh pr create --fill
  ```

- [ ] Tag the release

  ```
  git checkout master
  git pull
  git tag -a $version -m "Releasing $version"
  git push origin $version
  ```

## In yokadi.github.com checkout

- [ ] Ensure checkout is up to date

- [ ] Update documentation

  ```
  ./updatedoc.py ../yokadi .
  ```

- [ ] Update version in download page (`download.md`)

- [ ] Write a blog entry in `_posts/`

- [ ] Test it:

  ```
  jekyll serve
  ```

- [ ] Upload archives on PyPI

  ```
  cd download/
  twine upload yokadi-<version>.*
  ```

- [ ] Publish blog post

  ```
  git add .
  git commit -m "Releasing $version"
  git push
  ```
