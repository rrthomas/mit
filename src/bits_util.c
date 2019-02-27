// Bit-counting utility functions.
//
// (c) Reuben Thomas 2018
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "count-leading-zeros.h"
#include "verify.h"

#include "smite.h"
#include "aux.h"


// Find most-significant bit set in a smite_WORD-sized quantity
_GL_ATTRIBUTE_CONST int smite_find_msbit(smite_WORD v)
{
    if (v < 0 && v > smite_word_min)
        v = -v;

#if WORD_SIZE == SIZEOF_INT
    return smite_word_bit - 1 - count_leading_zeros((unsigned int)v);
#elif WORD_SIZE == SIZEOF_LONG
    return smite_word_bit - 1 - count_leading_zeros_l((unsigned long int)v);
#elif WORD_SIZE == SIZEOF_LONG_LONG
    return smite_word_bit - 1 - count_leading_zeros_ll((unsigned long long int)v);
#else
#error "count-leading-zeroes lacks a function for WORD_SIZE!"
#endif
}

// Return number of bytes required for a smite_WORD-sized quantity
_GL_ATTRIBUTE_CONST int smite_byte_size(smite_WORD v)
{
    return smite_find_msbit(v) / 8 + 1;
}
