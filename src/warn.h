// Header for warn() and die().
//
// (c) Mit authors 2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include <stdarg.h>


void verror(const char *format, va_list args);
void warn(const char *format, ...);
void die(const char *format, ...);
