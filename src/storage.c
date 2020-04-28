// Manage storage for the state, registers and memory.
//
// (c) Mit authors 1994-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "mit/mit.h"


// Constants
const unsigned mit_word_bytes = MIT_WORD_BYTES;
const unsigned mit_byte_bit = 8;
const unsigned mit_byte_mask = MIT_BYTE_MASK;
const unsigned mit_word_bit = MIT_WORD_BIT;
const mit_uword mit_word_mask = MIT_WORD_MASK;
const mit_uword mit_uword_max = MIT_UWORD_MAX;
const mit_word mit_word_min = MIT_WORD_MIN;
const mit_word mit_word_max = MIT_WORD_MAX;
const unsigned mit_opcode_bit = MIT_OPCODE_BIT;
const unsigned mit_opcode_mask = MIT_OPCODE_MASK;


// Stacks

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
