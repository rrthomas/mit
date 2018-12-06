// Test the arithmetic operators. Also uses the SWAP and POP instructions,
// and numbers. Since unsigned arithmetic overflow behaviour is guaranteed
// by the ISO C standard, we only test the stack handling and basic
// correctness of the operators here, assuming that if the arithmetic works
// in one case, it will work in all. Note that the correct stack values are
// not quite independent of the word size (in WORD_W and str(WORD_W)); some
// stack pictures implicitly refer to it.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


const char *correct[] = {
    "", "0", "0 1", "0 1 " str(WORD_W), "0 1 " str(WORD_W) " -" str(WORD_W),
    "0 1 " str(WORD_W) " -" str(WORD_W) " -1", "0 1 " str(WORD_W) " -5",
    "0 1 -1", "0 1 1", "0 2", "0 2 1", "2 0", "2 0 -1", "2 0 -1 " str(WORD_W),
    "2 0 -" str(WORD_W), "2 0 -" str(WORD_W) " 1", "2 -" str(WORD_W) " 0",
    "2 -" str(WORD_W) " 0 2", "2", "-2", "-2 -1", "2 0", "2 0 1", "0 2", "0 2 2", "",
    str(WORD_W), "-" str(WORD_W), "-" str(WORD_W) " 1", "", "-" str(WORD_W),
    "-" str(WORD_W) " 3", "-1 -1", "-1 -1 1", "-1", "-1 -2", "1 1" };


int main(void)
{
    int exception = 0;

    init((WORD *)calloc(1024, 1), 256);

    start_ass(PC);
    ass_number(0);
    ass_number(1);
    ass_number(WORD_W);
    ass_number(-WORD_W);
    ass_number(-1);
    ass_action(O_ADD); ass_action(O_ADD); ass_action(O_NEGATE);
    ass_action(O_ADD); ass_number(1); ass_action(O_SWAP); ass_number(-1);
    ass_number(WORD_W);
    ass_action(O_MUL); ass_number(1); ass_action(O_SWAP); ass_number(2); ass_action(O_POP);
    ass_action(O_NEGATE); ass_number(-1);
    ass_action(O_DIVMOD); ass_number(1); ass_action(O_SWAP); ass_number(2); ass_action(O_POP);
    ass_number(WORD_W); ass_action(O_NEGATE); ass_number(1); ass_action(O_POP);
    ass_number(-WORD_W);
    ass_number(3);
    ass_action(O_DIVMOD); ass_number(1); ass_action(O_POP); ass_number(-2);
    ass_action(O_UDIVMOD);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in arithmetic tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    assert(exception == 0);
    printf("Arithmetic tests ran OK\n");
    return 0;
}
