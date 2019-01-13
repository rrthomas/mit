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


#define CORRECT 37

static void test(state *S)
{
    PUSH(CORRECT);
}

int main(void)
{
    state *S = init_default_stacks(4096);

    ass_native_pointer(S, test); ass_action(S, O_CALL_NATIVE); ass_number(S, 0);
    ass_action(S, O_HALT);

    WORD res = run(S);
    if (res != 0) {
        printf("Error in CALL_NATIVE tests: test aborted with return code %"PRI_WORD"\n", res);
        exit(1);
    }

    WORD top_word;
    load_stack(S->S0, S->SDEPTH, 0, &top_word);
    printf("Top of stack is %"PRI_WORD"; should be %d\n", top_word, CORRECT);
    show_data_stack(S);
    if (top_word != CORRECT) {
        printf("Error in CALL_NATIVE tests: incorrect value on top of stack\n");
        exit(1);
    }

    destroy(S);

    assert(exception == 0);
    printf("CALL_NATIVE tests ran OK\n");
    return 0;
}
