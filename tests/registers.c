// Test the register instructions, except for those operating on RP and SP
// (see memory.c). Also uses NEXT.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


#define SIZE 1024

const char *correct[] = {
    "", str(WORD_W), str(WORD_W) " 1", "",
    "-33554432", "-33554432 1", "",
    "16384", "16384 1", "",
    "-16777216", "-16777216 1", "",
    "16384", "16384 1", "",
    "168", "",
    "168", "168 1", "",
    str(SIZE), str(SIZE) " 1", "",
    "-1", "-1 -1",
};


int main(void)
{
    int exception = 0;

    init((WORD *)malloc(SIZE), SIZE / WORD_W);

    start_ass(PC);
    ass(O_PUSH_PC); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_S0); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_SSIZE); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_R0); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_RSIZE); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_LITERAL); lit(168); // 42 WORDS
    ass(O_STORE_HANDLER);
    ass(O_PUSH_HANDLER); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_MEMORY); ass(O_LITERAL); lit(1); ass(O_POP);
    ass(O_PUSH_BADPC); ass(O_PUSH_INVALID);

    assert(single_step() == -259);   // load first instruction word

    for (size_t i = 0; i - i / 5 < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i - i / 5]);
        if (strcmp(correct[i - i / 5], val_data_stack())) {
            printf("Error in registers tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(I));
    }

    assert(exception == 0);
    printf("Registers tests ran OK\n");
    return 0;
}
