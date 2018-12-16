// Test the CALL_NATIVE instruction.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM S->IS PROVIDED AS S->IS, WITH NO WARRANTY. USE S->IS AT THE USER‘S
// RISK.

#include "tests.h"


int exception = 0;
WORD temp;


static void test(state *S)
{
    PUSH(37);
}

int main(void)
{
    state *S = init_alloc(4096);

    ass_native_pointer(S, test); ass_action(S, O_CALL_NATIVE); ass_number(S, 0);
    ass_action(S, O_HALT);

    WORD res = run(S);
    if (res != 0) {
        printf("Error in CALL_NATIVE tests: test aborted with return code %"PRI_WORD"\n", res);
        exit(1);
    }

    printf("Top of stack is %"PRI_WORD"; should be %d\n", LOAD_WORD(S->SP), 37);
    show_data_stack(S);
    if (LOAD_WORD(S->SP) != 37) {
        printf("Error in CALL_NATIVE tests: incorrect value on top of stack\n");
        exit(1);
    }

    free(S->memory);
    destroy(S);

    assert(exception == 0);
    printf("CALL_NATIVE tests ran OK\n");
    return 0;
}
