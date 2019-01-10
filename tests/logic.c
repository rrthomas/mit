// Test the logic operators. We only test the stack handling and basic
// correctness of the operators here, assuming that if the logic works in
// one case, it will work in all (if the C compiler doesn't implement it
// correctly, we're in trouble anyway!).
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
         {(UWORD)0xff << (word_bit - CHAR_BIT), CHAR_BIT, 0xff, CHAR_BIT},
         {(UWORD)0xff << (word_bit - CHAR_BIT), CHAR_BIT, 0xff << CHAR_BIT},
         {(UWORD)0xff << (word_bit - CHAR_BIT), CHAR_BIT},
         {(UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT},
         {(UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT, 0xff << CHAR_BIT},
         {((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT)},
         {~(((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT))},
         {~(((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT)), 1},
         {~(((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT)), 1, -1},
         {~(((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT)), -2},
         {~(((UWORD)0xff << (word_bit - CHAR_BIT) >> CHAR_BIT) | (0xff << CHAR_BIT)) & -2},
        };

    int exception = 0;

    state *S = init_default_stacks(256);

    PUSH((UWORD)0xff << (word_bit - CHAR_BIT)); PUSH(CHAR_BIT); PUSH(0xff); PUSH(CHAR_BIT);

    ass_action(S, O_LSHIFT); ass_action(S, O_POP2R); ass_action(S, O_RSHIFT); ass_action(S, O_RPOP);
    ass_action(S, O_OR); ass_action(S, O_INVERT); ass_number(S, 1);
    ass_number(S, -1);
    ass_action(S, O_XOR); ass_action(S, O_AND);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in logic tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        single_step(S);
        printf("I = %s\n", disass(S->ITYPE, S->I));
    }

    destroy(S);

    assert(exception == 0);
    printf("Logic tests ran OK\n");
    return 0;
}
