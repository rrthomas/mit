// Test the comparison operators. We only test simple cases here, assuming
// that the C compiler's comparison routines will work for other cases.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


int exception = 0;
WORD temp;

const WORD correct[] = { 0, 1, 0, 1, 1, 0, 0, 1, 0, 0};


static void stack1(state *S)
{
    S->SP = S->S0;	// empty the stack

    PUSH(-4); PUSH(3);
    PUSH(2); PUSH(2);
    PUSH(1); PUSH(3);
    PUSH(3); PUSH(1);
}

static void stack2(state *S)
{
    S->SP = S->S0;	// empty the stack

    PUSH(1); PUSH(-1);
    PUSH(237); PUSH(237);
}

static void step(state *S, unsigned start, unsigned end)
{
    if (end > start)
        for (unsigned i = start; i < end; i++) {
            single_step(S);
            printf("I = %s\n", disass(S->ITYPE, S->I));
            printf("Result: %"PRI_WORD"; correct result: %"PRI_WORD"\n\n", LOAD_WORD(S->SP),
                   correct[i]);
            if (correct[i] != LOAD_WORD(S->SP)) {
                printf("Error in comparison tests: PC = %"PRI_UWORD"\n", S->PC);
                exit(1);
            }
            (void)POP;	// drop result of comparison
        }
}

int main(void)
{
    state *S = init_alloc(256);

    ass_action(S, O_LT); ass_action(S, O_LT); ass_action(S, O_LT); ass_action(S, O_LT);
    ass_action(S, O_EQ); ass_action(S, O_EQ);
    ass_action(S, O_ULT); ass_action(S, O_ULT); ass_action(S, O_ULT); ass_action(S, O_ULT);

    stack1(S);      // set up the stack with four standard pairs to compare
    step(S, 0, 4);  // do the < tests
    stack2(S);      // set up the stack with two standard pairs to compare
    step(S, 4, 6);  // do the = tests
    stack1(S);      // set up the stack with four standard pairs to compare
    step(S, 6, 10); // do the U< tests

    free(S->memory);
    destroy(S);

    assert(exception == 0);
    printf("Comparison tests ran OK\n");
    return 0;
}
