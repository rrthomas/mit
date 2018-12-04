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

#include "verify.h"
#include "xvasprintf.h"

#include "public.h"
#include "aux.h"
#include "debug.h"
#include "opcodes.h"


static UWORD here;	// where the current instruction word will be stored


// Find most-significant bit set in a WORD-sized quantity
// After https://stackoverflow.com/questions/2589096/find-most-significant-bit-left-most-that-is-set-in-a-bit-array
verify(WORD_BIT == 32); // FIXME: Code is hard-wired for 32 bits
static _GL_ATTRIBUTE_CONST unsigned find_msbit(WORD v)
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

void ass(BYTE instr)
{
    store_byte(here++, instr);
}

void lit(WORD v)
{
    // Continuation bytes
    for (unsigned bits = find_msbit(v) + 1; bits > LITERAL_CHUNK_BIT; bits -= LITERAL_CHUNK_BIT) {
        store_byte(here++, (BYTE)(v & LITERAL_CHUNK_MASK) | 0x40);
        v = ARSHIFT(v, LITERAL_CHUNK_BIT);
    }

    // Last (or only) byte
    store_byte(here++, (BYTE)v);
}

void plit(void (*literal)(void))
{
    WORD_pointer address = { .pointer = literal };
    for (unsigned i = 0; i < POINTER_W; i++)
        lit(address.words[i]);
}

void start_ass(UWORD addr)
{
    here = addr;
}

_GL_ATTRIBUTE_PURE UWORD ass_current(void)
{
    return here;
}

static const char *mnemonic[UINT8_MAX + 1] = {
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    "NOP", "POP", "PUSH", "SWAP", "RPUSH", "POP2R", "RPOP", "LT",
    "EQ", "ULT", "ADD", "MUL", "UDIVMOD", "DIVMOD", "NEGATE", "INVERT",
    "AND", "OR", "XOR", "LSHIFT", "RSHIFT", "LOAD", "STORE", "LOADB",
    "STOREB", "BRANCH", "BRANCHZ", "CALL", "RET", "THROW", "HALT", "CALL_NATIVE",
    "EXTRA", "PUSH_PSIZE", "PUSH_SP", "STORE_SP", "PUSH_RP", "STORE_RP", "PUSH_PC", "PUSH_S0",
    "PUSH_SSIZE", "PUSH_R0", "PUSH_RSIZE", "PUSH_HANDLER", "STORE_HANDLER", "PUSH_MEMORY", "PUSH_BADPC", "PUSH_INVALID",
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL };

_GL_ATTRIBUTE_CONST const char *disass(BYTE opcode)
{
    if (opcode <= 0x7f || opcode >= 0xc0)
        return "literal"; // FIXME: be more precise!
    if (mnemonic[opcode] == NULL) return "undefined";
    return mnemonic[opcode];
}

_GL_ATTRIBUTE_PURE BYTE toass(const char *token)
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
            i += WORD_W * STACK_DIRECTION;
            int exception = load_word(i, &c);
            if (exception != 0) {
                ptr = xasprintf("%sinvalid address!", picture);
                free(picture);
                picture = ptr;
                break;
            }
            ptr = xasprintf("%s%"PRId32, picture, c);
            free(picture);
            picture = ptr;
            if (with_hex) {
                ptr = xasprintf("%s (%#"PRIx32") ", picture, (UWORD)c);
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
            i += WORD_W * STACK_DIRECTION;
            int exception = load_word(i, &c);
            if (exception != 0) {
                printf("invalid address!\n");
                break;
            }
            printf("%#"PRIx32" ", (UWORD)c);
        }
        putchar('\n');
    }
}
