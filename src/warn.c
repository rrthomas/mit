// warn() and die().
//
// (c) Mit authors 2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdnoreturn.h>

#include "mit/mit.h"
#include "warn.h"


_GL_ATTRIBUTE_FORMAT_PRINTF(1, 0) void verror(const char *format, va_list args)
{
    fprintf(stderr, PACKAGE ": ");
    vfprintf(stderr, format, args);
    fprintf(stderr, "\n");
}

_GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void warn(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
}

noreturn _GL_ATTRIBUTE_FORMAT_PRINTF(1, 2) void die(const char *format, ...)
{
    va_list args;

    va_start(args, format);
    verror(format, args);
    exit(MIT_ERROR_STARTUP_ERROR);
}
