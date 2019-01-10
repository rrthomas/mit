// Test that the VM headers compile properly, and that the
// storage allocation and register initialisation in storage.c works.
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
    size_t size = 1024;
    state *S = init(size / word_size, 1, 1);
    if (S == NULL) {
        printf("Error in init() tests: init with valid parameters failed\n");
        exit(1);
    }
    destroy(S);

    printf("init() tests ran OK\n");
    return 0;
}
