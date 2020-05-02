// Stack manipulation.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "mit/mit.h"


_GL_ATTRIBUTE_PURE mit_word *mit_stack_position(mit_state *S, mit_uword pos)
{
    if (pos >= S->stack_depth)
        return NULL;
    return UNCHECKED_STACK(S->stack, S->stack_depth, pos);
}

int mit_pop_stack(mit_state *S, mit_word *val_ptr)
{
    if (S->stack_depth == 0)
        return MIT_ERROR_INVALID_STACK_READ;
    *val_ptr = *UNCHECKED_STACK(S->stack, S->stack_depth, 0);
    S->stack_depth--;
    return MIT_ERROR_OK;
}

int mit_push_stack(mit_state *S, mit_word val)
{
    if (unlikely(S->stack_depth >= S->stack_words))
        return MIT_ERROR_STACK_OVERFLOW;
    S->stack_depth++;
    *UNCHECKED_STACK(S->stack, S->stack_depth, 0) = val;
    return MIT_ERROR_OK;
}
