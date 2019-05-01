# configure.ac for SMite
# Process this file with autoconf to produce a configure script

# (c) SMite authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

AC_INIT(SMite, 0.1, rrt@sc3d.org)
AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([-Wall -Werror foreign subdir-objects])
package_upper=`echo ${PACKAGE} | tr '[[:lower:]]' '[[:upper:]]'`
AC_SUBST([PACKAGE_UPPER], [$package_upper])
AC_DEFINE_UNQUOTED([PACKAGE_UPPER], ["$package_upper"], [PACKAGE upper-cased])

# Check for programs
AC_PROG_CC_C99
gl_EARLY
AM_PROG_AR
LT_INIT([win32-dll])
AM_PATH_PYTHON([3.4])
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
   IPYTHON_OPTS="--autocall 2"]
   AC_SUBST([IPYTHON_OPTS])
)
AC_PATH_PROG([LATEXMK], [latexmk], [true])
AC_PATH_PROG([SLOCCOUNT], [sloccount], [true])
AM_CONDITIONAL([HAVE_LATEXMK], [test "$ac_cv_path_LATEXMK" != "true"])
gl_INIT

# help2man
# Set a value even if not found, so that an invocation via build-aux/missing works
AC_PATH_PROG([HELP2MAN], [help2man], [help2man])

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
AC_ARG_VAR([WORD_BYTES],
  [value of WORD_BYTES register [default: sizeof(size_t)]])
: "${WORD_BYTES=$ac_cv_sizeof_size_t}"

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
AM_CONDITIONAL([USING_SUFFIX], [test "$gl_package_suffix" = "yes"])

# Generate output files
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
        Makefile
        lib/Makefile
        src/Makefile
        src/include/smite/smite.h
        src/feature/30-specializer/smite/specializer.h
        src/smite-include.man
        tests/Makefile
        python/Makefile
        python/smite/binding.py
        python/smite-dump.1
        python/smite-shell.1
        doc/Makefile
        doc/smite.tex
])
AC_CONFIG_FILES([python/smite-dump], [chmod +x python/smite-dump])
AC_CONFIG_FILES([python/smite-shell], [chmod +x python/smite-shell])
AC_OUTPUT
