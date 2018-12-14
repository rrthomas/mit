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


const WORD correct[][8] =
    {
     {},
     {ZERO},
     {ZERO, 1},
     {ZERO, 1, WORD_SIZE},
     {ZERO, 1, WORD_SIZE, -WORD_SIZE},
     {ZERO, 1, WORD_SIZE, -WORD_SIZE, -1},
     {ZERO, 1, WORD_SIZE, -WORD_SIZE - 1},
     {ZERO, 1, -1},
     {ZERO, 1, 1},
     {ZERO, 2},
     {ZERO, 2, 1},
     {2, ZERO},
     {2, ZERO, -1},
     {2, ZERO, -1, WORD_SIZE},
     {2, ZERO, -WORD_SIZE},
     {2, ZERO, -WORD_SIZE, 1},
     {2, -WORD_SIZE, ZERO},
     {2, -WORD_SIZE, ZERO, 2},
     {2},
     {-2},
     {-2, -1},
     {2, ZERO},
     {2, ZERO, 1},
     {ZERO, 2},
     {ZERO, 2, 2},
     {},
     {WORD_SIZE},
     {-WORD_SIZE},
     {-WORD_SIZE, 1},
     {},
     {-WORD_SIZE},
     {-WORD_SIZE, WORD_SIZE - 1},
     {-1, -1},
     {-1, -1, 1},
     {-1},
     {-1, -2},
     {1, 1},
    };


int main(void)
{
    int exception = 0;

    init_alloc(256);

    ass_number(0);
    ass_number(1);
    ass_number(WORD_SIZE);
    ass_number(-WORD_SIZE);
    ass_number(-1);
    ass_action(O_ADD); ass_action(O_ADD); ass_action(O_NEGATE);
    ass_action(O_ADD); ass_number(1); ass_action(O_SWAP); ass_number(-1);
    ass_number(WORD_SIZE);
    ass_action(O_MUL); ass_number(1); ass_action(O_SWAP); ass_number(2); ass_action(O_POP);
    ass_action(O_NEGATE); ass_number(-1);
    ass_action(O_DIVMOD); ass_number(1); ass_action(O_SWAP); ass_number(2); ass_action(O_POP);
    ass_number(WORD_SIZE); ass_action(O_NEGATE); ass_number(1); ass_action(O_POP);
    ass_number(-WORD_SIZE);
    ass_number(WORD_SIZE - 1);
    ass_action(O_DIVMOD); ass_number(1); ass_action(O_POP); ass_number(-2);
    ass_action(O_UDIVMOD);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack())) {
            printf("Error in arithmetic tests: PC = %"PRI_UWORD"\n", PC);
            exit(1);
        }
        free(correct_stack);
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    assert(exception == 0);
    printf("Arithmetic tests ran OK\n");
    return 0;
}
