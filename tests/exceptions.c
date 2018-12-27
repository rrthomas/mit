// Test the VM-generated exceptions and HALT codes.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


#define SIZE 4096
WORD result[] = { -257, -257, 42, 0, -257, -10, -9, -9, -23, -256 };
// Values written 000 are overwritten later
UWORD badpc[] = { 000, 0, 0, 0, 000, 000, SIZE * WORD_SIZE, 000, 000, 000 };
UWORD address[] = { (UWORD)0xfffffff0 + WORD_SIZE, SIZE * WORD_SIZE, 0, 0, 5, 0, SIZE * WORD_SIZE, -24, 1, 0 };
int testno = 0;
UWORD test[sizeof(result) / sizeof(result[0])];


int main(void)
{
    int exception = 0;

    state *S = init_default(SIZE);

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 1: push stack value into non-existent memory
    ass_number(S, 0xfffffff0);
    ass_action(S, O_STORE_SP);
    badpc[testno] = ass_current(S);
    ass_number(S, 0);
    testno++;

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 2: set SP to MEMORY, then try to pop (>R) the stack
    ass_number(S, S->MEMORY);
    ass_action(S, O_STORE_SP);
    badpc[testno] = ass_current(S);
    ass_action(S, O_POP2R);
    testno++;

    test[testno++] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 3: test arbitrary throw code
    ass_number(S, 42); ass_action(S, O_HALT);

    test[testno++] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 4: test SP can point to just after a memory area
    ass_number(S, S->MEMORY);
    ass_number(S, WORD_SIZE);
    ass_action(S, O_NEGATE); ass_action(S, O_ADD);
    ass_action(S, O_STORE_SP); ass_action(S, O_POP2R); ass_number(S, 0); ass_action(S, O_HALT);

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 5: test unaligned SP is detected
    ass_number(S, 5); ass_action(S, O_STORE_SP);
    badpc[testno] = ass_current(S);
    ass_action(S, O_LOAD);
    testno++;

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 6
    ass_number(S, 1); ass_number(S, 0);
    badpc[testno] = ass_current(S);
    ass_action(S, O_DIVMOD); ass_number(S, 1);
    ass_action(S, O_POP);
    testno++;

    test[testno++] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 7: allow execution to run off the end of a memory area
    // (test 4 has set MEMORY - 1 to all zeroes)
    ass_number(S, S->MEMORY - 1);
    ass_action(S, O_BRANCH);

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 8: fetch from an invalid address
    ass_number(S, -24);
    badpc[testno] = ass_current(S);
    ass_action(S, O_LOAD);
    testno++;

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 9
    ass_number(S, 1);
    badpc[testno] = ass_current(S);
    ass_action(S, O_LOAD);
    testno++;

    test[testno] = ass_current(S);
    printf("Test %d: PC = %"PRI_UWORD"\n", testno, ass_current(S));
    // test 10: test invalid opcode
    badpc[testno] = ass_current(S);
    ass_action(S, O_UNDEFINED);
    testno++;

    start_ass(S, 200);
    ass_action(S, O_HALT);

    S->HANDLER = 200;   // set address of exception handler

    UWORD error = 0;
    for (size_t i = 0; i < sizeof(test) / sizeof(test[0]); i++) {
        S->SP = S->S0;    // reset stack pointer

        printf("Test %zu\n", i + 1);
        S->PC = test[i];
        S->BADPC = S->INVALID = 0;
        WORD res = run(S);

        if (result[i] != res || (result[i] != 0 && badpc[i] != S->BADPC) ||
            ((result[i] <= -257 || result[i] == -9 || result[i] == -23) &&
             address[i] != S->INVALID)) {
             printf("Error in exceptions tests: test %zu failed; PC = %"PRI_UWORD"\n", i + 1, S->PC);
             printf("Return code is %"PRI_WORD"; should be %"PRI_WORD"\n", res, result[i]);
             if (result[i] != 0)
                 printf("BADPC = %"PRI_UWORD"; should be %"PRI_UWORD"\n", S->BADPC, badpc[i]);
             if (result[i] <= -257 || result[i] == -9 || result[i] == -23)
                 printf("INVALID = %"PRI_XWORD"; should be %"PRI_XWORD"\n", S->INVALID, address[i]);
             error++;
        }
        putchar('\n');
    }

    destroy(S);

    assert(exception == 0);
    if (error == 0)
        printf("Exceptions tests ran OK\n");
    return error;
}
