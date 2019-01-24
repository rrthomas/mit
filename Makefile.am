# Top-level Makefile.am
#
# (c) Reuben Thomas 2011-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

SUBDIRS = lib src python tests doc

ACLOCAL_AMFLAGS = -I m4

EXTRA_DIST = README.md \
	m4/gnulib-cache.m4 \
	build-aux/add-symbol-prefix \
	build-aux/find-external-defines \
	build-aux/find-external-syms

loc:
	cd python && $(MAKE) loc
	cd src && $(MAKE) loc

release: distcheck
	git diff --exit-code && \
	git tag -a -m "Release tag" "v$(VERSION)" && \
	git push && git push --tags && \
	woger github \
		github_user=rrthomas \
		package=$(PACKAGE) \
		version=$(VERSION) \
		dist_type=tar.gz
