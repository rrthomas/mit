# configure.ac for Mit
# Process this file with autoconf to produce a configure script
#
# (c) Mit authors 2011-2020
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
AM_INIT_AUTOMAKE([-Wall foreign subdir-objects])

# Check for programs
AC_PROG_CC_C99
gl_EARLY
AM_PROG_AR
LT_INIT([win32-dll])
AM_PATH_PYTHON([3.7])
AC_PATH_PROGS([IPYTHON], [ipython3 ipython])
# Check detected/configured IPython, and set command-line options
AS_IF([test "$IPYTHON" = ""],
   [# If we don't have IPython, fall back to Python
   IPYTHON=$PYTHON
   IPYTHON_OPTS=""],
   [# Check IPython is Python 3; error if not
   # On mingw32, run ipython script with python.exe to avoid using winpty
   case $host in
     *mingw32) PYTHON_PREFIX=$ac_cv_path_PYTHON ;;
     *) PYTHON_PREFIX="" ;;
   esac
   PYTHON_VERSION=`$PYTHON_PREFIX $IPYTHON --quick --no-term-title -c "import sys; print(sys.version_info.major)"`
   PYTHON_VERSION=${PYTHON_VERSION%\\n}
   AS_IF([test "$PYTHON_VERSION" != "3"], AC_MSG_ERROR([IPYTHON is not Python 3]))
   IPYTHON_OPTS="--profile mit-shell --ext mit.ipython_suppress_traceback --autocall 2 --no-confirm-exit"]
   AC_SUBST([IPYTHON_OPTS])
)
AC_PATH_PROG([LATEXMK], [latexmk], [true])
AC_PATH_PROG([SLOCCOUNT], [sloccount], [true])
AM_CONDITIONAL([HAVE_LATEXMK], [test "$ac_cv_path_LATEXMK" != "true"])
gl_INIT

# Test whether we have cygpath
# Code adapted from automake's init.m4
if test -z "$CYGPATH_M"; then
  if (cygpath --version) >/dev/null 2>/dev/null; then
    CYGPATH_M='cygpath -m'
  else
    CYGPATH_M=echo
  fi
fi
AC_SUBST([CYGPATH_M])

# help2man
# Set a value even if not found, so that an invocation via build-aux/missing works
AC_PATH_PROG([HELP2MAN], [help2man], [help2man])

# Timing/profiling
AC_PATH_PROG([TIME], [time])
AC_PATH_PROG([OPERF], [operf])
AS_IF([test "$ac_cv_path_OPERF" != ""], [
  AX_CPU_VENDOR
  case $ax_cv_cpu_vendor in
    Intel)
      OPERF_OPTIONS="--events INST_RETIRED:100000";;
    AMD)
      OPERF_OPTIONS="--events RETIRED_INSTRUCTIONS:200000";;
    *)
      AC_MSG_WARN([Don't know how to run operf on this arch]);;
  esac
])
AC_SUBST([OPERF_OPTIONS])

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
  # Set up the list of undesired warnings.
  nw=
  nw="$nw -Wvla"              # We require C99, so variable-length arrays are OK
  nw="$nw -Wsystem-headers"   # Don’t let system headers trigger warnings
  nw="$nw -Wimplicit-fallthrough=5" # We want to allow "fallthrough" comments.

  gl_MANYWARN_ALL_GCC([warnings])

  # Enable all GCC warnings not in this list.
  gl_MANYWARN_COMPLEMENT([warnings], [$warnings], [$nw])
  for w in $warnings; do
    gl_WARN_ADD([$w])
  done

  # Add some more safety measures
  gl_WARN_ADD([-Wimplicit-fallthrough])
  gl_WARN_ADD([-Wswitch-default])

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

# Thread-local storage
AC_ARG_ENABLE([tls],
  [AS_HELP_STRING([--disable-tls],
                  [do not use thread-local storage])],
  [
  case $enableval in
    yes|no) ;;
    *)      AC_MSG_ERROR([bad value $enableval for tls option]) ;;
  esac
  if test "$enableval" = yes; then
    case $host in
      # Disable by default on some platforms
      # MingW/MSYS: see https://sourceforge.net/p/mingw-w64/bugs/827/
      # macOS: segfault when a library with a _Thread_local is dlopened (e.g. in Python)
      *mingw32|*msys|*darwin*) AC_MSG_WARN([Thread-local storage is disabled by default on this platform]);;
      *) AX_TLS ;;
    esac
  fi
  AS_IF([test "$ac_cv_tls" = "" -o "$ac_cv_tls" = "none"],
    AC_MSG_WARN([Define THREAD_LOCAL to a storage specifier if desired.]))
  AC_ARG_VAR([THREAD_LOCAL],
    [storage specifier for thread-local storage [default: auto-detected]])
  : "${THREAD_LOCAL=$ac_cv_tls}"])

# Check features
AC_C_BIGENDIAN
AC_CHECK_SIZEOF([size_t]) # word_bytes
SIZEOF_SIZE_T=$ac_cv_sizeof_size_t
AS_IF([test "$SIZEOF_SIZE_T" != 4 -a "$SIZEOF_SIZE_T" != 8],
   AC_MSG_ERROR([sizeof(size_t) must be 4 or 8!]))
AC_SUBST([SIZEOF_SIZE_T])
AX_C_ARITHMETIC_RSHIFT
AC_CHECK_SIZEOF([intmax_t]) # largest stack item
SIZEOF_INTMAX_T=$ac_cv_sizeof_intmax_t
AC_SUBST([SIZEOF_INTMAX_T])

# Package suffix for side-by-side installation of multiple builds
AC_ARG_ENABLE([package-suffix],
  [AS_HELP_STRING([--enable-package-suffix],
                  [add suffix denoting the endianness and word size, e.g. "-le-8", to binaries and man pages, enabling side-by-side installation of multiple builds.])],
  [case $enableval in
     yes|no) ;;
     *)      AC_MSG_ERROR([bad value $enableval for package-suffix option]) ;;
   esac
   gl_package_suffix=$enableval],
  [gl_package_suffix=no]
)
if test "$gl_package_suffix" = yes; then
  if test "$ac_cv_c_bigendian" = "yes"; then
    endism_text=be
  else
    endism_text=le
  fi
  PACKAGE_SUFFIX=-$endism_text-$ac_cv_sizeof_size_t
fi
AC_SUBST([PACKAGE_SUFFIX])
AM_CONDITIONAL([USING_PACKAGE_SUFFIX], [test "$gl_package_suffix" = "yes"])

# pForth tests, run if the pforth source tree is present and Mit is
# configured compatibly with pForth.
# AM_CONDITIONAL([USING_PFORTH],
#    [test -d $srcdir/src/specializer/pforth -a "$SIZEOF_SIZE_T" = 4 -a "$ac_cv_c_bigendian" != "yes"])

# Generate output files
AC_CONFIG_HEADERS([config.h])
AC_CONFIG_FILES([
        Makefile
        build-aux/man-include.man
        lib/Makefile
        src/Makefile
        src/run.h
        src/include/mit/mit.h
        src/mit-include.man
        python/Makefile
        python/mit-shell-include.man
        tests/Makefile
        doc/Makefile
])
AC_CONFIG_FILES([python/mit-profile], [chmod +x python/mit-profile])
AC_CONFIG_FILES([python/mit-shell], [chmod +x python/mit-shell])
AC_CONFIG_FILES([tests/test-mit-shell], [chmod +x tests/test-mit-shell])
AC_OUTPUT
