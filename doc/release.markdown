# Release check list

## In yokadi checkout

Ensure checkout is up to date

Ensure version is ok in "version" file

	git push origin master:refs/heads/<serie>
	git fetch origin
	git checkout --track -b <serie> origin/<serie>

	git tag -a <version>
	git push --tags

Bump version on master

	git checkout master
	vi version

Go back to branch in order to prepare tarballs

	git co <serie>

## In yokadi.github.com checkout

Ensure checkout is up to date

	./updatedoc.py <path/to/yokadi/checkout> .
	./mkdist.sh <path/to/yokadi/checkout> download/

Write a blog entry in _posts/

Update version in download page (download.markdown)

## Tell the world

freshmeat.net
pypi.python.org
