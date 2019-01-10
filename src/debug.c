// Functions useful for VM debugging.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <inttypes.h>

#include "xvasprintf.h"

#include "public.h"
#include "aux.h"
#include "debug.h"
#include "opcodes.h"


void ass_action(state *S, WORD instr)
{
    S->here += encode_instruction(S, S->here, INSTRUCTION_ACTION, instr);
}

void ass_number(state *S, WORD v)
{
    S->here += encode_instruction(S, S->here, INSTRUCTION_NUMBER, v);
}

void ass_native_pointer(state *S, void *ptr)
{
    for (unsigned i = 0; i < align(sizeof(void *)) / word_size; i++) {
        ass_number(S, (UWORD)((size_t)ptr & word_mask));
        ptr = (void *)((size_t)ptr >> word_bit);
    }
}

void ass_byte(state *S, BYTE byte)
{
    store_byte(S, S->here++, byte);
}

void start_ass(state *S, UWORD addr)
{
    S->here = addr;
}

_GL_ATTRIBUTE_PURE UWORD ass_current(state *S)
{
    return S->here;
}

static const char *mnemonic[O_UNDEFINED] = {
#undef INSTRUCTION
#define INSTRUCTION(name, opcode) #name,
#include "instruction-list.h"
#undef INSTRUCTION
};

_GL_ATTRIBUTE_CONST const char *disass(enum instruction_type type, WORD opcode)
{
    switch (type) {
    case INSTRUCTION_NUMBER:
        {
            static char *number = NULL;
            free(number);
            number = xasprintf("%"PRI_WORD" (%"PRI_XWORD")", opcode, (UWORD)opcode);
            return number;
        }
    case INSTRUCTION_ACTION:
        if (opcode < 0 || opcode >= O_UNDEFINED)
            return "undefined";
        return mnemonic[opcode];
    default:
        return "invalid type!";
    }
}

_GL_ATTRIBUTE_PURE UWORD toass(const char *token)
{
    for (size_t i = 0; i < sizeof(mnemonic) / sizeof(mnemonic[0]); i++)
        if (mnemonic[i] && strcasecmp(token, mnemonic[i]) == 0) return i;

    return O_UNDEFINED;
}

static char *_val_data_stack(state *S, bool with_hex)
{
    static char *picture = NULL;

    free(picture);
    picture = xasprintf("%s", "");
    if (!stack_underflow(S->SP, S->S0))
        for (UWORD i = 0; i != (UWORD)(S->SP - S->S0);) {
            char *ptr;
            i += stack_direction;
            if (!stack_valid(S->S0 + i, S->S0, S->SSIZE)) {
                ptr = xasprintf("%sinvalid address!", picture);
                free(picture);
                picture = ptr;
                break;
            }
            ptr = xasprintf("%s%"PRI_WORD, picture, S->S0[i]);
            free(picture);
            picture = ptr;
            if (with_hex) {
                ptr = xasprintf("%s (%"PRI_XWORD") ", picture, (UWORD)S->S0[i]);
                free(picture);
                picture = ptr;
            }
            if (i != (UWORD)(S->SP - S->S0)) {
                ptr = xasprintf("%s ", picture);
                free(picture);
                picture = ptr;
            }
        }

    return picture;
}

char *val_data_stack(state *S)
{
    return _val_data_stack(S, false);
}

void show_data_stack(state *S)
{
    if (S->SP == S->S0)
        printf("Data stack empty\n");
    else if (stack_underflow(S->SP, S->S0))
        printf("Data stack underflow\n");
    else
        printf("Data stack: %s\n", _val_data_stack(S, true));
}

void show_return_stack(state *S)
{
    if (S->RP == S->R0)
        printf("Return stack empty\n");
    else if (stack_underflow(S->RP, S->R0))
        printf("Return stack underflow\n");
    else {
        printf("Return stack: ");
        for (UWORD i = 0; i != (UWORD)(S->RP - S->R0);) {
            i += stack_direction;
            if (!stack_valid(S->R0 + i, S->R0, S->RSIZE)) {
                printf("invalid address!");
                break;
            }
            printf("%"PRI_XWORD" ", (UWORD)S->R0[i]);
        }
        putchar('\n');
    }
}
