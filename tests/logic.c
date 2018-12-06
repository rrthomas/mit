// Test the logic operators. We only test the stack handling and basic
// correctness of the operators here, assuming that if the logic works in
// one case, it will work in all (if the C compiler doesn't implement it
// correctly, we're in trouble anyway!).
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
    "-16777216 8 255 8", "-16777216 8 65280", "-16777216 8", "16711680",
    "16711680 65280","16776960",
    "-16776961", "-16776961 1", "-16776961 1 -1", "-16776961 -2", "-16776962"};


int main(void)
{
    int exception = 0;

    init((WORD *)malloc(1024), 256);

    PUSH(0xff000000); PUSH(8); PUSH(0xff); PUSH(8);

    start_ass(PC);
    ass_action(O_LSHIFT); ass_action(O_POP2R); ass_action(O_RSHIFT); ass_action(O_RPOP);
    ass_action(O_OR); ass_action(O_INVERT); ass_number(1);
    ass_number(-1);
    ass_action(O_XOR); ass_action(O_AND);

    for (size_t i = 0; i < sizeof(correct) / sizeof(correct[0]); i++) {
        show_data_stack();
        printf("Correct stack: %s\n\n", correct[i]);
        if (strcmp(correct[i], val_data_stack())) {
            printf("Error in logic tests: PC = %"PRIu32"\n", PC);
            exit(1);
        }
        single_step();
        printf("I = %s\n", disass(INSTRUCTION_ACTION, I));
    }

    assert(exception == 0);
    printf("Logic tests ran OK\n");
    return 0;
}
