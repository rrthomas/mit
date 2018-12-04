// Test literals.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


WORD correct[] = {
  -257, 12345678, 4, 0x80000000,
  0x40000000, 0xff000000
};
const char *encodings[sizeof(correct) / sizeof(correct[0])] = {
  "\x7f\xfb", "\x4e\x45\x46\x2f", "\x04", "\x40\x40\x40\x40\x40\xfe",
  "\x40\x40\x40\x40\x40\x01", "\x40\x40\x40\x40\xff"
};

static void show_encoding(const char *encoding)
{
    size_t len = strlen(encoding);
    for (size_t i = 0; i < len; i++)
        printf("%02x ", (BYTE)encoding[i]);
}

static void ass_literal_test(WORD n, const char *encoding)
{
    UWORD start = ass_current();
    printf("here = %"PRIu32"\n", start);
    lit(n);
    UWORD len = ass_current() - start;
    lit(1); ass(O_POP); // pop number so they don't build up on stack

    size_t bytes_ok = 0;
    printf("%"PRId32" (%#"PRIx32") encoded as: ", n, (UWORD)n);
    for (UWORD i = 0; i < len; i++) {
        BYTE b;
        load_byte(start + i, &b);
        printf("%02x ", b);
        if ((BYTE)encoding[i] == b)
            bytes_ok++;
    }
    if (bytes_ok != strlen(encoding)) {
        printf("Error in literals tests: encoding should be ");
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

    init((WORD *)calloc(1024, 1), 256);

    start_ass(PC);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++)
        ass_literal_test(correct[i], encodings[i]);

    printf("here = %"PRIu32"\n", ass_current());

    load_byte(0, &b);
    printf("byte at 0 is %x\n", b);
    printf("\n");

    single_step(); // Load first literal
    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %"PRId32" (%#"PRIx32")\n\n", correct[i], (UWORD)correct[i]);
        ptrdiff_t actual;
        int items = sscanf(val_data_stack(), "%td", &actual);
        if (items != 1 || correct[i] != actual) {
            printf("Error in literals tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        single_step(); // Execute 1 POP
        single_step();
        printf("I = %s\n", disass(I));
    }

    assert(exception == 0);
    printf("Literals tests ran OK\n");
    return 0;
}
