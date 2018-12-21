// Test the stack operators.
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
    "1 2 3", "1 2 3 0", "1 2 3 3", "1 2 3 3 1", "1 2 3", "1 2 3 1", "1 3 2", "1 3 2 1", "1 3 2 3", "1 3 2 3 1",
    "1 3 3 2", "1 3 3 2 1", "1 3 3", "1 3 3 0", "1 3 3 3",
    "2 1 1", "2 1 2", "2 1 2 0", "2 1 2 2", "2 1 2 2 0", "2 1 2 2 2", "2 1 2 2", "2 1 2 2 0", "2 1 2 2 2", "2 1 2 2 2 2"};


int main(void)
{
    int exception = 0;

    state *S = init_alloc(256);

    PUSH(1); PUSH(2); PUSH(3);	// initialise the stack

    // First part
    ass_number(S, 0); ass_action(S, O_PUSH); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, 1); ass_action(S, O_PUSH);
    ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, 0); ass_action(S, O_PUSH);

    // Second part
    ass_action(S, O_PUSH); ass_action(S, O_PUSH); ass_number(S, 0); ass_action(S, O_PUSH);
    ass_number(S, 0); ass_action(S, O_PUSH); ass_action(S, O_POP2R);
    ass_number(S, 0); ass_action(S, O_RPUSH); ass_action(S, O_RPOP);

    size_t i;
    for (i = 0; i < 14; i++) {
        show_data_stack(S);
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack(S))) {
            printf("Error in stack tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    S->SP = S->S0;	// reset stack
    PUSH(2); PUSH(1); PUSH(0);	// initialise the stack
    printf("Next stack is wrong!\n");

    size_t first = i;
    for (; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack(S)) && i != first) {
            printf("Error in stack tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    free(S->memory);
    destroy(S);

    assert(exception == 0);
    printf("Stack tests ran OK\n");
    return 0;
}
