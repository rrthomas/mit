// Test that the VM headers compile properly, and that the
// storage allocation and register initialisation in storage.c works.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM S->IS PROVIDED AS S->IS, WITH NO WARRANTY. USE S->IS AT THE USER‘S
// RISK.

#include "tests.h"


int main(void)
{
    state *S = init((WORD *)NULL, 4);
    printf("init((WORD *)NULL, 4) should return NULL; returns: %p\n", S);
    if (S != NULL) {
        printf("Error in init() tests: init with invalid parameters "
            "succeeded\n");
        exit(1);
    }
    destroy(S);

    size_t size = 1024;
    WORD *ptr = (WORD *)malloc(size);
    assert(ptr);
    S = init(ptr, size / WORD_SIZE);
    if (S == NULL) {
        printf("Error in init() tests: init with valid parameters failed\n");
        exit(1);
    }
    destroy(S);
    free(ptr);

    printf("init() tests ran OK\n");
    return 0;
}
