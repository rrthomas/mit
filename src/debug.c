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
#include <inttypes.h>

#include "xvasprintf.h"

#include "public.h"
#include "aux.h"
#include "debug.h"
#include "opcodes.h"


static UWORD here;	// where the current instruction word will be stored


void ass_action(WORD instr)
{
    encode_instruction(&here, INSTRUCTION_ACTION, instr);
}

void ass_number(WORD v)
{
    encode_instruction(&here, INSTRUCTION_NUMBER, v);
}

void ass_native_pointer(void (*pointer)(void))
{
    WORD_pointer address = { .pointer = pointer };
    for (unsigned i = 0; i < NATIVE_POINTER_SIZE / WORD_SIZE; i++)
        ass_number(address.words[i]);
}

void ass_byte(BYTE byte)
{
    store_byte(here++, byte);
}

void start_ass(UWORD addr)
{
    here = addr;
}

_GL_ATTRIBUTE_PURE UWORD ass_current(void)
{
    return here;
}

static const char *mnemonic[O_UNDEFINED] = {
    "NOP", "POP", "PUSH", "SWAP", "RPUSH", "POP2R", "RPOP", "LT",
    "EQ", "ULT", "ADD", "MUL", "UDIVMOD", "DIVMOD", "NEGATE", "INVERT",
    "AND", "OR", "XOR", "LSHIFT", "RSHIFT", "LOAD", "STORE", "LOADB",
    "STOREB", "BRANCH", "BRANCHZ", "CALL", "RET", "THROW", "HALT", "CALL_NATIVE",
    "EXTRA", "PUSH_WORD_SIZE", "PUSH_POINTER_SIZE", "PUSH_NATIVE_POINTER_SIZE", "PUSH_SP", "STORE_SP", "PUSH_RP", "STORE_RP",
    "PUSH_PC", "PUSH_S0", "PUSH_SSIZE", "PUSH_R0", "PUSH_RSIZE", "PUSH_HANDLER", "STORE_HANDLER", "PUSH_MEMORY",
    "PUSH_BADPC", "PUSH_INVALID",
};

_GL_ATTRIBUTE_CONST const char *disass(enum instruction_type type, WORD opcode)
{
    switch (type) {
    case INSTRUCTION_NUMBER:
        {
            static char *number = NULL;
            free(number);
            number = xasprintf("%"PRI_WORD" (%#"PRI_XWORD")", opcode, (UWORD)opcode);
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
        if (mnemonic[i] && strcmp(token, mnemonic[i]) == 0) return i;

    return O_UNDEFINED;
}

static char *_val_data_stack(bool with_hex)
{
    static char *picture = NULL;

    free(picture);
    picture = xasprintf("%s", "");
    if (!STACK_UNDERFLOW(SP, S0))
        for (UWORD i = S0; i != SP;) {
            WORD c;
            char *ptr;
            i += WORD_SIZE * STACK_DIRECTION;
            int exception = load_word(i, &c);
            if (exception != 0) {
                ptr = xasprintf("%sinvalid address!", picture);
                free(picture);
                picture = ptr;
                break;
            }
            ptr = xasprintf("%s%"PRI_WORD, picture, c);
            free(picture);
            picture = ptr;
            if (with_hex) {
                ptr = xasprintf("%s (%#"PRI_XWORD") ", picture, (UWORD)c);
                free(picture);
                picture = ptr;
            }
            if (i != SP) {
                ptr = xasprintf("%s ", picture);
                free(picture);
                picture = ptr;
            }
        }

    return picture;
}

char *val_data_stack(void)
{
    return _val_data_stack(false);
}

void show_data_stack(void)
{
    if (SP == S0)
        printf("Data stack empty\n");
    else if (STACK_UNDERFLOW(SP, S0))
        printf("Data stack underflow\n");
    else
        printf("Data stack: %s\n", _val_data_stack(true));
}

void show_return_stack(void)
{
    if (RP == R0)
        printf("Return stack empty\n");
    else if (STACK_UNDERFLOW(RP, R0))
        printf("Return stack underflow\n");
    else {
        printf("Return stack: ");
        for (UWORD i = R0; i != RP;) {
            WORD c;
            i += WORD_SIZE * STACK_DIRECTION;
            int exception = load_word(i, &c);
            if (exception != 0) {
                printf("invalid address!\n");
                break;
            }
            printf("%#"PRI_XWORD" ", (UWORD)c);
        }
        putchar('\n');
    }
}
