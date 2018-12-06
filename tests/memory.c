// Test the memory operators. Also uses previously tested instructions.
// See exceptions.c for address exception handling tests.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


const char *correct[] = {
    "", "16384", "16384 " str(WORD_W), "16384 -" str(WORD_W), "16380", "16380 513", "16380 513 1", "16380 513 16380",
    "16380", "16380 0", "16380 16380", "16380 513", "16380 513 1",
    "16380", "16380 0", "16380 16380", "16380 1", "16381", "2", "2 16383", "",
    "16380", "33554945", "33554945 1", "", "-33554432", "", "-16777216", "-16777216 1", "",
    "0", "", "0", "0 1", "", "16384", "67305985", "67305985 1", "",
    "16389", "2", "2 1", "", "1", "1 16385", "", "16385", "1", "1 1", "",
    "16392", "16392 0", "16392 16392", "-20",
};

const unsigned area[] = {0x4000, 0x4004, 0x4005, 0x4008};


int main(void)
{
    int exception = 0;

    // Data for extra memory area tests
    char *onetwothreefour = strdup("\x01\x02\x03\x04"); // Hold on to this to prevent a memory leak
    char *item[] = {onetwothreefour, strdup("\x01"), strdup("\x02\x03"), strdup("basilisk")};
    unsigned nitems = sizeof(item) / sizeof(item[0]);

    size_t size = 4096;
    init((WORD *)calloc(size, WORD_W), size);
    for (unsigned i = 0; i < nitems; i++) {
        UWORD addr = mem_allot(item[i], strlen(item[i]), i < 3);
        printf("Extra memory area %u allocated at address %"PRIX32" (should be %"PRIX32")\n",
               i, addr, area[i]);
        if (addr != area[i]) {
            printf("Error in memory tests: incorrect address for memory allocation\n");
            exit(1);
        }
        if (i == 2)
            mem_align();
    }

    start_ass(PC);

    ass_action(O_PUSH_MEMORY); ass_number(WORD_W); ass_action(O_NEGATE); ass_action(O_ADD);
    ass_number(513); ass_number(1); ass_action(O_PUSH); ass_action(O_STORE); ass_number(0); ass_action(O_PUSH);
    ass_action(O_LOAD); ass_number(1); ass_action(O_POP); ass_number(0); ass_action(O_PUSH); ass_action(O_LOADB);
    ass_action(O_ADD); ass_action(O_LOADB); ass_number(16383); ass_action(O_STOREB);
    ass_number(16380); ass_action(O_LOAD); ass_number(1); ass_action(O_POP); ass_action(O_PUSH_SP);
    ass_action(O_STORE_SP); ass_action(O_PUSH_RP); ass_number(1); ass_action(O_POP); ass_number(0);
    ass_action(O_STORE_RP); ass_action(O_PUSH_RP); ass_number(1); ass_action(O_POP);
    ass_number(size * WORD_W); ass_action(O_LOAD); ass_number(1); ass_action(O_POP);
    ass_number(size * WORD_W + 5); ass_action(O_LOADB); ass_number(1); ass_action(O_POP);
    ass_number(1);
    ass_number(size * WORD_W + 1); ass_action(O_STOREB);
    ass_number(size * WORD_W + 1); ass_action(O_LOADB); ass_number(1); ass_action(O_POP);
    ass_number(size * WORD_W + 8); ass_number(0); ass_action(O_PUSH); ass_action(O_STOREB);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in memory tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    assert(exception == 0);
    printf("Memory tests ran OK\n");
    return 0;
}
