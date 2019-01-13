// Test the memory operators. Also uses previously tested instructions.
// See exceptions.c for address exception handling tests.
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
    unsigned size = 4096;

    const WORD correct[][8] =
        {
         {},
         {size * word_size},
         {size * word_size, word_size},
         {size * word_size, -word_size},
         {size * word_size - word_size},
         {size * word_size - word_size, 513},
         {size * word_size - word_size, 513, 1},
         {size * word_size - word_size, 513, size * word_size - word_size},
         {size * word_size - word_size},
         {size * word_size - word_size, ZERO},
         {size * word_size - word_size, size * word_size - word_size},
         {size * word_size - word_size, 513},
         {size * word_size - word_size, 513, 1},
         {size * word_size - word_size},
         {size * word_size - word_size, ZERO},
         {size * word_size - word_size, size * word_size - word_size},
         {size * word_size - word_size, 1},
         {size * word_size - word_size + 1},
         {2},
         {2, size * word_size - 1},
         {},
         {size * word_size - word_size},
         {((UWORD)0x02 << (word_bit - CHAR_BIT)) | 0x0201},
         {((UWORD)0x02 << (word_bit - CHAR_BIT)) | 0x0201, 1},
         {},
         {ZERO},
         {},
         {ZERO},
         {ZERO, 1},
         {},
         {ZERO},
         {},
         {ZERO},
         {ZERO, 1},
         {},
        };

    int exception = 0;

    state *S = init_default_stacks(size);

    ass_action(S, O_PUSH_MEMORY); ass_number(S, word_size); ass_action(S, O_NEGATE); ass_action(S, O_ADD);
    ass_number(S, 513); ass_number(S, 1); ass_action(S, O_PUSH); ass_action(S, O_STORE); ass_number(S, 0); ass_action(S, O_PUSH);
    ass_action(S, O_LOAD); ass_number(S, 1); ass_action(S, O_POP); ass_number(S, 0); ass_action(S, O_PUSH); ass_action(S, O_LOADB);
    ass_action(S, O_ADD); ass_action(S, O_LOADB); ass_number(S, size * word_size - 1); ass_action(S, O_STOREB);
    ass_number(S, size * word_size - word_size); ass_action(S, O_LOAD); ass_number(S, 1); ass_action(S, O_POP); ass_action(S, O_PUSH_SDEPTH);
    ass_action(S, O_STORE_SDEPTH); ass_action(S, O_PUSH_RDEPTH); ass_number(S, 1); ass_action(S, O_POP); ass_number(S, 0);
    ass_action(S, O_STORE_RDEPTH); ass_action(S, O_PUSH_RDEPTH); ass_number(S, 1); ass_action(S, O_POP);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in memory tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    destroy(S);

    assert(exception == 0);
    printf("Memory tests ran OK\n");
    return 0;
}
