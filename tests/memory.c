// Test the memory operators. Also uses previously tested instructions.
// See exceptions.c for address exception handling tests.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM S->IS PROVIDED AS S->IS, WITH NO WARRANTY. USE S->IS AT THE USER‘S
// RISK.

#include "tests.h"


#define SIZE 4096

const WORD correct[][8] =
    {
     {},
     {SIZE * WORD_SIZE},
     {SIZE * WORD_SIZE, WORD_SIZE},
     {SIZE * WORD_SIZE, -WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE, 513},
     {SIZE * WORD_SIZE - WORD_SIZE, 513, 1},
     {SIZE * WORD_SIZE - WORD_SIZE, 513, SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE, ZERO},
     {SIZE * WORD_SIZE - WORD_SIZE, SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE, 513},
     {SIZE * WORD_SIZE - WORD_SIZE, 513, 1},
     {SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE, ZERO},
     {SIZE * WORD_SIZE - WORD_SIZE, SIZE * WORD_SIZE - WORD_SIZE},
     {SIZE * WORD_SIZE - WORD_SIZE, 1},
     {SIZE * WORD_SIZE - WORD_SIZE + 1},
     {2},
     {2, SIZE * WORD_SIZE - 1},
     {},
     {SIZE * WORD_SIZE - WORD_SIZE},
     {((UWORD)0x02 << (WORD_BIT - CHAR_BIT)) | 0x0201},
     {((UWORD)0x02 << (WORD_BIT - CHAR_BIT)) | 0x0201, 1},
     {},
     {(UWORD)DATA_STACK_SEGMENT},
     {},
     {(UWORD)RETURN_STACK_SEGMENT},
     {(UWORD)RETURN_STACK_SEGMENT, 1},
     {},
     {ZERO},
     {},
     {ZERO},
     {ZERO, 1},
     {},
     {SIZE * WORD_SIZE},
     {(UWORD)0x0807060504030201},
     {(UWORD)0x0807060504030201, 1},
     {},
     {SIZE * WORD_SIZE + WORD_SIZE + 1},
     {2},
     {2, 1},
     {},
     {1},
     {1, SIZE * WORD_SIZE + 1},
     {},
     {SIZE * WORD_SIZE + 1},
     {1},
     {1, 1},
     {},
     {SIZE * WORD_SIZE + 2 * WORD_SIZE},
     {SIZE * WORD_SIZE + 2 * WORD_SIZE, ZERO},
     {SIZE * WORD_SIZE + 2 * WORD_SIZE, SIZE * WORD_SIZE + 2 * WORD_SIZE},
     {-20},
    };

const unsigned area[] =
    {
     0x1000 * WORD_SIZE,
     0x1000 * WORD_SIZE + WORD_SIZE,
     0x1000 * WORD_SIZE + WORD_SIZE + 1,
     0x1000 * WORD_SIZE + ((WORD_SIZE + 1 + 3 + (WORD_SIZE - 1)) / WORD_SIZE) * WORD_SIZE,
    };


int main(void)
{
    int exception = 0;

    // Data for extra memory area tests
    verify(WORD_SIZE <= 8); // If not, a longer string is needed in the next line
    char *count = strdup("\x01\x02\x03\x04\x05\x06\x07\x08"); // Hold on to this to prevent a memory leak
    count[WORD_SIZE] = '\0'; // Truncate to WORD_SIZE
    char *item[] = {count, strdup("\x01"), strdup("\x02\x03"), strdup("basilisk")};
    unsigned nitems = sizeof(item) / sizeof(item[0]);

    state *S = init_alloc(SIZE);
    for (unsigned i = 0; i < nitems; i++) {
        UWORD addr = mem_allot(S, item[i], strlen(item[i]), i < 3);
        printf("Extra memory area %u allocated at address %"PRI_XWORD" (should be %x)\n",
               i, addr, area[i]);
        if (addr != area[i]) {
            printf("Error in memory tests: incorrect address for memory allocation\n");
            exit(1);
        }
        if (i == 2)
            mem_align(S);
    }

    ass_action(S, O_PUSH_MEMORY); ass_number(S, WORD_SIZE); ass_action(S, O_NEGATE); ass_action(S, O_ADD);
    ass_number(S, 513); ass_number(S, 1); ass_action(S, O_PUSH); ass_action(S, O_STORE); ass_number(S, 0); ass_action(S, O_PUSH);
    ass_action(S, O_LOAD); ass_number(S, 1); ass_action(S, O_POP); ass_number(S, 0); ass_action(S, O_PUSH); ass_action(S, O_LOADB);
    ass_action(S, O_ADD); ass_action(S, O_LOADB); ass_number(S, SIZE * WORD_SIZE - 1); ass_action(S, O_STOREB);
    ass_number(S, SIZE * WORD_SIZE - WORD_SIZE); ass_action(S, O_LOAD); ass_number(S, 1); ass_action(S, O_POP); ass_action(S, O_PUSH_SP);
    ass_action(S, O_STORE_SP); ass_action(S, O_PUSH_RP); ass_number(S, 1); ass_action(S, O_POP); ass_number(S, 0);
    ass_action(S, O_STORE_RP); ass_action(S, O_PUSH_RP); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, SIZE * WORD_SIZE); ass_action(S, O_LOAD); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, SIZE * WORD_SIZE + WORD_SIZE + 1); ass_action(S, O_LOADB); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, 1);
    ass_number(S, SIZE * WORD_SIZE + 1); ass_action(S, O_STOREB);
    ass_number(S, SIZE * WORD_SIZE + 1); ass_action(S, O_LOADB); ass_number(S, 1); ass_action(S, O_POP);
    ass_number(S, SIZE * WORD_SIZE + 2 * WORD_SIZE); ass_number(S, 0); ass_action(S, O_PUSH); ass_action(S, O_STOREB);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in memory tests: S->PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        single_step(S);
        printf("I = %s\n", disass(INSTRUCTION_ACTION, S->I));
    }

    free(S->memory);
    destroy(S);
    for (size_t i = 0; i < nitems; i++)
        free(item[i]);

    assert(exception == 0);
    printf("Memory tests ran OK\n");
    return 0;
}
