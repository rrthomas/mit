# Generate the body of `run_inner()` and `run()` functions.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from spec import Instructions
from code_util import Code, disable_warnings


def run_body():
    '''
    Compute the instruction dispatch code for an inner run function.
    '''
    return Instructions.dispatch(Code(
        '// Undefined instruction.',
        'THROW(MIT_ERROR_INVALID_OPCODE);'
    ))

def run_inner_fn(suffix, instrument):
    '''
    Generate a `run_inner` function.

     - suffix - str - the function is named `run_inner_{suffix}`.
     - instrument - Code or str - instrumentation to insert at start of main
       loop.
    '''
    return disable_warnings(
        ['-Wstack-protector', '-Wvla-larger-than='], # TODO: Stack protection cannot cope with VLAs.
        Code(
            f'''\
            // Define run_inner for the benefit of `call`.
            #define run_inner run_inner_{suffix}
            static void run_inner_{suffix}(mit_word_t *pc, mit_word_t ir, mit_word_t * restrict stack, mit_uword_t stack_words, mit_uword_t * restrict stack_depth_ptr, jmp_buf *jmp_buf_ptr)
            {{''',
            Code(*[
                '''\
                #define stack_depth (*stack_depth_ptr)
                mit_word_t error;

                for (;;) {''',
                instrument,
                Code('''\
                    uint8_t opcode = (uint8_t)ir;
                    ir = ARSHIFT(ir, 8);

                    // Check stack_depth is valid
                    if (stack_depth > stack_words)
                        THROW(MIT_ERROR_STACK_OVERFLOW);'''
                ),
                run_body(),
                '''\
                #undef stack_depth
                }''',
            ]),
            '''\
            error:
                THROW_LONGJMP(error);
            }
            #undef run_inner''',
        )
    )

def run_fn(suffix):
    '''
    Generate a `mit_run`-like function.

     - suffix - str - the function is named `mit_run_{suffix}` and will call
       an inner function `run_inner_{suffix}`.
    '''
    return Code(f'''
        mit_word_t mit_run_{suffix}(mit_word_t *pc, mit_word_t ir, mit_word_t * restrict stack, mit_uword_t stack_words, mit_uword_t *stack_depth_ptr)
        {{
            jmp_buf env;
            mit_word_t error = (mit_word_t)setjmp(env);
            if (error == 0) {{
                run_inner_{suffix}(pc, ir, stack, stack_words, stack_depth_ptr, &env);
                error = MIT_ERROR_OK;
            }} else if (error == MIT_ERROR_OK_LONGJMP) // see THROW_LONGJMP in run.h.in
                error = 0;
            return error;
        }}
        ''',
    )
