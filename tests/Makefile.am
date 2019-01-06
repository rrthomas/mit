# Tests Makefile.am
#
# (c) Reuben Thomas 2011-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

AM_CPPFLAGS = -I$(top_srcdir)/src -I$(top_builddir)/lib -I$(top_srcdir)/lib $(WARN_CFLAGS)

noinst_LTLIBRARIES = libtest.la
libtest_la_SOURCES = test_util.c

LOG_COMPILER = $(srcdir)/run-test

LDADD = $(top_builddir)/src/lib@PACKAGE@.la libtest.la

noinst_PROGRAMS = load_object
check_PROGRAMS = arithmetic branch comparison init numbers logic memory \
	registers stack single_step run exceptions call_native extra_libc
check_SCRIPTS = hello.test

TESTS = $(check_PROGRAMS) $(check_SCRIPTS)
TESTS_ENVIRONMENT = \
	if test -n "$(VALGRIND)"; then export VALGRIND='$(VALGRIND)'; fi; \
	export LIBTOOL=$(top_builddir)/libtool; \
	export TEST_RUNNER=$(top_srcdir)/build-aux/test-runner; \
	export EXECUTOR=$(top_builddir)/src/@PACKAGE@$(EXEEXT);

do_load_object: load_object
	( $(TESTS_ENVIRONMENT) $(LOG_COMPILER) $(top_builddir)/src/@PACKAGE@$(EXEEXT) < $(srcdir)/numbers.asm ) && \
	$(TESTS_ENVIRONMENT) $(LOG_COMPILER) $(builddir)/load_object $(srcdir) $(builddir) && \
	rm numbers.obj

check-local: do_load_object

EXTRA_DIST = run-test tests.h \
	badobj1-4 badobj2-4 badobj3-4 badobj4-4 \
	badobj1-8 badobj2-8 badobj3-8 badobj4-8 \
	testobj1-be-4 testobj1-le-4 \
	testobj1-be-8 testobj1-le-8 \
	testobj2-be-4 testobj2-le-4 \
	testobj2-be-8 testobj2-le-8 \
	TEST.test \
	hello.test hello.asm hello.correct \
	numbers.asm
