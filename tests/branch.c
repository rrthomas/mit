// Test the branch instructions. Also uses instructions tested by
// earlier tests.
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

    state *S = init_default_stacks(4096);

    start_ass(S, 0);
    ass_number(S, 96); ass_action(S, O_BRANCH);

    start_ass(S, 96);
    ass_number(S, 48); ass_action(S, O_BRANCH);

    start_ass(S, 48);
    ass_number(S, 10000); ass_action(S, O_BRANCH);

    start_ass(S, 10000);
    ass_number(S, 1);
    ass_number(S, 10008); ass_action(S, O_BRANCHZ);
    ass_number(S, 1);
    ass_number(S, 0); ass_action(S, O_BRANCHZ); ass_number(S, 0);
    ass_number(S, 11000); ass_action(S, O_BRANCHZ);

    start_ass(S, 11000);
    ass_number(S, 0);
    ass_number(S, 11016); ass_action(S, O_BRANCHZ);

    start_ass(S, 11016);
    ass_number(S, 60);
    ass_action(S, O_CALL);

    start_ass(S, 60);
    ass_number(S, 200); ass_action(S, O_CALL);
    ass_number(S, 64);
    ass_number(S, 24);
    ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, 1); ass_action(S, O_PUSH); ass_action(S, O_STORE); ass_action(S, O_LOAD);
    ass_action(S, O_CALL);

    start_ass(S, 200);
    ass_number(S, 300); ass_action(S, O_CALL);
    ass_action(S, O_RET);

    start_ass(S, 300);
    ass_action(S, O_RET);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        printf("Instruction %zu: PC = %"PRI_UWORD"; should be %u\n\n", i, S->PC, correct[i]);
        if (correct[i] != S->PC) {
            printf("Error in branch tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    destroy(S);

    assert(exception == 0);
    printf("Branch tests ran OK\n");
    return 0;
}
