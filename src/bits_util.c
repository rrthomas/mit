// Bit-counting utility functions.
//
// (c) Reuben Thomas 2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include "count-leading-zeros.h"
#include "verify.h"

#include "public.h"
#include "aux.h"


// Find most-significant bit set in a WORD-sized quantity
_GL_ATTRIBUTE_CONST int find_msbit(WORD v)
{
    if (v < 0)
        v = -v;

      // FIXME: Determine correct function to use properly
#if WORD_SIZE == 4
verify(sizeof(WORD) == sizeof(int));
    return WORD_BIT - 1 - count_leading_zeros((unsigned int)v);
#elif WORD_SIZE == 8
verify(sizeof(WORD) == sizeof(long int));
    return WORD_BIT - 1 - count_leading_zeros_l((unsigned long int)v);
#endif
}

// Return number of bytes required for a WORD-sized quantity
_GL_ATTRIBUTE_CONST int byte_size(WORD v)
{
    return find_msbit(v) / 8 + 1;
}
