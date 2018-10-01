// Test that single_step works, and that address alignment and bounds
// checking is properly performed on PC.
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

    init((WORD *)calloc(1024, 1), 256);

    for (int i = 0; i < 10; i++) {
        printf("PC = %u\n", PC);
        single_step();
    }

    const UWORD final_pc = 10;
    printf("PC should now be %"PRIu32"\n", final_pc);
    if (PC != final_pc) {
        printf("Error in single_step() tests: PC = %"PRIu32"\n", PC);
        exit(1);
    }

    assert(exception == 0);
    printf("single_step() tests ran OK\n");
    return 0;
}
