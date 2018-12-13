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
verify(sizeof(WORD) == sizeof(int)); // FIXME
_GL_ATTRIBUTE_CONST int find_msbit(WORD v)
{
    if (v < 0)
        v = -v;

    return 31 - count_leading_zeros((unsigned int)v);
}

// Return number of bytes required for a WORD-sized quantity
_GL_ATTRIBUTE_CONST int byte_size(WORD v)
{
    return find_msbit(v) / 8 + 1;
}
