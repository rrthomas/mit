// Test the register instructions, except for those operating on RDEPTH and
// SDEPTH (see memory.c).
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


#define SIZE 1024

int main(void)
{
   const WORD correct[][8] =
       {
        {},
        {1},
        {1, 1},
        {},
        {16384},
        {16384, 1},
        {},
        {(UWORD)DEFAULT_STACK_SIZE},
        {(UWORD)DEFAULT_STACK_SIZE, 1},
        {},
        {42 * word_size},
        {},
        {42 * word_size},
        {42 * word_size, 1},
        {},
        {SIZE},
        {SIZE, 1},
        {},
        {ZERO},
        {ZERO, ZERO},
        {ZERO, ZERO, 2},
        {},
        {word_size},
        {word_size, native_pointer_size},
        {word_size, native_pointer_size, 2},
        {},
       };

    int exception = 0;

    state *S = init_default_stacks(SIZE / word_size);

    ass_action(S, O_PUSH_PC); ass_number(S, 1); ass_action(S, O_POP);
    ass_action(S, O_PUSH_SSIZE); ass_number(S, 1); ass_action(S, O_POP);
    ass_action(S, O_PUSH_RSIZE); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, 42 * word_size);
    ass_action(S, O_STORE_HANDLER);
    ass_action(S, O_PUSH_HANDLER); ass_number(S, 1); ass_action(S, O_POP);
    ass_action(S, O_PUSH_MEMORY); ass_number(S, 1); ass_action(S, O_POP);
    ass_action(S, O_PUSH_BADPC); ass_action(S, O_PUSH_INVALID); ass_number(S, 2); ass_action(S, O_POP);
    ass_action(S, O_PUSH_WORD_SIZE); ass_action(S, O_PUSH_NATIVE_POINTER_SIZE); ass_number(S, 2); ass_action(S, O_POP);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in registers tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    destroy(S);

    assert(exception == 0);
    printf("Registers tests ran OK\n");
    return 0;
}
