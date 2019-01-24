dnl Process this file with autoconf to produce a configure script

AC_INIT(SMite, 0.1, rrt@sc3d.org)
AC_CONFIG_AUX_DIR([build-aux])
AM_INIT_AUTOMAKE([-Wall -Werror foreign])
package_upper=`echo ${PACKAGE} | tr '[[:lower:]]' '[[:upper:]]'`
AC_SUBST([PACKAGE_UPPER], [$package_upper])
AC_DEFINE_UNQUOTED([PACKAGE_UPPER], ["$package_upper"], [PACKAGE upper-cased])

dnl Check for programs
AC_PROG_CC_C99
gl_EARLY
AM_PROG_AR
LT_INIT
AM_PATH_PYTHON([3.4])
AC_PATH_PROG(LATEXMK, latexmk, true)
AM_CONDITIONAL([HAVE_LATEXMK], [test "$ac_cv_path_LATEXMK" != "true"])
gl_INIT

dnl help2man
dnl Set a value even if not found, so that an invocation via build-aux/missing works
AC_PATH_PROG([HELP2MAN], [help2man], [help2man])

dnl Extra warnings with GCC
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

  gl_MANYWARN_ALL_GCC([warnings])

  dnl Enable all GCC warnings not in this list.
  gl_MANYWARN_COMPLEMENT([warnings], [$warnings], [$nw])
  for w in $warnings; do
    gl_WARN_ADD([$w])
  done

  dnl Add some more safety measures
  gl_WARN_ADD([-D_FORTIFY_SOURCE=2])

  # When compiling with GCC, prefer -isystem to -I when including system
  # include files, to avoid generating useless diagnostics for the files.
  ISYSTEM='-isystem '
else
  ISYSTEM='-I'
fi
AC_SUBST([ISYSTEM])
AC_SUBST([PY_LOG_ENV])

dnl Accessing in-tree shared libraries
AC_SUBST([objdir])

dnl Check features
AC_C_BIGENDIAN

dnl Set size of word
AC_CHECK_SIZEOF([int])
AC_CHECK_SIZEOF([long])
AC_CHECK_SIZEOF([long long])
AC_ARG_VAR([WORD_SIZE],
  [value of WORD_SIZE register [default: sizeof(long)]])
: "${WORD_SIZE=SIZEOF_LONG}"

dnl Generate output files
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
        Makefile
        lib/Makefile
        src/Makefile
        src/public.h
        src/smite-dump.1
        tests/Makefile
        contrib/Makefile
        doc/Makefile
        doc/smite.tex
        doc/csmite.tex
        doc/shell.tex
])
AC_CONFIG_FILES([build-aux/add-symbol-prefix], [chmod +x build-aux/add-symbol-prefix])
AC_OUTPUT
