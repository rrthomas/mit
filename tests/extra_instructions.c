// Test extra instructions. Also uses previously-tested instructions.
// FIXME: test file routines.
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
    int exception = 0;
    WORD temp = 0;

    // Data for ARGC/ARG tests
    int argc = 3;
    char *argv[] = {strdup("foo"), strdup("bard"), strdup("basilisk")};

    init((WORD *)malloc(4096), 1024);
    assert(register_args(argc, argv) == 0);

    start_ass(PC);
    ass_number(OX_ARGC); ass_action(O_EXTRA);
    ass_number(1); ass_number(OX_ARG); ass_action(O_EXTRA);

    do {
        single_step();
    } while (I != O_EXTRA);
    printf("argc is %"PRId32", and should be %d\n\n", LOAD_WORD(SP), argc);
    if (POP != argc) {
       printf("Error in extra instructions tests: PC = %"PRIu32"\n", PC);
        exit(1);
    }

    do {
        single_step();
    } while (I != O_EXTRA);
    printf("arg 1's length is %"PRId32", and should be %zu\n", LOAD_WORD(SP), strlen(argv[1]));
    if ((UWORD)POP != strlen(argv[1])) {
        printf("Error in extra instructions tests: PC = %"PRIu32"\n", PC);
        exit(1);
    }

    printf("Extra instructions tests ran OK\n");
    return 0;
}
