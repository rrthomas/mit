// Private implementation-specific APIs that are shared between modules.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef BEETLE_PRIVATE
#define BEETLE_PRIVATE


// Memory access

// Address checking
#define CHECK_ALIGNED(a)                        \
    if (!IS_ALIGNED(a)) {                       \
        S->INVALID = a;                         \
        exception = -23;                        \
    }


#endif
