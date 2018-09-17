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


WORD result[] = { -257, -257, 42, 0, -23, -23, -10, -9, -9, -23, -256, -258 };
UWORD bad[] = { -1, -1, -1, 28, 60, 68, 80, 16388, 104, 112, 116, 132 };
UWORD address[] = { -12, 16384, 0, 0, 5, 1, 0, 16384, -20, 1, 0, 1 };
int testno = 0;
UWORD test[sizeof(result) / sizeof(result[0])];


int main(void)
{
    int exception = 0;

    size_t size = 4096;
    init((WORD *)calloc(size, WORD_W), size);

    start_ass(0);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 1: push stack value into non-existent memory
    ass(O_LITERAL); ass(O_NEXT00); ass(O_NEXT00); ass(O_NEXT00);
    lit(0xfffffff0);
    ass(O_STORE_SP); ass(O_LITERAL); lit(0); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 2: set SP to MEMORY, then try to pop (>R) the stack
    ass(O_LITERAL); lit(MEMORY);
    ass(O_STORE_SP); ass(O_POP2R); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 3: test arbitrary throw code
    ass(O_LITERAL); lit(42);
    ass(O_HALT); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 4: test SP can point to just after a memory area
    ass(O_LITERAL); lit(MEMORY);
    ass(O_LITERAL); lit(WORD_W);
    ass(O_NEGATE); ass(O_ADD);
    ass(O_STORE_SP); ass(O_POP2R); ass(O_LITERAL); lit(0); ass(O_HALT);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 5
    ass(O_LITERAL); lit(5);
    ass(O_STORE_SP); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 6
    ass(O_LITERAL); lit(1); ass(O_CALL); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 7
    ass(O_LITERAL); lit(1);
    ass(O_LITERAL); lit(0);
    ass(O_DIVMOD); ass(O_LITERAL); lit(1);
    ass(O_POP); ass(O_NEXT00); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 8: allow execution to run off the end of a memory area
    ass(O_LITERAL); lit(MEMORY - WORD_W);
    ass(O_BRANCH); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 9: fetch from an invalid address
    ass(O_LITERAL); lit(0xffffffec);
    ass(O_LOAD); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 10
    ass(O_LITERAL); lit(1);
    ass(O_LOAD); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 11: test invalid opcode
    ass(O_UNDEFINED); ass(O_NEXT00); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: PC = %u\n", testno, ass_current());
    // test 12: test invalid 'THROW contents
    ass(O_LITERAL); lit(0xffffffec);
    ass(O_LITERAL); lit(0); ass(O_PUSH); ass(O_STORE_HANDLER); ass(O_THROW);

    start_ass(200);
    ass(O_HALT);

    THROW = 200;   // set address of exception handler

    UWORD error = 0;
    for (size_t i = 0; i < sizeof(test) / sizeof(test[0]); i++) {
        SP = S0;    // reset stack pointer

        printf("Test %zu\n", i + 1);
        PC = test[i];
        assert(single_step() == -259);   // load first instruction word
        WORD res = run();

        if (result[i] != res || (result[i] != 0 && bad[i] != BAD) ||
            ((result[i] <= -257 || result[i] == -9 || result[i] == -23) &&
             address[i] != NOT_ADDRESS)) {
             printf("Error in exceptions tests: test %zu failed; PC = %"PRIu32"\n", i + 1, PC);
             printf("Return code is %d; should be %d\n", res, result[i]);
             if (result[i] != 0)
                 printf("'BAD = %"PRIu32"; should be %"PRIu32"\n", BAD, bad[i]);
             if (result[i] <= -257 || result[i] == -9 || result[i] == -23)
                 printf("-ADDRESS = %"PRIX32"; should be %"PRIX32"\n", NOT_ADDRESS, address[i]);
             error++;
        }
        putchar('\n');
    }

    assert(exception == 0);
    if (error == 0)
        printf("Exceptions tests ran OK\n");
    return error;
}
