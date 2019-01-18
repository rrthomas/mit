# Tests Makefile.am
#
# (c) Reuben Thomas 2011-2018
#
# The package is distributed under the GNU Public License version 3, or,
# at your option, any later version.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
# RISK.

TEST_EXTENSIONS = .py
# FIXME: run Python under Valgrind with run-test (but not libtool)
#LOG_COMPILER = $(srcdir)/run-test
PY_LOG_COMPILER = $(PYTHON)

check_SCRIPTS =		\
	arithmetic.py	\
	branch.py	\
	call_native.py	\
	comparison.py	\
	extra_libc.py	\
	exceptions.py	\
	hello.py	\
	init.py		\
	load_object.py	\
	logic.py	\
	memory.py	\
	numbers.py	\
	registers.py	\
	run.py		\
	save_object.py	\
	single_step.py	\
	stack.py

TESTS = $(check_SCRIPTS) $(check_PROGRAMS)
TESTS_ENVIRONMENT = \
	if test -n "$(VALGRIND)"; then export VALGRIND='$(VALGRIND) --suppressions=$(srcdir)/valgrind-python.supp'; fi; \
	export LD_LIBRARY_PATH=$(top_builddir)/src/@objdir@; \
	export PYTHON=$(PYTHON); \
	export PYTHONPATH=$(top_srcdir)/src:$(srcdir); \
	export srcdir=$(srcdir); \
	export builddir=$(builddir);

EXTRA_DIST = run-test \
	$(check_SCRIPTS) \
	redirect_stdout.py \
	valgrind-python.supp \
	badobj1-4 badobj2-4 badobj3-4 badobj4-4 \
	badobj1-8 badobj2-8 badobj3-8 badobj4-8 \
	testobj1-be-4 testobj1-le-4 \
	testobj1-be-8 testobj1-le-8 \
	testobj2-be-4 testobj2-le-4 \
	testobj2-be-8 testobj2-le-8 \
	hello.py hello.correct
