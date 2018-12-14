// Utility functions for VM tests.
//
// (c) Reuben Thomas 2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


char *xasprint_array(const WORD *array, WORD zero)
{
  char *s = strdup("");
  for (size_t i = 0; array[i] != 0; i++) {
    char *s_ = xasprintf("%s%s%"PRI_WORD, s, i > 0 ? " " : "", array[i] == zero ? 0 : array[i]);
    free(s);
    s = s_;
  }
  return s;
}
