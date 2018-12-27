// Test that run works, and that the return value of the HALT instruction is
// correctly returned.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


int main(void)
{
    int exception = 0;

    state *S = init_default(256);
    if (S == NULL) {
        printf("Error in run(S) tests: init with valid parameters failed\n");
        exit(1);
    }

    start_ass(S, 52);
    ass_number(S, 37);
    ass_action(S, O_HALT);

    WORD ret = run(S);

    const WORD return_value = 37;
    printf("Return value should be %"PRI_WORD" and is %"PRI_WORD"\n", return_value, ret);
    if (ret != return_value) {
        printf("Error in run(S) tests: incorrect return value from run\n");
        exit(1);
    }

    const UWORD final_pc = 54;
    printf("PC should now be %"PRI_UWORD"\n", final_pc);
    if (S->PC != final_pc) {
        printf("Error in run(S) tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    destroy(S);

    assert(exception == 0);
    printf("run(S) tests ran OK\n");
    return 0;
}
