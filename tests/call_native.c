// Test the CALL_NATIVE instruction.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


int exception = 0;
WORD temp;


static void test(void)
{
    PUSH(37);
}

int main(void)
{
    init_alloc(4096);

    ass_native_pointer(test); ass_action(O_CALL_NATIVE); ass_number(0);
    ass_action(O_HALT);

    WORD res = run();
    if (res != 0) {
        printf("Error in CALL_NATIVE tests: test aborted with return code %"PRI_WORD"\n", res);
        exit(1);
    }

    printf("Top of stack is %"PRI_WORD"; should be %d\n", LOAD_WORD(SP), 37);
    show_data_stack();
    if (LOAD_WORD(SP) != 37) {
        printf("Error in CALL_NATIVE tests: incorrect value on top of stack\n");
        exit(1);
    }

    assert(exception == 0);
    printf("CALL_NATIVE tests ran OK\n");
    return 0;
}
