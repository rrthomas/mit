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

    int i = init((WORD *)calloc(1024, 1), 256);
    if (i != 0) {
        printf("Error in run() tests: init with valid parameters failed\n");
        exit(1);
    }

    start_ass(52);
    ass_number(37);
    ass_action(O_HALT);

    WORD ret = run();

    const WORD return_value = 37;
    printf("Return value should be %d and is %"PRId32"\n", return_value, ret);
    if (ret != return_value) {
        printf("Error in run() tests: incorrect return value from run\n");
        exit(1);
    }

    const UWORD final_pc = 54;
    printf("PC should now be %"PRIu32"\n", final_pc);
    if (PC != final_pc) {
        printf("Error in run() tests: PC = %"PRIu32"\n", PC);
        exit(1);
    }

    assert(exception == 0);
    printf("run() tests ran OK\n");
    return 0;
}
