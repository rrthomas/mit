// Test that single_step works, and that address alignment and bounds
// checking is properly performed on S->PC.
//
// (c) Reuben Thomas 1994-2018
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

    state *S = init_alloc(256);

    for (int i = 0; i < 10; i++) {
        printf("PC = %"PRI_UWORD"\n", S->PC);
        single_step(S);
    }

    const UWORD final_pc = 10;
    printf("PC should now be %"PRI_UWORD"\n", final_pc);
    if (S->PC != final_pc) {
        printf("Error in single_step(S) tests: S->PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    free(S->memory);
    destroy(S);

    assert(exception == 0);
    printf("single_step(S) tests ran OK\n");
    return 0;
}
