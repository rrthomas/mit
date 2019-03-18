# Extra instructions.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique
from .instruction_gen import Action, StackPicture

class TypedAction(Action):
    '''VM action instruction descriptor.

    An Action, but with TypedStackPictures.
    '''
    def __init__(self, opcode, args, results, code):
        '''
         - args - list acceptable to StackPicture.from_list.
         - results - list acceptable to StackPicture.from_list.
        '''
        self.opcode = opcode
        self.args = TypedStackPicture.from_list(args)
        self.results = TypedStackPicture.from_list(results)
        self.code = code


class TypedItem:
    def __init__(self, name, type):
        self.name = name
        self.type = type

class TypedStackPicture(StackPicture):
    '''
    A StackPicture where each item has a C type.

    Public fields:

     - named_items - list of TypedItem - the non-variadic items.
       The constructor argument is a list of str, each name optionally
       followed by ":TYPE" to give the C type of the underlying quantity.

     - is_variadic - bool - If `True`, there are `COUNT` more items underneath
       the non-variadic items.
    '''
    def __init__(self, item_list, is_variadic=False):
        named_items = []
        for item in item_list:
            named_items.append(TypedItem(self.stack_item_name(item),
                                         self.stack_item_type(item)))
        assert len(set(named_items)) == len(named_items)
        self.named_items = named_items
        self.is_variadic = is_variadic

    @staticmethod
    def stack_item_name(item):
        return item.split(":")[0]

    @staticmethod
    def stack_item_type(item):
        l = item.split(":")
        return l[1] if len(l) > 1 else 'smite_WORD'

    @staticmethod
    def type_size(type):
        '''Return a C expression for the size in stack words of a type.'''
        return '(sizeof({}) / WORD_SIZE)'.format(type)

    @staticmethod
    def load_var(pos, var):
        if var.type != 'smite_WORD':
            fmt = 'UNCHECKED_LOAD_STACK_TYPE({pos}, {type}, &{var});'
        else:
            fmt = 'UNCHECKED_LOAD_STACK({pos}, &{var});'
        return fmt.format(pos=pos, var=var.name, type=var.type)

    @staticmethod
    def store_var(pos, var):
        if var.type != 'smite_WORD':
            fmt = 'UNCHECKED_STORE_STACK_TYPE({pos}, {type}, {var});'
        else:
            fmt = 'UNCHECKED_STORE_STACK({pos}, {var});'
        return fmt.format(pos=pos, var=var.name, type=var.type)

    def static_depth(self):
        '''
        Return a C expression for the number of stack words occupied by the
        static items in a TypedStackPicture.
        '''
        depth = ' + '.join([self.type_size(item.type) for item in self.named_items])
        return '({})'.format(depth if depth != '' else '0')

    def declare_vars(self):
        '''Returns C variable declarations for all of `self.named_items`.'''
        return '\n'.join(['{} {};'.format(item.type, item.name)
                          for item in self.named_items])

    def load(self):
        '''
        Returns C source code to read the named items from the stack into C
        variables.
        `S->STACK_DEPTH` is not modified.
        '''
        code = []
        pos = ['-1']
        for item in reversed(self.named_items):
            pos.append(self.type_size(item.type))
            code.append(self.load_var(" + ".join(pos), item))
        return '\n'.join(code)

    def store(self):
        '''
        Returns C source code to write the named items from C variables into
        the stack.
        `S->STACK_DEPTH` must be modified first.
        '''
        code = []
        pos = ['-1']
        for item in reversed(self.named_items):
            pos.append(self.type_size(item.type))
            code.append(self.store_var(" + ".join(pos), item))
        return '\n'.join(code)


@unique
class LibcLib(Enum):
    ARGC = TypedAction(0x0, [], ['argc'], '''\
        argc = S->main_argc;
    ''')

    ARG = TypedAction(0x1, ['u'], ['arg:char *'], '''\
        arg = S->main_argv[u];
    ''')

    EXIT = TypedAction(0x2, ['ret_code'], [], '''\
        exit(ret_code);
    ''')

    STRLEN = TypedAction(0x3, ['s:const char *'], ['len'], '''\
        len = (smite_WORD)(smite_UWORD)strlen(s);
    ''')

    STRNCPY = TypedAction(0x4, ['dest:char *', 'src:const char *', 'n'], ['ret:char *'], '''\
        ret = strncpy(dest, src, (size_t)n);
    ''')

    STDIN = TypedAction(0x5, [], ['fd'], '''\
        fd = (smite_WORD)STDIN_FILENO;
    ''')

    STDOUT = TypedAction(0x6, [], ['fd'], '''\
        fd = (smite_WORD)STDOUT_FILENO;
    ''')

    STDERR = TypedAction(0x7, [], ['fd'], '''\
        fd = (smite_WORD)STDERR_FILENO;
    ''')

    O_RDONLY = TypedAction(0x8, [], ['flag'], '''\
        flag = (smite_WORD)O_RDONLY;
    ''')

    O_WRONLY = TypedAction(0x9, [], ['flag'], '''\
        flag = (smite_WORD)O_WRONLY;
    ''')

    O_RDWR = TypedAction(0xa, [], ['flag'], '''\
        flag = (smite_WORD)O_RDWR;
    ''')

    O_CREAT = TypedAction(0xb, [], ['flag'], '''\
        flag = (smite_WORD)O_CREAT;
    ''')

    O_TRUNC = TypedAction(0xc, [], ['flag'], '''\
        flag = (smite_WORD)O_TRUNC;
    ''')

    OPEN = TypedAction(0xd, ['str', 'flags'], ['fd'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            fd = s ? open(s, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            set_binary_mode(fd, O_BINARY); // Best effort
        }
    ''')

    CLOSE = TypedAction(0xe, ['fd'], ['ret'], '''\
        ret = (smite_WORD)close(fd);
    ''')

    READ = TypedAction(0xf, ['buf', 'nbytes', 'fd'], ['nread'], '''\
        {
            nread = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nread = read((int)fd, ptr, nbytes);
        }
    ''')

    WRITE = TypedAction(0x10, ['buf', 'nbytes', 'fd'], ['nwritten'], '''\
        {
            nwritten = -1;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nwritten = write((int)fd, ptr, nbytes);
        }
    ''')

    SEEK_SET = TypedAction(0x11, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_SET;
    ''')

    SEEK_CUR = TypedAction(0x12, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_CUR;
    ''')

    SEEK_END = TypedAction(0x13, [], ['whence'], '''\
        whence = (smite_WORD)SEEK_END;
    ''')

    LSEEK = TypedAction(0x14, ['fd', 'offset:off_t', 'whence'], ['pos:off_t'], '''\
        pos = lseek((int)fd, offset, whence);
    ''')

    FDATASYNC = TypedAction(0x15, ['fd'], ['ret'], '''\
        ret = fdatasync((int)fd);
    ''')

    RENAME = TypedAction(0x16, ['old_name', 'new_name'], ['ret'], '''\
        {
            char *s1 = (char *)smite_native_address_of_range(S, old_name, 0);
            char *s2 = (char *)smite_native_address_of_range(S, new_name, 0);
            if (s1 == NULL || s2 == NULL)
                RAISE(5);
            ret = rename(s1, s2);
        }
    ''')

    REMOVE = TypedAction(0x17, ['name'], ['ret'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, name, 0);
            if (s == NULL)
                RAISE(5);
            ret = remove(s);
        }
    ''')

    # FIXME: Expose stat(2). This requires struct mapping!
    FILE_SIZE = TypedAction(0x18, ['fd'], ['size:off_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            size = st.st_size;
        }
    ''')

    RESIZE_FILE = TypedAction(0x19, ['size:off_t', 'fd'], ['ret'], '''\
        ret = ftruncate((int)fd, size);
    ''')

    FILE_STATUS = TypedAction(0x1a, ['fd'], ['mode:mode_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            mode = st.st_mode;
        }
    ''')

@unique
class SMiteLib(Enum):
    CURRENT_STATE = TypedAction(0x0, [], ['state:smite_state *'], '''\
        state = S;
    ''')

    LOAD_WORD = TypedAction(0x1, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        value = 0;
        ret = load_word(inner_state, addr, &value);
    ''')

    STORE_WORD = TypedAction(0x2, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_word(inner_state, addr, value);
    ''')

    LOAD_BYTE = TypedAction(0x3, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        {
            smite_BYTE b = 0;
            ret = load_byte(inner_state, addr, &b);
            value = b;
        }
    ''')

    STORE_BYTE = TypedAction(0x4, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = store_byte(inner_state, addr, (smite_BYTE)value);
    ''')

    REALLOC_MEMORY = TypedAction(0x5, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_memory(inner_state, (size_t)u);
    ''')

    REALLOC_STACK = TypedAction(0x6, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_stack(inner_state, (size_t)u);
    ''')

    NATIVE_ADDRESS_OF_RANGE = TypedAction(0x7, ['addr', 'len', 'inner_state:smite_state *'], ['ptr:uint8_t *'], '''\
        ptr = smite_native_address_of_range(inner_state, addr, len);
    ''')

    RUN = TypedAction(0x8, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_run(inner_state);
    ''')

    SINGLE_STEP = TypedAction(0x9, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_single_step(inner_state);
    ''')

    LOAD_OBJECT = TypedAction(0xa, ['fd', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_load_object(inner_state, (int)fd, addr);
    ''')

    INIT = TypedAction(0xb, ['memory_size', 'stack_size'], ['new_state:smite_state *'], '''\
        new_state = smite_init((size_t)memory_size, (size_t)stack_size);
    ''')

    DESTROY = TypedAction(0xc, ['inner_state:smite_state *'], [], '''\
        smite_destroy(inner_state);
    ''')

    REGISTER_ARGS = TypedAction(0xd, ['argv:char **', 'argc', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_register_args(inner_state, (int)argc, argv);
    ''')

class Library(TypedAction):
    '''Wrap a TypedAction enumeration as a library.'''
    def __init__(self, opcode, library):
        super().__init__(opcode, ['function'], [], '''\
{{
    int ret = extra_{}(S, function);
    if (ret != 0)
        RAISE(ret);
}}''')
        self.library = library

@unique
class LibActions(Enum):
    '''VM action instructions to access external libraries.'''
    LIB_SMITE = Library(0x3f, SMiteLib)
    LIB_C = Library(0x3e, LibcLib)

# Inject name into each library's code
for action in LibActions:
    action.value.code = action.value.code.format(str.lower(action.name))
