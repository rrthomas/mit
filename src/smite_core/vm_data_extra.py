# Extra instructions.
#
# (c) SMite authors 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique

from .instruction_gen import Instruction


# FIXME: this should be a per-library attribute
includes = '''\
#include "config.h"

#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include "binary-io.h"
#include "verify.h"

#include "smite.h"
#include "extra.h"
#include "opcodes.h"
'''

@unique
class LibcLib(Enum):
    ARGC = Instruction(0x0, [], ['argc'], '''\
        argc = S->main_argc;
    ''')

    ARG = Instruction(0x1, ['u'], ['arg:char *'], '''\
        arg = S->main_argv[u];
    ''')

    EXIT = Instruction(0x2, ['ret_code'], [], '''\
        exit(ret_code);
    ''')

    STRLEN = Instruction(0x3, ['s:const char *'], ['len'], '''\
        len = (smite_WORD)(smite_UWORD)strlen(s);
    ''')

    STRNCPY = Instruction(0x4, ['dest:char *', 'src:const char *', 'n'], ['ret:char *'], '''\
        ret = strncpy(dest, src, (size_t)n);
    ''')

    STDIN = Instruction(0x5, [], ['fd'], '''\
        fd = (smite_WORD)STDIN_FILENO;
    ''')

    STDOUT = Instruction(0x6, [], ['fd'], '''\
        fd = (smite_WORD)STDOUT_FILENO;
    ''')

    STDERR = Instruction(0x7, [], ['fd'], '''\
        fd = (smite_WORD)STDERR_FILENO;
    ''')

    O_RDONLY = Instruction(0x8, [], ['flag'], '''\
        flag = (smite_WORD)O_RDONLY;
    ''')

    O_WRONLY = Instruction(0x9, [], ['flag'], '''\
        flag = (smite_WORD)O_WRONLY;
    ''')

    O_RDWR = Instruction(0xa, [], ['flag'], '''\
        flag = (smite_WORD)O_RDWR;
    ''')

    O_CREAT = Instruction(0xb, [], ['flag'], '''\
        flag = (smite_WORD)O_CREAT;
    ''')

    O_TRUNC = Instruction(0xc, [], ['flag'], '''\
        flag = (smite_WORD)O_TRUNC;
    ''')

    OPEN = Instruction(0xd, ['str', 'flags'], ['fd'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            fd = s ? open(s, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            set_binary_mode(fd, O_BINARY); // Best effort
        }
    ''')

    CLOSE = Instruction(0xe, ['fd'], ['ret'], '''\
        ret = (smite_WORD)close(fd);
    ''')

    READ = Instruction(0xf, ['buf', 'nbytes', 'fd'], ['nread'], '''\
        {
            nread = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nread = read((int)fd, ptr, nbytes);
        }
    ''')

    WRITE = Instruction(0x10, ['buf', 'nbytes', 'fd'], ['nwritten'], '''\
        {
            nwritten = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nwritten = write((int)fd, ptr, nbytes);
        }
    ''')

    SEEK_SET = Instruction(0x11, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_SET;
    ''')

    SEEK_CUR = Instruction(0x12, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_CUR;
    ''')

    SEEK_END = Instruction(0x13, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_END;
    ''')

    LSEEK = Instruction(0x14, ['fd', 'offset:off_t', 'whence'], ['pos:off_t'], '''\
        pos = lseek((int)fd, offset, whence);
    ''')

    FDATASYNC = Instruction(0x15, ['fd'], ['ret'], '''\
        ret = fdatasync((int)fd);
    ''')

    RENAME = Instruction(0x16, ['old_name', 'new_name'], ['ret'], '''\
        {
            char *s1 = (char *)smite_native_address_of_range(S, old_name, 0);
            char *s2 = (char *)smite_native_address_of_range(S, new_name, 0);
            if (s1 == NULL || s2 == NULL)
                RAISE(SMITE_ERR_MEMORY_READ);
            ret = rename(s1, s2);
        }
    ''')

    REMOVE = Instruction(0x17, ['name'], ['ret'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, name, 0);
            if (s == NULL)
                RAISE(SMITE_ERR_MEMORY_READ);
            ret = remove(s);
        }
    ''')

    # FIXME: Expose stat(2). This requires struct mapping!
    FILE_SIZE = Instruction(0x18, ['fd'], ['size:off_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            size = st.st_size;
        }
    ''')

    RESIZE_FILE = Instruction(0x19, ['size:off_t', 'fd'], ['ret'], '''\
        ret = ftruncate((int)fd, size);
    ''')

    FILE_STATUS = Instruction(0x1a, ['fd'], ['mode:mode_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            mode = st.st_mode;
        }
    ''')

@unique
class SMiteLib(Enum):
    CURRENT_STATE = Instruction(0x0, [], ['state:smite_state *'], '''\
        state = S;
    ''')

    LOAD_WORD = Instruction(0x1, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        value = 0;
        ret = load_word(inner_state, addr, &value);
    ''')

    STORE_WORD = Instruction(0x2, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_word(inner_state, addr, value);
    ''')

    LOAD_BYTE = Instruction(0x3, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        {
            smite_BYTE b = 0;
            ret = load_byte(inner_state, addr, &b);
            value = b;
        }
    ''')

    STORE_BYTE = Instruction(0x4, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_byte(inner_state, addr, (smite_BYTE)value);
    ''')

    REALLOC_MEMORY = Instruction(0x5, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_memory(inner_state, (size_t)u);
    ''')

    REALLOC_STACK = Instruction(0x6, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_stack(inner_state, (size_t)u);
    ''')

    NATIVE_ADDRESS_OF_RANGE = Instruction(0x7, ['addr', 'len', 'inner_state:smite_state *'], ['ptr:uint8_t *'], '''\
        ptr = smite_native_address_of_range(inner_state, addr, len);
    ''')

    RUN = Instruction(0x8, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_run(inner_state);
    ''')

    SINGLE_STEP = Instruction(0x9, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_single_step(inner_state);
    ''')

    LOAD_OBJECT = Instruction(0xa, ['fd', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_load_object(inner_state, (int)fd, addr);
    ''')

    INIT = Instruction(0xb, ['memory_size', 'stack_size'], ['new_state:smite_state *'], '''\
        new_state = smite_init((size_t)memory_size, (size_t)stack_size);
    ''')

    DESTROY = Instruction(0xc, ['inner_state:smite_state *'], [], '''\
        smite_destroy(inner_state);
    ''')

    REGISTER_ARGS = Instruction(0xd, ['argv:char **', 'argc', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_register_args(inner_state, (int)argc, argv);
    ''')

class Library(Instruction):
    '''Wrap an Instruction enumeration as a library.'''
    def __init__(self, opcode, library):
        super().__init__(opcode, ['function'], [], '''\
{{
    int ret = extra_{}(S, function);
    if (ret != 0)
        RAISE(ret);
}}''')
        self.library = library

    def types(self):
        '''Return a list of all types used in the library.'''
        return list(set(
            [item.type for instruction in
             [function.value
              for function in self.library]
             for item in (instruction.effect.args +
                          instruction.effect.results)
            ]
        ))

@unique
class LibInstructions(Enum):
    '''VM instruction instructions to access external libraries.'''
    LIB_SMITE = Library(0x3f, SMiteLib)
    LIB_C = Library(0x3e, LibcLib)

# Inject name into each library's code
for instruction in LibInstructions:
    instruction.value.code = instruction.value.code.format(str.lower(instruction.name))
