// Header for warn() and die().
//
// (c) Mit authors 2019-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_WARN_H
#define MIT_WARN_H


#include <stdarg.h>


// Implementation-defined errors
enum {
    MIT_ERROR_STARTUP_ERROR = 128,
};

void verror(const char *format, va_list args);
void warn(const char *format, ...);
void die(const char *format, ...);

#endif
