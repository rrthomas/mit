// Test the arithmetic operators. Also uses the SWAP and POP instructions,
// and numbers. Since unsigned arithmetic overflow behaviour is guaranteed
// by the ISO C standard, we only test the stack handling and basic
// correctness of the operators here, assuming that if the arithmetic works
// in one case, it will work in all.
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
    const WORD correct[][8] =
        {
         {},
         {ZERO},
         {ZERO, 1},
         {ZERO, 1, word_size},
         {ZERO, 1, word_size, -word_size},
         {ZERO, 1, word_size, -word_size, -1},
         {ZERO, 1, word_size, -word_size - 1},
         {ZERO, 1, -1},
         {ZERO, 1, 1},
         {ZERO, 2},
         {ZERO, 2, 1},
         {2, ZERO},
         {2, ZERO, -1},
         {2, ZERO, -1, word_size},
         {2, ZERO, -word_size},
         {2, ZERO, -word_size, 1},
         {2, -word_size, ZERO},
         {2, -word_size, ZERO, 2},
         {2},
         {-2},
         {-2, -1},
         {2, ZERO},
         {2, ZERO, 1},
         {ZERO, 2},
         {ZERO, 2, 2},
         {},
         {word_size},
         {-word_size},
         {-word_size, 1},
         {},
         {-word_size},
         {-word_size, word_size - 1},
         {-1, -1},
         {-1, -1, 1},
         {-1},
         {-1, -2},
         {1, 1},
        };

    int exception = 0;

    state *S = init_default_stacks(256);

    ass_number(S, 0);
    ass_number(S, 1);
    ass_number(S, word_size);
    ass_number(S, -word_size);
    ass_number(S, -1);
    ass_action(S, O_ADD); ass_action(S, O_ADD); ass_action(S, O_NEGATE);
    ass_action(S, O_ADD); ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, -1);
    ass_number(S, word_size);
    ass_action(S, O_MUL); ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, 2); ass_action(S, O_POP);
    ass_action(S, O_NEGATE); ass_number(S, -1);
    ass_action(S, O_DIVMOD); ass_number(S, 1); ass_action(S, O_SWAP); ass_number(S, 2); ass_action(S, O_POP);
    ass_number(S, word_size); ass_action(S, O_NEGATE); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, -word_size);
    ass_number(S, word_size - 1);
    ass_action(S, O_DIVMOD); ass_number(S, 1); ass_action(S, O_POP); ass_number(S, -2);
    ass_action(S, O_UDIVMOD);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in arithmetic tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    destroy(S);

    assert(exception == 0);
    printf("Arithmetic tests ran OK\n");
    return 0;
}
