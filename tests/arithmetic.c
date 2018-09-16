// Test the arithmetic operators. Also uses the NEXT, SWAP, ROT,
// DROP, and (LITERAL) instructions. Since unsigned arithmetic
// overflow behaviour is guaranteed by the ISO C standard, we only test
// the stack handling and basic correctness of the operators here,
// assuming that if the arithmetic works in one case, it will work in
// all. Note that the correct stack values are not quite independent
// of the cell size (in CELL_W and str(CELL_W)); some stack pictures
// implicitly refer to it.
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
    "", "0", "0 1", "0 1 " str(CELL_W), "0 1 " str(CELL_W) " -" str(CELL_W), "0 1 " str(CELL_W) " -" str(CELL_W),
    "0 1 " str(CELL_W) " -" str(CELL_W) " -1", "0 1 " str(CELL_W) " -5",
    "0 1 -1", "0 1 1", "0 1 1", "0 2", "2 0", "2 0 -1", "2 0 -1 " str(CELL_W),
    "2 0 -1 " str(CELL_W), "2 0 -" str(CELL_W), "2 -" str(CELL_W) " 0",
    "2 -" str(CELL_W), "2", "2", "-2", "-2 -1", "2 0", "0 2", "0 2", "0", "",
    str(CELL_W), "-" str(CELL_W), "-" str(CELL_W), "", "-" str(CELL_W),
    "-" str(CELL_W) " 3", "-1 -1", "-1 -1", "-1", "-1 -2", "1 1" };


int main(void)
{
    int exception = 0;

    init((CELL *)calloc(1024, 1), 256);

    start_ass(EP);
    ass(O_LITERAL); lit(0);
    ass(O_LITERAL); lit(1);
    ass(O_LITERAL); lit(CELL_W);
    ass(O_LITERAL); lit(-CELL_W);
    ass(O_LITERAL); lit(-1);
    ass(O_PLUS); ass(O_PLUS); ass(O_NEGATE);
    ass(O_PLUS); ass(O_SWAP); ass(O_LITERAL); lit(-1);
    ass(O_LITERAL); lit(CELL_W);
    ass(O_STAR); ass(O_SWAP); ass(O_DROP); ass(O_DROP);
    ass(O_NEGATE); ass(O_LITERAL); lit(-1);
    ass(O_SREMSLASH); ass(O_SWAP); ass(O_DROP); ass(O_DROP);
    ass(O_LITERAL); lit(CELL_W); ass(O_NEGATE); ass(O_DROP);
    ass(O_LITERAL); lit(-CELL_W);
    ass(O_LITERAL); lit(3);
    ass(O_SREMSLASH); ass(O_DROP); ass(O_LITERAL); lit(-2);
    ass(O_UMODSLASH);

    assert(single_step() == -259);   // load first instruction word

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in arithmetic tests: EP = %"PRIu32"\n", EP);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(I));
    }

    assert(exception == 0);
    printf("Arithmetic tests ran OK\n");
    return 0;
}
