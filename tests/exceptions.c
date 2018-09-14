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


CELL result[] = { -257, -257, 42, 0, -23, -23, -10, -9, -9, -23, -256, -258 };
UCELL bad[] = { -1, -1, -1, 28, 56, 64, 76, 16388, 92, 100, 104, 112 };
UCELL address[] = { -16, 16384, 0, 0, 5, 1, 0, 16384, -20, 1, 0, 1 };
int testno = 0;
UCELL test[sizeof(result) / sizeof(result[0])];


int main(void)
{
    int exception = 0;

    size_t size = 4096;
    init((CELL *)calloc(size, CELL_W), size);

    start_ass(0);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 1: DUP into non-existent memory
    ass(O_LITERAL); ass(O_NEXT00); ass(O_NEXT00); ass(O_NEXT00);
    lit(0xfffffff0);
    ass(O_SPSTORE); ass(O_DUP); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 2: set SP to MEMORY, then try to pop (>R) the stack
    ass(O_LITERAL); lit(MEMORY);
    ass(O_SPSTORE); ass(O_TOR); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 3: test arbitrary throw code
    ass(O_LITERAL); lit(42);
    ass(O_HALT); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 4: test SP can point to just after a memory area
    ass(O_LITERAL); lit(MEMORY);
    ass(O_LITERAL); lit(CELL_W);
    ass(O_NEGATE); ass(O_PLUS);
    ass(O_SPSTORE); ass(O_TOR); ass(O_LITERAL); lit(0); ass(O_HALT);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 5
    ass(O_LITERAL); lit(5);
    ass(O_SPSTORE); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 6
    ass(O_LITERAL); lit(1); ass(O_EXECUTE); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 7
    ass(O_LITERAL); lit(1);
    ass(O_LITERAL); lit(0);
    ass(O_SREMSLASH); ass(O_DROP);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 8: allow execution to run off the end of a memory area
    ass(O_LITERAL); lit(MEMORY - CELL_W);
    ass(O_EPSTORE); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 9: fetch from an invalid address
    ass(O_LITERAL); lit(0xffffffec);
    ass(O_FETCH); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 10
    ass(O_LITERAL); lit(1);
    ass(O_FETCH); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 11: test invalid opcode
    ass(O_UNDEFINED); ass(O_NEXT00); ass(O_NEXT00); ass(O_NEXT00);

    test[testno++] = ass_current();
    fprintf(stderr, "Test %d: EP = %u\n", testno, ass_current());
    // test 12: test invalid 'THROW contents
    ass(O_LITERAL); lit(0xffffffec);
    ass(O_DUP); ass(O_THROWSTORE); ass(O_THROW);

    start_ass(200);
    ass(O_HALT);

    THROW = 200;   // set address of exception handler

    UCELL error = 0;
    for (size_t i = 0; i < sizeof(test) / sizeof(test[0]); i++) {
        SP = S0;    // reset stack pointer

        printf("Test %zu\n", i + 1);
        EP = test[i];
        assert(single_step() == -259);   // load first instruction word
        CELL res = run();

        if (result[i] != res || (result[i] != 0 && bad[i] != BAD) ||
            ((result[i] <= -257 || result[i] == -9 || result[i] == -23) &&
             address[i] != NOT_ADDRESS)) {
             printf("Error in exceptions tests: test %zu failed; EP = %"PRIu32"\n", i + 1, EP);
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
