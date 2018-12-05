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


WORD result[] = { -257, -257, 42, 0, -23, -10, -9, -9, -23, -256 };
UWORD badpc[] = { 0, 0, 0, 0, 21, 24, 16384, 32, 34, 35 };
UWORD address[] = { -12, 16384, 0, 0, 5, 0, 16384, -20, 1, 0 };
int testno = 0;
UWORD test[sizeof(result) / sizeof(result[0])];


int main(void)
{
    int exception = 0;

    size_t size = 4096;
    init((WORD *)calloc(size, WORD_W), size);

    start_ass(0);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 1: push stack value into non-existent memory
    lit(0xfffffff0);
    ass(O_STORE_SP); lit(0);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 2: set SP to MEMORY, then try to pop (>R) the stack
    lit(MEMORY);
    ass(O_STORE_SP); ass(O_POP2R);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 3: test arbitrary throw code
    lit(42); ass(O_HALT);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 4: test SP can point to just after a memory area
    lit(MEMORY);
    lit(WORD_W);
    ass(O_NEGATE); ass(O_ADD);
    ass(O_STORE_SP); ass(O_POP2R); lit(0); ass(O_HALT);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 5
    lit(5); ass(O_STORE_SP);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 6
    lit(1); lit(0); ass(O_DIVMOD); lit(1);
    ass(O_POP);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 7: allow execution to run off the end of a memory area
    // (test 4 has set MEMORY - 1 to all zeroes)
    lit(MEMORY - 1);
    ass(O_BRANCH);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 8: fetch from an invalid address
    lit(0xffffffec); ass(O_LOAD);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 9
    lit(1); ass(O_LOAD);

    test[testno++] = ass_current();
    printf("Test %d: PC = %u\n", testno, ass_current());
    // test 10: test invalid opcode
    ass(O_UNDEFINED);

    start_ass(200);
    ass(O_HALT);

    HANDLER = 200;   // set address of exception handler

    UWORD error = 0;
    for (size_t i = 0; i < sizeof(test) / sizeof(test[0]); i++) {
        SP = S0;    // reset stack pointer

        printf("Test %zu\n", i + 1);
        PC = test[i];
        WORD res = run();

        if (result[i] != res || (result[i] != 0 && badpc[i] != BADPC) ||
            ((result[i] <= -257 || result[i] == -9 || result[i] == -23) &&
             address[i] != INVALID)) {
             printf("Error in exceptions tests: test %zu failed; PC = %"PRIu32"\n", i + 1, PC);
             printf("Return code is %d; should be %d\n", res, result[i]);
             if (result[i] != 0)
                 printf("BADPC = %"PRIu32"; should be %"PRIu32"\n", BADPC, badpc[i]);
             if (result[i] <= -257 || result[i] == -9 || result[i] == -23)
                 printf("INVALID = %"PRIX32"; should be %"PRIX32"\n", INVALID, address[i]);
             error++;
        }
        putchar('\n');
    }

    assert(exception == 0);
    if (error == 0)
        printf("Exceptions tests ran OK\n");
    return error;
}
