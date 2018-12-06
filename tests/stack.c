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

    init((WORD *)malloc(1024), 256);

    PUSH(1); PUSH(2); PUSH(3);	// initialise the stack

    start_ass(PC);

    // First part
    ass_number(0); ass_action(O_PUSH); ass_number(1); ass_action(O_POP);
    ass_number(1); ass_action(O_SWAP); ass_number(1); ass_action(O_PUSH);
    ass_number(1); ass_action(O_SWAP); ass_number(1); ass_action(O_POP);
    ass_number(0); ass_action(O_PUSH);

    // Second part
    ass_action(O_PUSH); ass_action(O_PUSH); ass_number(0); ass_action(O_PUSH);
    ass_number(0); ass_action(O_PUSH); ass_action(O_POP2R);
    ass_number(0); ass_action(O_RPUSH); ass_action(O_RPOP);

    size_t i;
    for (i = 0; i < 14; i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in stack tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    SP = S0;	// reset stack
    PUSH(2); PUSH(1); PUSH(0);	// initialise the stack
    printf("Next stack is wrong!\n");

    size_t first = i;
    for (; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack()) && i != first) {
            printf("Error in stack tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    assert(exception == 0);
    printf("Stack tests ran OK\n");
    return 0;
}
