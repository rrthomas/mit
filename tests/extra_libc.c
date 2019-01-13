// Test libc EXTRA calls.
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


#define BUFFER 0x100


int main(void)
{
    int exception = 0;

    // Data for ARGC/ARG_LEN/ARG_COPY tests
    int argc = 3;
    char *argv[] = {strdup("foo"), strdup("bard"), strdup("basilisk")};

    state * S = init_default_stacks(1024);
    assert(register_args(S, argc, argv) == 0);

    ass_number(S, OX_ARGC); ass_number(S, OXLIB_LIBC); ass_action(S, O_EXTRA);
    ass_number(S, 1); ass_number(S, OX_ARG_LEN); ass_number(S, OXLIB_LIBC); ass_action(S, O_EXTRA);
    ass_number(S, 1); ass_number(S, BUFFER); ass_number(S, 16);
    ass_number(S, OX_ARG_COPY); ass_number(S, OXLIB_LIBC); ass_action(S, O_EXTRA);

    // Test 1: OX_ARGC
    do {
        single_step(S);
    } while (S->I != O_EXTRA);
    WORD argc_;
    load_stack(S, 0, &argc_);
    printf("argc is %"PRI_WORD", and should be %d\n", argc_, argc);
    WORD temp;
    POP(&temp);
    if (temp != argc) {
       printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    // Test 2: OX_ARG_LEN
    do {
        single_step(S);
    } while (S->I != O_EXTRA);
    UWORD arg1len;
    load_stack(S, 0, (WORD *)&arg1len);
    printf("arg 1's length is %"PRI_UWORD", and should be %zu\n", arg1len, strlen(argv[1]));
    if (arg1len != strlen(argv[1])) {
        printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    // Tests 3 & 4: OX_ARG_COPY
    do {
        single_step(S);
    } while (S->I != O_EXTRA);
    POP((WORD *)&arg1len);
    printf("arg 1's length is %"PRI_UWORD", and should be %zu\n", arg1len, strlen(argv[1]));
    if (arg1len != strlen(argv[1])) {
        printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }
    printf("arg 1 is %s, and should be %s\n", native_address_of_range(S, BUFFER, 0), argv[1]);
    if (strncmp((char *)native_address_of_range(S, BUFFER, 0), argv[1], strlen(argv[1])) != 0) {
        printf("Error in extra instructions tests: PC = %"PRI_UWORD"\n", S->PC);
        exit(1);
    }

    destroy(S);
    for (int i = 0; i < argc; i++)
        free(argv[i]);

    assert(exception == 0);
    printf("Extra instructions tests ran OK\n");
    return 0;
}
