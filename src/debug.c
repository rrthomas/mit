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


static int ibytes; // number of opcodes assembled in current instruction word so far
static WORD iword;  // accumulator for instructions being assembled
static UWORD current;	// where the current instruction word will be stored
static UWORD here; // where we assemble the next instruction word or literal


// Return number of bytes required for a WORD-sized quantity
// After https://stackoverflow.com/questions/2589096/find-most-significant-bit-left-most-that-is-set-in-a-bit-array
verify(WORD_BIT == 32); // Code is hard-wired for 32 bits
_GL_ATTRIBUTE_CONST int byte_size(WORD v)
{
    static const int pos[32] = {
        0, 9, 1, 10, 13, 21, 2, 29, 11, 14, 16, 18, 22, 25, 3, 30,
        8, 12, 20, 28, 15, 17, 24, 7, 19, 27, 23, 6, 26, 5, 4, 31
    };

    if (v < 0)
        v = -v;

    v |= v >> 1; // first round down to one less than a power of 2
    v |= v >> 2;
    v |= v >> 4;
    v |= v >> 8;
    v |= v >> 16;

    return pos[(UWORD)(v * 0x07C4ACDDU) >> 27] / 8 + 1;
}

void ass(BYTE instr)
{
    iword |= instr << ibytes * 8;
    store_word(current, iword);
    ibytes++;
    if (ibytes == WORD_W) {
        current = here;  here += WORD_W;
        iword = 0;  ibytes = 0;
    }
}

void lit(WORD literal)
{
    if (ibytes == 0) { store_word(here - WORD_W, literal);  current += WORD_W; }
    else { store_word(here, literal); }
    here += WORD_W;
}

void plit(void (*literal)(void))
{
    WORD_pointer address;
    unsigned i;
    address.pointer = literal;
    for (i = 0; i < POINTER_W; i++) {
        ass(O_LITERAL);
        lit(address.words[i]);
    }
}

void start_ass(UWORD addr)
{
    here = addr;  ibytes = 0;  iword = 0;  current = here;  here += WORD_W;
}

_GL_ATTRIBUTE_PURE UWORD ass_current(void)
{
    return current;
}

static const char *mnemonic[UINT8_MAX + 1] = {
    "NEXT00", "POP", "PUSH", "SWAP", "RPUSH", ">R", "R>", "<",
    "=", "U<", "+", "*", "UMOD/", "SREM/", "NEGATE", "INVERT",
    "AND", "OR", "XOR", "LSHIFT", "RSHIFT", "@", "!", "C@",
    "C!", "SP@", "SP!", "RP@", "RP!", "PC@", "PC!", "?PC!",
    "S0@", "#S", "R0@", "#R", "'THROW@", "'THROW!", "MEMORY@", "'BAD@",
    "-ADDRESS@", "CALL", "RET", "THROW", "HALT", "LINK", "(LITERAL)", NULL,
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
    "ARGC", "ARG", "STDIN_FILENO", "STDOUT_FILENO", "STDERR_FILENO", "OPEN-FILE", "CLOSE-FILE", "READ-FILE",
    "WRITE-FILE", "FILE-POSITION", "REPOSITION-FILE", "FLUSH-FILE", "RENAME-FILE", "DELETE-FILE", "FILE-SIZE", "RESIZE-FILE",
    "FILE-STATUS", NULL, NULL, NULL, NULL, NULL, NULL, NULL,
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
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, "NEXTFF" };

_GL_ATTRIBUTE_CONST const char *disass(BYTE opcode)
{
    if (mnemonic[opcode] == NULL) return "";
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
                ptr = xasprintf("%s ($%"PRIX32") ", picture, (UWORD)c);
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
            printf("$%"PRIX32" ", (UWORD)c);
        }
        putchar('\n');
    }
}
