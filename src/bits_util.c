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

#include "verify.h"

#include "public.h"
#include "aux.h"


// Find most-significant bit set in a WORD-sized quantity
// After https://stackoverflow.com/questions/2589096/find-most-significant-bit-left-most-that-is-set-in-a-bit-array
verify(WORD_BIT == 32); // FIXME: Code is hard-wired for 32 bits
_GL_ATTRIBUTE_CONST unsigned find_msbit(WORD v)
{
    static const unsigned pos[32] = {
        0, 9, 1, 10, 13, 21, 2, 29, 11, 14, 16, 18, 22, 25, 3, 30,
        8, 12, 20, 28, 15, 17, 24, 7, 19, 27, 23, 6, 26, 5, 4, 31
    };

    if (v < 0)
        v = -v;

    v |= v >> 1; // first round up to one less than a power of 2
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;

    return pos[(UWORD)(v * 0x07C4ACDDU) >> 27];
}

// Return number of bytes required for a WORD-sized quantity
_GL_ATTRIBUTE_CONST unsigned byte_size(WORD v)
{
    return find_msbit(v) / 8 + 1;
}
