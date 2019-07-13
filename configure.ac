# configure.ac for Mit
# Process this file with autoconf to produce a configure script
#
# (c) Mit authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AC_PREREQ([2.69])

# Make inter-release version strings look like, e.g., v6.9-219-g58ddd, which
# indicates that it is built from the 219th delta (in _some_ repository)
# following the v6.9 tag, and that 58ddd is a prefix of the commit SHA1.
# The explicit URL can be removed when autoconf > 2.69 is released.
AC_INIT([Mit],
        m4_esyscmd([build-aux/git-version-gen .tarball-version]),
        [rrt@sc3d.org],
        [mit],
        [https://github.com/rrthomas/mit/])
AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([-Wall -Werror foreign subdir-objects])

# Check for programs
AC_PROG_CC_C99
gl_EARLY
AM_PROG_AR
LT_INIT([win32-dll])
AM_PATH_PYTHON([3.5])
AC_PATH_PROGS([IPYTHON], [ipython3 ipython])
# Check detected/configured IPython, and set command-line options
AS_IF([test "$IPYTHON" = ""],
   [# If we don't have IPython, fall back to Python
   IPYTHON=$PYTHON
   IPYTHON_OPTS=""],
   [# Check IPython is Python 3; error if not
   PYTHON_VERSION=`$IPYTHON --quick --no-term-title -c "import sys; print(sys.version_info.major)"`
   PYTHON_VERSION=${PYTHON_VERSION%\\n}
   AS_IF([test "$PYTHON_VERSION" != "3"], AC_MSG_ERROR([IPYTHON is not Python 3]))
   IPYTHON_OPTS="--autocall 2 --no-confirm-exit"]
   AC_SUBST([IPYTHON_OPTS])
)
AC_PATH_PROG([LATEXMK], [latexmk], [true])
AC_PATH_PROG([SLOCCOUNT], [sloccount], [true])
AM_CONDITIONAL([HAVE_LATEXMK], [test "$ac_cv_path_LATEXMK" != "true"])
gl_INIT

# help2man
# Set a value even if not found, so that an invocation via build-aux/missing works
AC_PATH_PROG([HELP2MAN], [help2man], [help2man])

# Timing/profiling
AC_PATH_PROG([TIME], [time])

# Optimization
AX_CC_MAXOPT
AX_GCC_BUILTIN(__builtin_expect)
if test "$ax_cv_have___builtin_expect" = yes; then
  HAVE___BUILTIN_EXPECT=1
else
  HAVE___BUILTIN_EXPECT=0
fi
AC_SUBST([HAVE___BUILTIN_EXPECT])

# Extra warnings with GCC
AC_ARG_ENABLE([gcc-warnings],
  [AS_HELP_STRING([--disable-gcc-warnings],
                  [turn off lots of GCC warnings])],
  [case $enableval in
     yes|no) ;;
     *)      AC_MSG_ERROR([bad value $enableval for gcc-warnings option]) ;;
   esac
   gl_gcc_warnings=$enableval],
  [gl_gcc_warnings=yes]
)
if test "$gl_gcc_warnings" = yes; then
  dnl Set up the list of undesired warnings.
  nw=
  nw="$nw -Wvla"              # Require C99, so variable-length arrays are OK
  nw="$nw -Wsystem-headers"   # Don’t let system headers trigger warnings
  nw="$nw -Wimplicit-fallthrough=5" # We want to allow "fallthrough" comments.

  gl_MANYWARN_ALL_GCC([warnings])

  dnl Enable all GCC warnings not in this list.
  gl_MANYWARN_COMPLEMENT([warnings], [$warnings], [$nw])
  for w in $warnings; do
    gl_WARN_ADD([$w])
  done

  dnl Add some more safety measures
  gl_WARN_ADD([-Wimplicit-fallthrough])
  gl_WARN_ADD([-Wswitch-default])
  gl_WARN_ADD([-D_FORTIFY_SOURCE=2])

  # When compiling with GCC, prefer -isystem to -I when including system
  # include files, to avoid generating useless diagnostics for the files.
  ISYSTEM='-isystem '
else
  ISYSTEM='-I'
fi
AC_SUBST([ISYSTEM])
AC_SUBST([PY_LOG_ENV])

# Accessing in-tree shared libraries
AC_SUBST([objdir])

# Check features
AX_C_ARITHMETIC_RSHIFT

# Set endianness
AC_C_BIGENDIAN
AC_SUBST([WORDS_BIGENDIAN])
AC_ARG_VAR([ENDISM],
  [value of ENDISM register [default: native endianness]])
if test "$ac_cv_c_bigendian" = "yes"; then
  WORDS_BIGENDIAN=1
else
  WORDS_BIGENDIAN=0
fi
: "${ENDISM=$WORDS_BIGENDIAN}"
case $ENDISM in
     0) endism_text=le ;;
     1) endism_text=be ;;
     *) AC_MSG_ERROR([bad value $ENDISM for ENDISM]) ;;
esac

# Set size of word
AC_CHECK_SIZEOF([size_t])
# Use a configure variable to substitute this in mit.h.in, where we can't
# include config.h, as mit.h is a public header.
SIZEOF_SIZE_T=$ac_cv_sizeof_size_t
AC_SUBST([SIZEOF_SIZE_T])
AC_ARG_VAR([WORD_BYTES],
  [value of WORD_BYTES register [default: sizeof(size_t)]])
: "${WORD_BYTES=$ac_cv_sizeof_size_t}"
AS_IF([test "$WORD_BYTES" = 16], [
  AX_HAVE_INT128
  AS_IF([test "$ax_cv_int128" != yes],
    AC_MSG_ERROR([Cannot find 128-bit support for WORD_BYTES=16]))])

# Set instruction opcode size
default_opcode_bit=8
AC_ARG_VAR([OPCODE_BIT],
  [value of MIT_OPCODE_BIT [default: $default_opcode_bit]])
: "${OPCODE_BIT=$default_opcode_bit}"

# Get size of largest integer
AC_CHECK_SIZEOF([intmax_t])
SIZEOF_INTMAX_T=$ac_cv_sizeof_intmax_t
AC_SUBST([SIZEOF_INTMAX_T])

# Package suffix for side-by-side installation of multiple builds
AC_ARG_ENABLE([package-suffix],
  [AS_HELP_STRING([--enable-package-suffix],
                  [add suffix containing values of ENDISM and WORD_BYTES, e.g. "-le-8", to binaries, libraries, include directories etc., enabling side-by-side installation of multiple builds.])],
  [case $enableval in
     yes|no) ;;
     *)      AC_MSG_ERROR([bad value $enableval for package-suffix option]) ;;
   esac
   gl_package_suffix=$enableval],
  [gl_package_suffix=no]
)
if test "$gl_package_suffix" = yes; then
  PACKAGE_SUFFIX=-$endism_text-$WORD_BYTES
fi
AC_SUBST([PACKAGE_SUFFIX])
AM_CONDITIONAL([USING_PACKAGE_SUFFIX], [test "$gl_package_suffix" = "yes"])

# pForth tests, run if the pforth source tree is present and Mit is
# configured compatibly with pForth.
AM_CONDITIONAL([USING_PFORTH],
   [test -d src/features/pforth -a "$WORD_BYTES" = 4 -a "$ENDISM" = 0])

# Generate output files
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
        Makefile
        lib/Makefile
        src/Makefile
        src/include/mit/mit.h
        src/mit_core/params.py
        src/features/mit/features.h
        tests/Makefile
        python/Makefile
        python/mit/binding.py
        python/mit-dump.1
        python/mit-shell.1
        doc/Makefile
])
AC_CONFIG_FILES([python/mit-dump], [chmod +x python/mit-dump])
AC_CONFIG_FILES([python/mit-shell], [chmod +x python/mit-shell])
AC_CONFIG_FILES([tests/test-mit-shell], [chmod +x tests/test-mit-shell])
AC_OUTPUT
