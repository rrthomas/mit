// Test the register instructions, except for those operating on RP and SP
// (see memory.c).
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"

#include "xvasprintf.h"


#define SIZE 1024

const char *correct[] = {
    "", "1", "1 1", "",
    "-33554432", "-33554432 1", "",
    "16384", "16384 1", "",
    "-16777216", "-16777216 1", "",
    "16384", "16384 1", "",
    "168", "",
    "168", "168 1", "",
    str(SIZE), str(SIZE) " 1", "",
    "0", "0 0", "0 0 2", "",
};


int main(void)
{
    int exception = 0;

    init((WORD *)malloc(SIZE), SIZE / WORD_W);

    start_ass(PC);
    ass(O_PUSH_PC); lit(1); ass(O_POP);
    ass(O_PUSH_S0); lit(1); ass(O_POP);
    ass(O_PUSH_SSIZE); lit(1); ass(O_POP);
    ass(O_PUSH_R0); lit(1); ass(O_POP);
    ass(O_PUSH_RSIZE); lit(1); ass(O_POP);
    lit(168); // 42 WORDS
    ass(O_STORE_HANDLER);
    ass(O_PUSH_HANDLER); lit(1); ass(O_POP);
    ass(O_PUSH_MEMORY); lit(1); ass(O_POP);
    ass(O_PUSH_BADPC); ass(O_PUSH_INVALID); lit(2); ass(O_POP);
    ass(O_PUSH_PSIZE);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in registers tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(I));
    }

    // Cannot statically stringify POINTER_W
    show_data_stack();
    char *pointer_w = xasprintf("%u", (unsigned)POINTER_W);
    printf("Correct stack: %s\n\n", pointer_w);
    if (strcmp(pointer_w, val_data_stack())) {
        printf("Error in registers tests: PC = %"PRIu32"\n", PC);
        exit(1);
    }
    free(pointer_w);

    assert(exception == 0);
    printf("Registers tests ran OK\n");
    return 0;
}
