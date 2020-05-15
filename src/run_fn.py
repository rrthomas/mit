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


def run_body(error=''):
    '''
    Compute the instruction dispatch code for an inner run function.

     - error - str - expression for error code to return, needed when the
       code is compiled into a `mit_fn`. `run_inner` functions have no
       return value.
    '''
    return Code(
        Code(f'#define RET_ERROR {error}'),
        Instructions.dispatch(Code(
            '// Undefined instruction.',
            'RAISE(MIT_ERROR_INVALID_OPCODE);'
        )),
        Code(f'#undef RET_ERROR'),
    )

def run_inner_fn(name, instrument):
    '''
    Generate a `run_inner` function.

     - suffix - str - the function is named `mit_run_{name}` and will call
       an inner function `run_inner_{name}`.
     - instrument - Code or str - instrumentation to insert at end of main
       loop.
    '''
    return disable_warnings(
        ['-Wstack-protector'], # Stack protection cannot cope with VLAs.
        Code(f'''
        #define run_inner run_inner_{name}
        static void run_inner_{name}(mit_word *pc, mit_word ir, mit_word *outer_stack, mit_uword nargs, mit_uword nres, jmp_buf *jmp_buf_ptr)
        {{''',
            Code(*['''\
            mit_word error;
            mit_word stack[mit_stack_words];
            if (outer_stack != NULL)
                memcpy(stack, outer_stack, nargs * MIT_WORD_BYTES);
            mit_uword stack_depth = nargs;

            for (;;) {''',
            Code('''\
                mit_byte opcode = ir & MIT_OPCODE_MASK;
                ir = ARSHIFT(ir, MIT_OPCODE_BIT);

                // Check stack_depth is valid
                if (stack_depth > mit_stack_words)
                    RAISE(MIT_ERROR_STACK_OVERFLOW);'''
            ),
            run_body(),
            instrument,
            Code('''\
            continue;
            '''),
            '''\
            }

            error:
            // We mustn't return 0 with longjmp(), or the caller of setjmp will assume
            // it has just executed setjmp, not longjmp. MIT_ERROR_BREAK cannot be
            // returned by `mit_run()`, so use it to stand in for 0.
            if (error == 0)
                error = MIT_ERROR_BREAK;
            longjmp(*jmp_buf_ptr, error);''',
            ]),
        '}',
        '#undef run_inner',
    ))

def run_fn(name):
    '''
    Generate a `mit_run`-like function.

     - suffix - str - the function is named `mit_run_{name}` and will call
       an inner function `run_inner_{name}`.
    '''
    return Code(f'''
        #define run_inner run_inner_{name}
        mit_word mit_run_{name}(mit_word *pc)
        {{
            jmp_buf env;
            mit_word error = (mit_word)setjmp(env);
            if (error == 0) {{
                run_inner(pc, 0, NULL, 0, 0, &env);
                error = MIT_ERROR_OK;
            }} else if (error == MIT_ERROR_BREAK)
                // Translate MIT_ERROR_BREAK as 0.
                error = 0;
            return error;
        }}
        #undef run_inner
        ''',
    )
    return code
