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


const char *correct[] = { "", "-257", "-257 12345678", "-257 12345678 4" };


// FIXME: Check encoding is actually correct by comparing encoded literals
// against known-correct binary patterns.
int main(void)
{
    int exception = 0;
    BYTE b;

    init((WORD *)calloc(1024, 1), 256);

    start_ass(PC);
    printf("here = %"PRIu32"\n", ass_current());
    lit(-257);
    printf("here = %"PRIu32"\n", ass_current());
    lit(12345678);
    printf("here = %"PRIu32"\n", ass_current());
    lit(4);
    printf("here = %"PRIu32"\n", ass_current());

    load_byte(0, &b);
    printf("byte at 0 is %x\n", b);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in literals tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(I));
    }

    assert(exception == 0);
    printf("Literals tests ran OK\n");
    return 0;
}
