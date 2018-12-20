// Test numbers.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


const WORD correct[] = {
  -257, 12345678, 4, (UWORD)1 << (WORD_BIT - 1),
  (UWORD)1 << (WORD_BIT - 2), (UWORD)0xff << (WORD_BIT - CHAR_BIT)
};
const char *encodings[sizeof(correct) / sizeof(correct[0])] = {
  "\x7f\xfb", "\x4e\x45\x46\x2f", "\x04",
#if WORD_SIZE == 4
  "\x40\x40\x40\x40\x40\xfe",
  "\x40\x40\x40\x40\x40\x01",
  "\x40\x40\x40\x40\xff"
#elif WORD_SIZE == 8
  "\x40\x40\x40\x40\x40\x40\x40\x40\x40\x40\xf8",
  "\x40\x40\x40\x40\x40\x40\x40\x40\x40\x40\x04",
  "\x40\x40\x40\x40\x40\x40\x40\x40\x40\xfc"
#endif
};

static void show_encoding(const char *encoding)
{
    size_t len = strlen(encoding);
    for (size_t i = 0; i < len; i++)
        printf("%02x ", (BYTE)encoding[i]);
}

static void ass_number_test(state *S, WORD n, const char *encoding)
{
    UWORD start = ass_current(S);
    printf("here = %"PRI_UWORD"\n", start);
    ass_number(S, n);
    UWORD len = ass_current(S) - start;
    ass_number(S, 1); ass_action(S, O_POP); // pop number so they don't build up on stack

    size_t bytes_ok = 0;
    printf("%"PRI_WORD" (%#"PRI_XWORD") encoded as: ", n, (UWORD)n);
    for (UWORD i = 0; i < len; i++) {
        BYTE b;
        load_byte(S, start + i, &b);
        printf("%02x ", b);
        if ((BYTE)encoding[i] == b)
            bytes_ok++;
    }
    if (bytes_ok != strlen(encoding)) {
        printf("Error in numbers tests: encoding should be ");
        show_encoding(encoding);
        printf("\n");
        exit(1);
    }
    printf("\n");
}


int main(void)
{
    int exception = 0;
    BYTE b;

    state *S = init_alloc(256);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++)
        ass_number_test(S, correct[i], encodings[i]);

    printf("here = %"PRI_UWORD"\n", ass_current(S));

    load_byte(S, 0, &b);
    printf("byte at 0 is %x\n", b);
    printf("\n");

    single_step(S); // Load first number
    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        printf("Correct stack: %"PRI_WORD" (%#"PRI_XWORD")\n\n", correct[i], (UWORD)correct[i]);
        ptrdiff_t actual;
        int items = sscanf(val_data_stack(S), "%td", &actual);
        if (items != 1 || correct[i] != actual) {
            printf("Error in numbers tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        single_step(S);
        single_step(S); // Execute 1 POP
        single_step(S);
        printf("I = %s\n", disass(INSTRUCTION_ACTION, S->I));
    }

    free(S->memory);
    destroy(S);

    assert(exception == 0);
    printf("Numbers tests ran OK\n");
    return 0;
}
