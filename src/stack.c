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


int mit_load_stack(mit_state *S, mit_uword pos, mit_word *val_ptr)
{
    return load_stack(S->stack, S->stack_depth, pos, val_ptr);
}

int mit_store_stack(mit_state *S, mit_uword pos, mit_word val)
{
    return store_stack(S->stack, S->stack_depth, pos, val);
}

int mit_pop_stack(mit_state *S, mit_word *val_ptr)
{
    int ret = load_stack(S->stack, S->stack_depth, 0, val_ptr);
    S->stack_depth--;
    return ret;
}

int mit_push_stack(mit_state *S, mit_word val)
{
    if (unlikely(S->stack_depth >= S->stack_words))
        return MIT_ERROR_STACK_OVERFLOW;

    (S->stack_depth)++;
    return store_stack(S->stack, S->stack_depth, 0, val);
}
