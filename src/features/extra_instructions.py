# External extra instructions.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique

from mit_core.code_util import Code
from mit_core.instruction import InstructionEnum
from mit_core.stack import StackEffect
from mit_core.spec import Register
from mit_core.stack import pop_stack, push_stack


@unique
class LibC(InstructionEnum):
    'Function codes for the external extra instruction LIBC.'
    EXIT = (StackEffect.of(['ret_code'], []), Code('''\
        exit(ret_code);
    '''))

    STRLEN = (StackEffect.of(['s:const char *'], ['len']), Code('''\
        len = (mit_word)(mit_uword)strlen(s);
    '''))

    STRNCPY = (StackEffect.of(['dest:char *', 'src:const char *', 'n'], ['ret:char *']),
        Code('ret = strncpy(dest, src, (size_t)n);'),
    )

    STDIN = (StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word)STDIN_FILENO;
    '''))

    STDOUT = (StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word)STDOUT_FILENO;
    '''))

    STDERR = (StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word)STDERR_FILENO;
    '''))

    O_RDONLY = (StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word)O_RDONLY;
    '''))

    O_WRONLY = (StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word)O_WRONLY;
    '''))

    O_RDWR = (StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word)O_RDWR;
    '''))

    O_CREAT = (StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word)O_CREAT;
    '''))

    O_TRUNC = (StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word)O_TRUNC;
    '''))

    OPEN = (StackEffect.of(['str:char *', 'flags'], ['fd:int']), Code('''\
        {

            fd = mit_address_range_valid(S, (mit_uword)str, 0) ?
                open(str, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            set_binary_mode(fd, O_BINARY); // Best effort
        }
    '''))

    CLOSE = (
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = (mit_word)close(fd);'),
    )

    READ = (
        StackEffect.of(['buf:uint8_t *', 'nbytes', 'fd:int'], ['nread:int']),
        Code('''\
            {
                nread = -1;
                if (mit_address_range_valid(S, (mit_uword)buf, nbytes))
                    nread = read(fd, buf, nbytes);
            }
        '''),
    )

    WRITE = (
        StackEffect.of(['buf:uint8_t *', 'nbytes', 'fd:int'], ['nwritten']),
        Code('''\
            {
                nwritten = -1;
                if (mit_address_range_valid(S, (mit_uword)buf, nbytes))
                    nwritten = write(fd, buf, nbytes);
            }
        '''),
    )

    SEEK_SET = (StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word)SEEK_SET;
    '''))

    SEEK_CUR = (StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word)SEEK_CUR;
    '''))

    SEEK_END = (StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word)SEEK_END;
    '''))

    LSEEK = (
        StackEffect.of(['fd:int', 'offset:off_t', 'whence'], ['pos:off_t']),
        Code('pos = lseek(fd, offset, whence);'),
    )

    FDATASYNC = (
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = fdatasync(fd);'),
    )

    RENAME = (
        StackEffect.of(['old_name:char *', 'new_name:char *'], ['ret:int']),
        Code('ret = rename(old_name, new_name);'),
    )

    REMOVE = (
        StackEffect.of(['name:char *'], ['ret:int']),
        Code('ret = remove(name);')
    )

    # TODO: Expose stat(2). This requires struct mapping!
    FILE_SIZE = (
        StackEffect.of(['fd:int'], ['size:off_t', 'ret:int']),
        Code('''\
            {
                struct stat st;
                ret = fstat(fd, &st);
                size = st.st_size;
            }
        '''),
    )

    RESIZE_FILE = (
        StackEffect.of(['size:off_t', 'fd:int'], ['ret:int']),
        Code('ret = ftruncate(fd, size);'),
    )

    FILE_STATUS = (
        StackEffect.of(['fd:int'], ['mode:mode_t', 'ret:int']),
        Code('''\
            {
                struct stat st;
                ret = fstat(fd, &st);
                mode = st.st_mode;
            }
        '''),
    )

mit_lib = {}

for register in Register:
    pop_code = Code()
    pop_code.append('mit_state *inner_state;')
    pop_code.extend(pop_stack('inner_state', type='mit_state *'))

    get_code = Code()
    get_code.extend(pop_code)
    get_code.extend(push_stack(
        'mit_get_{}(inner_state)'.format(register.name),
        type=register.type
    ))
    mit_lib['GET_{}'.format(register.name.upper())] = (
        None, get_code,
    )

    set_code = Code()
    set_code.extend(pop_code)
    set_code.append('{} value;'.format(register.type))
    set_code.extend(pop_stack('value', register.type))
    set_code.append('''\
        mit_set_{}(inner_state, value);'''.format(register.name),
    )
    mit_lib['SET_{}'.format(register.name.upper())] = (
        None, set_code,
    )

mit_lib.update({
    # libmit functions

    'CURRENT_STATE': (
        StackEffect.of([], ['state:mit_state *']),
        Code('state = S;'),
    ),

    'ADDRESS_RANGE_VALID': (
        StackEffect.of(
            ['addr', 'len', 'inner_state:mit_state *'],
            ['flag'],
        ),
        Code('flag = mit_address_range_valid(inner_state, addr, len);'),
    ),

    'LOAD_STACK': (
        StackEffect.of(
            ['pos', 'inner_state:mit_state *'],
            ['value', 'ret:int'],
        ),
        Code('''\
            value = 0;
            ret = mit_load_stack(inner_state, pos, &value);
        '''),
    ),

    'STORE_STACK': (
        StackEffect.of(
            ['value', 'pos', 'inner_state:mit_state *'],
            ['ret:int'],
        ),
        Code('ret = mit_store_stack(inner_state, pos, value);'),
    ),

    'POP_STACK': (
        StackEffect.of(
            ['inner_state:mit_state*'],
            ['value', 'ret:int'],
        ),
        Code('''\
            value = 0;
            ret = mit_pop_stack(inner_state, &value);
        ''')
    ),

    'PUSH_STACK': (
        StackEffect.of(
            ['value', 'inner_state:mit_state *'],
            ['ret:int'],
        ),
        Code('ret = mit_push_stack(inner_state, value);'),
    ),

    'NEW_STATE': (
        StackEffect.of(
            ['memory_words', 'stack_words'],
            ['new_state:mit_state *'],
        ),
        Code('''\
            new_state = mit_new_state((size_t)memory_words, (size_t)stack_words);
        '''),
    ),

    'FREE_STATE': (
        StackEffect.of(['inner_state:mit_state *'], []),
        Code('mit_free_state(inner_state);'),
    ),

    'RUN': (
        StackEffect.of(['inner_state:mit_state *'], ['ret']),
        Code('ret = mit_run(inner_state);'),
    ),

    'SINGLE_STEP': (
        StackEffect.of(['inner_state:mit_state *'], ['ret']),
        Code('ret = mit_single_step(inner_state);'),
    ),

    'NATIVE_POINTER_WORDS': (
        StackEffect.of([], ['n']),
        Code('n = MAX(sizeof(void *), sizeof(mit_word)) / sizeof(mit_word);'),
    ),


    # libmitfeatures functions

    'ARGC': (
        StackEffect.of([], ['argc']),
        Code('argc = (mit_word)mit_argc();'),
    ),

    'ARG': (
        StackEffect.of(['u'], ['arg:const char *']),
        Code('arg = mit_argv((int)u);'),
    ),

    'REGISTER_ARGS': (
        # Note: actually "char *argv[]", but we can't express that.
        StackEffect.of(['argc:int', 'argv:const char **'], ['ret:int']),
        Code('ret = mit_register_args(argc, argv);'),
    ),

    'EXTRA_INSTRUCTION': (
        StackEffect.of(['state:mit_state *'], ['ret']),
        Code('ret = mit_extra_instruction(state);'),
    ),

    'CORE_DUMP': (
        StackEffect.of(['state:mit_state *'], ['file:const char *']),
        Code('file = mit_core_dump(state);'),
    ),

    'SPECIALIZER_RUN': (
        StackEffect.of(['state:mit_state *'], ['ret']),
        Code('ret = mit_specializer_run(state);'),
    ),

    'PROFILE_INIT': (
        StackEffect.of([], []),
        Code('mit_profile_init();'),
    ),

    'PROFILE_RUN': (
        StackEffect.of(['state:mit_state *'], ['ret']),
        Code('ret = mit_profile_run(state);'),
    ),

    'PROFILE_DUMP': (
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = mit_profile_dump(fd);'),
    ),

    'STEP_TO': (
        StackEffect.of(['state:mit_state *', 'n:mit_uword *', 'addr', 'auto_NEXT:int'], ['ret']),
        Code('ret = mit_step_to(state, n, addr, auto_NEXT);'),
    ),
})

LibMit = InstructionEnum('LibMit', mit_lib)
LibMit.__doc__ = 'Function codes for the external extra instruction LIBMIT.'


class Library(InstructionEnum):
    '''Wrap an Instruction enumeration as a library.'''
    def __init__(self, opcode, library, includes, extra_types=[]):
        super().__init__(None, Code(
            '''\
            {
                mit_word function;''',
            pop_stack('function'),
            '''
                int ret = extra_{}(S, function);
                if (ret != 0)
                    RAISE(ret);
            }}'''.format(self.name.lower())
        ), opcode=opcode)
        self.library = library
        self.includes = includes
        self.extra_types = extra_types

    def types(self):
        '''Return a list of all types used in the library.'''
        return list(set(self.extra_types +
            [item.type
             for function in self.library
             if function.effect is not None
             for item in function.effect.by_name.values()
            ]
        ))

@unique
class LibInstruction(Library):
    '''External extra instruction opcodes.'''
    LIBMIT = (0x01, LibMit, '''\
#include "minmax.h"

#include "mit/mit.h"
#include "mit/features.h"
''',
              ['mit_word *'])
    LIBC = (0x02, LibC, '''\
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include "binary-io.h"
''')
