# Code generation functions.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from code_util import Code, unrestrict, disable_warnings, c_symbol
from stack import StackEffect, Size, type_words


def declare_vars(stack_effect):
    '''
    Returns a Code to declare C variables for arguments and results other
    than 'ITEMS'.
     - stack_effect - StackEffect
    '''
    return Code(*[
        f'{item.type} {item.name};'
        for item in stack_effect.by_name.values()
        if item.name != 'ITEMS'
    ])

def load_args(stack_effect):
    '''
    Returns a Code to read the arguments from the stack into C variables,
    skipping 'ITEMS' and 'COUNT'.
     - stack_effect - StackEffect

    `stack_depth` is not modified.
    '''
    code = Code()
    for item in stack_effect.args.items:
        if item.name != 'ITEMS' and item.name != 'COUNT':
            code.extend(load_item(item))
    return code

def store_results(stack_effect):
    '''
    Returns a Code to write the results from C variables into the stack,
    skipping 'ITEMS'.
     - stack_effect - StackEffect

    `stack_depth` must be modified first.
    '''
    code = Code()
    for item in stack_effect.results.items:
        if item.name != 'ITEMS':
            code.extend(store_item(item))
    return code

def check_underflow(num_pops):
    '''
    Returns a Code to check that the stack contains enough items to
    pop the specified number of items.
     - num_pops - Size, with non-negative `count`.
    '''
    assert isinstance(num_pops, Size)
    assert num_pops >= 0, num_pops
    if num_pops == 0: return Code()
    tests = []
    tests.append(f'unlikely(stack_depth < (mit_uword_t)({num_pops.size}))')
    if num_pops.count == 1:
        tests.append(
            f'unlikely(stack_depth - (mit_uword_t)({num_pops.size}) < (mit_uword_t)(COUNT))'
        )
    return Code(
        'if ({}) {{'.format(' || '.join(tests)),
        Code('THROW(MIT_ERROR_INVALID_STACK_READ);'),
        '}',
    )

def check_overflow(num_pops, num_pushes):
    '''
    Returns a Code to check that the stack contains enough space to
    push `num_pushes` items, given that `num_pops` items will first be
    popped successfully.
     - num_pops - Size.
     - num_pushes - Size.
    `num_pops` and `num_pushes` must both be variadic or both not.
    '''
    assert isinstance(num_pops, Size)
    assert isinstance(num_pushes, Size)
    assert num_pops >= 0
    assert num_pushes >= 0
    depth_change = num_pushes - num_pops
    if depth_change <= 0: return Code()
    # Ensure comparison will not overflow
    assert depth_change.count == 0
    return Code(f'''\
        if (unlikely(stack_words - stack_depth < {depth_change}))
            THROW(MIT_ERROR_STACK_OVERFLOW);'''
    )

def load_stack(name, depth=0, type='mit_word_t'):
    '''
    Generate C code to load the variable `name` of type `type` occupying
    stack slots `depth`, `depth+1`, ... . Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.append(
        f'mit_max_stack_item_t temp = (mit_uword_t)(*mit_stack_pos(stack, stack_depth, {depth}));'
    )
    for i in range(1, type_words(type)):
        code.append('temp <<= MIT_WORD_BIT;')
        code.append(
            f'temp |= (mit_uword_t)(*mit_stack_pos(stack, stack_depth, {depth + i}));'
        )
    code.extend(disable_warnings(
        ['-Wint-to-pointer-cast'],
        Code(f'{name} = ({type})temp;'),
    ))
    return Code('{', code, '}')

def store_stack(value, depth=0, type='mit_word_t'):
    '''
    Generate C code to store the value `value` of type `type` occupying
    stack slots `depth`, `depth+1`, ... . Does not check the stack.

    Returns a Code.
    '''
    code = Code()
    code.extend(disable_warnings(
        ['-Wpointer-to-int-cast', '-Wbad-function-cast'],
        Code(f'mit_max_stack_item_t temp = (mit_max_stack_item_t){value};'),
    ))
    for i in reversed(range(1, type_words(type))):
        code.append(
            f'*mit_stack_pos(stack, stack_depth, {depth + i}) = (mit_uword_t)(temp & MIT_UWORD_MAX);'
        )
        code.append('temp >>= MIT_WORD_BIT;')
    code.append(
        '*mit_stack_pos(stack, stack_depth, {}) = (mit_uword_t)({});'
        .format(
            depth,
            'temp & MIT_UWORD_MAX' if type_words(type) > 1 else 'temp',
        )
    )
    return Code('{', code, '}')

def pop_stack(name, type='mit_word_t'):
    code = Code()
    code.extend(check_underflow(Size(type_words(type))))
    code.extend(load_stack(name, type=type))
    code.append(f'stack_depth -= {type_words(type)};')
    return code

def push_stack(value, type='mit_word_t'):
    code = Code()
    code.extend(check_overflow(Size(0), Size(type_words(type))))
    code.extend(store_stack(value, depth=-type_words(type), type=type))
    code.append(f'stack_depth += {type_words(type)};')
    return code

def load_item(item):
    '''
     - item - StackItem - returns a Code to load `item` from the stack to its
       C variable.
    '''
    return load_stack(item.name, item.depth, item.type)

def store_item(item):
    '''
     - item - StackItem - returns a Code to store `item` to the stack from its
       C variable.
    '''
    return store_stack(item.name, item.depth, item.type)

def gen_action_case(action):
    '''
    Generate a Code for an Action.

    In the code, errors are reported by calling THROW().
    '''
    effect = action.effect
    code = Code()
    if effect is not None:
        # Load the arguments into C variables.
        code.extend(declare_vars(effect))
        count = effect.args.by_name.get('COUNT')
        if count is not None:
            # If we have COUNT, check its stack position is valid, and load it.
            # We actually check `effect.args.size.size` (more than we need),
            # because this check will be generated anyway by the next
            # check_underflow call, so the compiler can elide one check.
            code.extend(check_underflow(Size(effect.args.size.size)))
            code.extend(load_item(count))
        code.extend(check_underflow(effect.args.size))
        code.extend(check_overflow(effect.args.size, effect.results.size))
        code.extend(load_args(effect))
    code.extend(action.code)
    if effect is not None:
        # Store the results from C variables.
        code.append(f'stack_depth += {effect.results.size - effect.args.size};')
        code.extend(store_results(effect))
    return code

def gen_instruction_case(instruction):
    code = gen_action_case(instruction.action)
    if instruction.terminal is not None:
        ir_all_bits = 0 if instruction.opcode & 0x80 == 0 else -1
        code = Code(
            f'if (ir != {ir_all_bits}) {{',
            gen_action_case(instruction.terminal),
            '} else {',
            code,
            '}',
        )
    return code

def dispatch(actions, undefined_case, opcode='opcode', gen_case=gen_action_case):
    '''
    Generate dispatch code for an ActionEnum.
     - actions - ActionEnum.
     - undefined_case - Code - the fallback behaviour.
     - opcode - str - a C expression for the opcode.
     - gen_case - function - a function to generate a C case from an element
       of `actions`.
    '''
    assert isinstance(undefined_case, Code), undefined_case
    code = Code()
    else_text = ''
    for (_, value) in enumerate(actions):
        opcode_symbol = f'{c_symbol(actions.__name__)}_{value.name}'
        code.append(
            f'{else_text}if ({opcode} == {opcode_symbol}) {{'
        )
        code.append(gen_case(value.action))
        code.append('}')
        else_text = 'else '
    code.append(f'{else_text}{{')
    code.append(undefined_case)
    code.append('}')
    return code

def run_body(instructions):
    '''
    Compute the instruction dispatch code for an inner run function.
    '''
    return dispatch(
        instructions,
        Code(
            '// Undefined instruction.',
            'THROW(MIT_ERROR_INVALID_OPCODE);'
        ),
        gen_case=gen_instruction_case,
    )

def run_inner_fn(instructions, suffix, instrument):
    '''
    Generate a `run_inner` function.

     - instructions - ActionEnum - instruction set.
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
                run_body(instructions),
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
