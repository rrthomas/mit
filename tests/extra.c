// Test EXTRA instruction. Also uses previously-tested instructions.
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

    state * S = init_alloc(1024);
    assert(register_args(S, argc, argv) == 0);

    ass_number(S, OX_ARGC); ass_action(S, O_EXTRA);
    ass_number(S, 1); ass_number(S, OX_ARG); ass_action(S, O_EXTRA);

    do {
        single_step(S);
    } while (S->I != O_EXTRA);
    printf("argc is %"PRI_WORD", and should be %d\n\n", LOAD_WORD(S->SP), argc);
    if (POP != argc) {
       printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    do {
        single_step(S);
    } while (S->I != O_EXTRA);
    printf("arg 1's length is %"PRI_WORD", and should be %zu\n", LOAD_WORD(S->SP), strlen(argv[1]));
    if ((UWORD)POP != strlen(argv[1])) {
        printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    free(S->memory);
    destroy(S);
    for (int i = 0; i < argc; i++)
        free(argv[i]);

    assert(exception == 0);
    printf("Extra instructions tests ran OK\n");
    return 0;
}
