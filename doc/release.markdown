# Release check list

## In yokadi checkout

Ensure checkout is up to date

Ensure version is ok in "version" file

Ensure NEWS file is up to date with new stuff and correct release date.

Serie is like 0.12
Version is like 0.12.0

	git push origin master:refs/heads/<serie>
	git fetch origin
	git checkout --track -b <serie> origin/<serie>

	git tag -a <version>
	git push --tags

Bump version on master

	git checkout master
	vi version
	git commit version

Go back to branch in order to prepare tarballs

	git checkout <serie>

## In yokadi.github.com checkout

Ensure checkout is up to date

	./updatedoc.py <path/to/yokadi/checkout> .
	./mkdist.sh <path/to/yokadi/checkout> download/

Write a blog entry in _posts/

Update version in download page (download.markdown)

## Tell the world

freshmeat.net
pypi.python.org
