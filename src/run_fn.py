# Generate the body of `run_inner()` functions.
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

     - error - str - expression for error code to return, needed when the
       code is compiled into a `mit_fn`. `run_inner` functions have no
       return value.
    '''
    return Instructions.dispatch(Code(
        '// Undefined instruction.',
        'THROW(MIT_ERROR_INVALID_OPCODE);'
    ))

def run_inner_fn(name, instrument):
    '''
    Generate a `run_inner` function.

     - suffix - str - the function is named `mit_run_{name}` and will call
       an inner function `run_inner_{name}`.
     - instrument - Code or str - instrumentation to insert at end of main
       loop.
    '''
    return disable_warnings(
        ['-Wstack-protector'], # TODO: Stack protection cannot cope with VLAs.
        Code(f'''
        #define run_inner run_inner_{name}
        static void run_inner_{name}(mit_word_t *pc, mit_word_t ir, mit_word_t * restrict stack, mit_uword_t * restrict stack_depth_ptr, jmp_buf *jmp_buf_ptr)
        {{
            #define stack_depth (*stack_depth_ptr)
            mit_uword_t stack_words = mit_stack_words;''',
        Code(*['''\
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
            Code('continue;'),
            '''}

            error:
            THROW_LONGJMP(error);'''
        ]),
        '''\
        #undef stack_depth
        }
        #undef run_inner''',
    ))

def run_fn(name):
    '''
    Generate a `mit_run`-like function.

     - suffix - str - the function is named `mit_run_{name}` and will call
       an inner function `run_inner_{name}`.
    '''
    return Code(f'''
        #define run_inner run_inner_{name}
        mit_word_t mit_run_{name}(mit_word_t *pc, mit_word_t ir, mit_word_t * restrict stack, mit_uword_t *stack_depth_ptr)
        {{
            jmp_buf env;
            mit_word_t error = (mit_word_t)setjmp(env);
            if (error == 0) {{
                run_inner(pc, ir, stack, stack_depth_ptr, &env);
                error = MIT_ERROR_OK;
            }} else if (error == MIT_ERROR_BREAK)
                // Translate MIT_ERROR_BREAK as 0; see THROW_LONGJMP in run.h.
                error = 0;
            return error;
        }}
        #undef run_inner
        ''',
    )
