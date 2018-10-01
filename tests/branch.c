// Test the branch instructions. Also uses other instructions with lower
// opcodes than the instructions tested (i.e. those already tested).
// See exceptions.c for address exception handling tests.
// The test program contains an infinite loop, but this is only executed
// once.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


unsigned correct[] = { 0, 2, 96, 97, 48, 51, 10000, 10001, 10004, 10005, 10006, 10007, 10008,
                       10009, 10012, 11000, 11001, 11004, 11016, 11017, 60, 62,
                       200, 202, 300, 203, 63, 65, 66, 67, 68, 69, 70, 71, 72, 64 };


int main(void)
{
    int exception = 0;

    size_t size = 4096;
    init((WORD *)calloc(size, WORD_W), size);

    start_ass(PC);
    lit(96); ass(O_BRANCH);

    start_ass(96);
    lit(48); ass(O_BRANCH);

    start_ass(48);
    lit(10000); ass(O_BRANCH);

    start_ass(10000);
    lit(1);
    lit(10008); ass(O_BRANCHZ);
    lit(1);
    lit(0); ass(O_BRANCHZ); lit(0);
    lit(11000); ass(O_BRANCHZ);

    start_ass(11000);
    lit(0);
    lit(11016); ass(O_BRANCHZ);

    start_ass(11016);
    lit(60);
    ass(O_CALL);

    start_ass(60);
    lit(200); ass(O_CALL);
    lit(64);
    lit(20);
    lit(1); ass(O_SWAP); lit(1); ass(O_PUSH); ass(O_STORE); ass(O_LOAD);
    ass(O_CALL);

    start_ass(200);
    lit(300); ass(O_CALL);
    ass(O_RET);

    start_ass(300);
    ass(O_RET);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        printf("Instruction %zu: PC = %u; should be %u\n\n", i, PC, correct[i]);
        if (correct[i] != PC) {
            printf("Error in branch tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(I));
    }

    assert(exception == 0);
    printf("Branch tests ran OK\n");
    return 0;
}
