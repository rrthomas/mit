Option('trace',
       'write dynamic instruction trace to FILE',
       arg='required_argument',
       arg_name='FILE',
       top_level_code='''\
#include <stdio.h>

FILE *trace_fp = NULL;
static smite_WORD trace_run(smite_state *state)
{
    int ret = 0;
    do {
        fprintf(trace_fp, "%d\\n", (int)(state->I & SMITE_INSTRUCTION_MASK));
        ret = smite_single_step(state);
    } while (ret == 0);
    return ret;
}''',
       init_code='''\
{
    trace_fp = fopen(optarg, "wb");
    run_fn = trace_run;
    if (trace_fp == NULL)
        die("cannot not open file %s", optarg);
    warn("trace will be written to %s\\n", optarg);
}
''')
