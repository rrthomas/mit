Option('trace',
       'write dynamic instruction trace to FILE',
       arg='required_argument',
       arg_name='FILE',
       top_level_code='''\
#include <stdio.h>

FILE *trace_fp = NULL;
static mit_WORD trace_run(mit_state *state)
{
    int ret = 0;
    do {
        fprintf(trace_fp, "%d\\n", (int)(state->I & MIT_INSTRUCTION_MASK));
        ret = mit_single_step(state);
    } while (ret == 0);
    return ret;
}''',
       parse_code='''\
{
    trace_fp = fopen(optarg, "wb");
    run_fn = trace_run;
    if (trace_fp == NULL)
        die("cannot not open file %s", optarg);
    warn("trace will be written to %s\\n", optarg);
}
''')
