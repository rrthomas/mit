# Extra instructions.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique

from .instruction_gen import Instruction, StackPicture
try:
    from .type_sizes import type_sizes
except ImportError:
    pass # We can't generate code

class TypedInstruction(Instruction):
    '''VM instruction instruction descriptor.

    An Instruction, but with TypedStackPictures.
    '''
    def __init__(self, opcode, args, results, code):
        '''
         - args - list acceptable to TypedStackPicture.from_list.
         - results - list acceptable to TypedStackPicture.from_list.
        '''
        self.opcode = opcode
        self.args = TypedStackPicture.from_list(args)
        self.results = TypedStackPicture.from_list(results)
        self.code = code


class TypedItem:
    def __init__(self, name, type):
        self.name = name
        self.type = type

def bytes_to_words(size):
    '''Return the number of words occupied by 'size' bytes.'''
    return (size + (type_sizes['smite_WORD'] - 1)) // type_sizes['smite_WORD']

class TypedStackPicture(StackPicture):
    '''
    A StackPicture where each item has a C type.

    Public fields:

     - named_items - list of TypedItem - the non-variadic items.
       The constructor argument is a list of str, each name optionally
       followed by ":TYPE" to give the C type of the underlying quantity.

     - is_variadic - bool - If `True`, there are `COUNT` more items underneath
       the non-variadic items.

     FIXME: Generate a proper error if type_sizes is used when unavailable.
    '''
    def __init__(self, item_list, is_variadic=False):
        named_items = []
        for item in item_list:
            l = item.split(":")
            name = l[0]
            type = l[1] if len(l) > 1 else 'smite_WORD'
            named_items.append(TypedItem(name, type))
        assert len(set(named_items)) == len(named_items)
        self.named_items = named_items
        self.is_variadic = is_variadic

    # In load_var & store_var, casts to size_t avoid warnings when `var` is
    # a pointer and sizeof(void *) > WORD_SIZE, but the effect is identical.
    @staticmethod
    def load_var(pos, var):
        code = ['{} = 0;'.format(var.name)]
        num_items = bytes_to_words(type_sizes[var.type])
        for i in reversed(range(num_items)):
            code.append('UNCHECKED_LOAD_STACK({}, &temp);'.format(pos + i))
            if i < num_items - 1:
                code.append('{var} = ({type})((size_t){var} << smite_WORD_BIT);'.format(var=var.name, type=var.type))
            code.append('{var} = ({type})((size_t){var} | (smite_UWORD)temp);'.format(var=var.name, type=var.type))
        return '\n'.join(code)

    @staticmethod
    def store_var(pos, var):
        code = []
        num_items = bytes_to_words(type_sizes[var.type])
        for i in range(num_items):
            code.append('UNCHECKED_STORE_STACK({pos}, (smite_UWORD)((size_t){var} & smite_WORD_MASK));'.format(pos=pos + i, var=var.name))
            if i < num_items - 1:
                code.append('{var} = ({type})((size_t){var} >> smite_WORD_BIT);'.format(var=var.name, type=var.type))
        return '\n'.join(code)

    def static_depth(self):
        '''
        Returns the number of stack words occupied by the static items in a
        TypedStackPicture.
        '''
        return sum([type_sizes[item.type] // type_sizes['smite_WORD'] for item in self.named_items])

    def declare_vars(self):
        '''Returns C variable declarations for all of `self.named_items`.'''
        return '\n'.join(['{} {};'.format(item.type, item.name)
                          for item in self.named_items])

    def load(self, cached_depth):
        '''
        Returns C source code to read the named items from the stack into C
        variables.
        `S->STACK_DEPTH` is not modified.
        '''
        assert cached_depth == 0
        code = []
        pos = 0
        for item in reversed(self.named_items):
            code.append(self.load_var(pos, item))
            pos += type_sizes[item.type] // type_sizes['smite_WORD']
        return '\n'.join(code)

    def store(self, cached_depth):
        '''
        Returns C source code to write the named items from C variables into
        the stack.
        `S->STACK_DEPTH` must be modified first.
        '''
        assert cached_depth == 0
        code = []
        pos = 0
        for item in reversed(self.named_items):
            code.append(self.store_var(pos, item))
            pos += type_sizes[item.type] // type_sizes['smite_WORD']
        return '\n'.join(code)

# FIXME: this should be a per-library attribute
includes = '''\
#include "config.h"

#include <assert.h>

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
    ARGC = TypedInstruction(0x0, [], ['argc'], '''\
        argc = S->main_argc;
    ''')

    ARG = TypedInstruction(0x1, ['u'], ['arg:char *'], '''\
        arg = S->main_argv[u];
    ''')

    EXIT = TypedInstruction(0x2, ['ret_code'], [], '''\
        exit(ret_code);
    ''')

    STRLEN = TypedInstruction(0x3, ['s:const char *'], ['len'], '''\
        len = (smite_WORD)(smite_UWORD)strlen(s);
    ''')

    STRNCPY = TypedInstruction(0x4, ['dest:char *', 'src:const char *', 'n'], ['ret:char *'], '''\
        ret = strncpy(dest, src, (size_t)n);
    ''')

    STDIN = TypedInstruction(0x5, [], ['fd'], '''\
        fd = (smite_WORD)STDIN_FILENO;
    ''')

    STDOUT = TypedInstruction(0x6, [], ['fd'], '''\
        fd = (smite_WORD)STDOUT_FILENO;
    ''')

    STDERR = TypedInstruction(0x7, [], ['fd'], '''\
        fd = (smite_WORD)STDERR_FILENO;
    ''')

    O_RDONLY = TypedInstruction(0x8, [], ['flag'], '''\
        flag = (smite_WORD)O_RDONLY;
    ''')

    O_WRONLY = TypedInstruction(0x9, [], ['flag'], '''\
        flag = (smite_WORD)O_WRONLY;
    ''')

    O_RDWR = TypedInstruction(0xa, [], ['flag'], '''\
        flag = (smite_WORD)O_RDWR;
    ''')

    O_CREAT = TypedInstruction(0xb, [], ['flag'], '''\
        flag = (smite_WORD)O_CREAT;
    ''')

    O_TRUNC = TypedInstruction(0xc, [], ['flag'], '''\
        flag = (smite_WORD)O_TRUNC;
    ''')

    OPEN = TypedInstruction(0xd, ['str', 'flags'], ['fd'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            fd = s ? open(s, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            set_binary_mode(fd, O_BINARY); // Best effort
        }
    ''')

    CLOSE = TypedInstruction(0xe, ['fd'], ['ret'], '''\
        ret = (smite_WORD)close(fd);
    ''')

    READ = TypedInstruction(0xf, ['buf', 'nbytes', 'fd'], ['nread'], '''\
        {
            nread = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nread = read((int)fd, ptr, nbytes);
        }
    ''')

    WRITE = TypedInstruction(0x10, ['buf', 'nbytes', 'fd'], ['nwritten'], '''\
        {
            nwritten = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nwritten = write((int)fd, ptr, nbytes);
        }
    ''')

    SEEK_SET = TypedInstruction(0x11, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_SET;
    ''')

    SEEK_CUR = TypedInstruction(0x12, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_CUR;
    ''')

    SEEK_END = TypedInstruction(0x13, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_END;
    ''')

    LSEEK = TypedInstruction(0x14, ['fd', 'offset:off_t', 'whence'], ['pos:off_t'], '''\
        pos = lseek((int)fd, offset, whence);
    ''')

    FDATASYNC = TypedInstruction(0x15, ['fd'], ['ret'], '''\
        ret = fdatasync((int)fd);
    ''')

    RENAME = TypedInstruction(0x16, ['old_name', 'new_name'], ['ret'], '''\
        {
            char *s1 = (char *)smite_native_address_of_range(S, old_name, 0);
            char *s2 = (char *)smite_native_address_of_range(S, new_name, 0);
            if (s1 == NULL || s2 == NULL)
                RAISE(SMITE_ERR_MEMORY_READ);
            ret = rename(s1, s2);
        }
    ''')

    REMOVE = TypedInstruction(0x17, ['name'], ['ret'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, name, 0);
            if (s == NULL)
                RAISE(SMITE_ERR_MEMORY_READ);
            ret = remove(s);
        }
    ''')

    # FIXME: Expose stat(2). This requires struct mapping!
    FILE_SIZE = TypedInstruction(0x18, ['fd'], ['size:off_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            size = st.st_size;
        }
    ''')

    RESIZE_FILE = TypedInstruction(0x19, ['size:off_t', 'fd'], ['ret'], '''\
        ret = ftruncate((int)fd, size);
    ''')

    FILE_STATUS = TypedInstruction(0x1a, ['fd'], ['mode:mode_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            mode = st.st_mode;
        }
    ''')

@unique
class SMiteLib(Enum):
    CURRENT_STATE = TypedInstruction(0x0, [], ['state:smite_state *'], '''\
        state = S;
    ''')

    LOAD_WORD = TypedInstruction(0x1, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        value = 0;
        ret = load_word(inner_state, addr, &value);
    ''')

    STORE_WORD = TypedInstruction(0x2, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_word(inner_state, addr, value);
    ''')

    LOAD_BYTE = TypedInstruction(0x3, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        {
            smite_BYTE b = 0;
            ret = load_byte(inner_state, addr, &b);
            value = b;
        }
    ''')

    STORE_BYTE = TypedInstruction(0x4, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_byte(inner_state, addr, (smite_BYTE)value);
    ''')

    REALLOC_MEMORY = TypedInstruction(0x5, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_memory(inner_state, (size_t)u);
    ''')

    REALLOC_STACK = TypedInstruction(0x6, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_stack(inner_state, (size_t)u);
    ''')

    NATIVE_ADDRESS_OF_RANGE = TypedInstruction(0x7, ['addr', 'len', 'inner_state:smite_state *'], ['ptr:uint8_t *'], '''\
        ptr = smite_native_address_of_range(inner_state, addr, len);
    ''')

    RUN = TypedInstruction(0x8, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_run(inner_state);
    ''')

    SINGLE_STEP = TypedInstruction(0x9, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_single_step(inner_state);
    ''')

    LOAD_OBJECT = TypedInstruction(0xa, ['fd', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_load_object(inner_state, (int)fd, addr);
    ''')

    INIT = TypedInstruction(0xb, ['memory_size', 'stack_size'], ['new_state:smite_state *'], '''\
        new_state = smite_init((size_t)memory_size, (size_t)stack_size);
    ''')

    DESTROY = TypedInstruction(0xc, ['inner_state:smite_state *'], [], '''\
        smite_destroy(inner_state);
    ''')

    REGISTER_ARGS = TypedInstruction(0xd, ['argv:char **', 'argc', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_register_args(inner_state, (int)argc, argv);
    ''')

class Library(TypedInstruction):
    '''Wrap a TypedInstruction enumeration as a library.'''
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
        return list(set([item.type for picture in
                         [instruction.value
                          for instruction in self.library]
                         for item in picture.args.named_items + picture.results.named_items]))

@unique
class LibInstructions(Enum):
    '''VM instruction instructions to access external libraries.'''
    LIB_SMITE = Library(0x3f, SMiteLib)
    LIB_C = Library(0x3e, LibcLib)

# Inject name into each library's code
for instruction in LibInstructions:
    instruction.value.code = instruction.value.code.format(str.lower(instruction.name))
