# Extra instructions.
#
# (c) Reuben Thomas 1994-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique
from .action_gen import Action

@unique
class LibcLib(Enum):
    ARGC = Action(0x0, [], ['argc'], '''\
        argc = S->main_argc;
    ''')

    ARG = Action(0x1, ['u'], ['arg:char *'], '''\
        arg = S->main_argv[u];
    ''')

    EXIT = Action(0x2, ['ret_code'], [], '''\
        exit(ret_code);
    ''')

    STRLEN = Action(0x3, ['s:const char *'], ['len'], '''\
        len = (smite_WORD)(smite_UWORD)strlen(s);
    ''')

    STRNCPY = Action(0x4, ['dest:char *', 'src:const char *', 'n'], ['ret:char *'], '''\
        ret = strncpy(dest, src, (size_t)n);
    ''')

    STDIN = Action(0x5, [], ['fd'], '''\
        fd = (smite_WORD)STDIN_FILENO;
    ''')

    STDOUT = Action(0x6, [], ['fd'], '''\
        fd = (smite_WORD)STDOUT_FILENO;
    ''')

    STDERR = Action(0x7, [], ['fd'], '''\
        fd = (smite_WORD)STDERR_FILENO;
    ''')

    OPEN_FILE = Action(0x8, ['str', 'perm_'], ['fd', 'ret'], '''\
        {
            bool binary = false;
            int perm = getflags(perm_, &binary);
            char *s = (char *)smite_native_address_of_range(S, str, 0);
            fd = s ? open(s, perm, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH) : -1;
            ret = fd < 0 || (binary && set_binary_mode(fd, O_BINARY) < 0) ? -1 : 0;
        }
    ''')

    CLOSE_FILE = Action(0x9, ['fd'], ['ret'], '''\
        ret = (smite_WORD)close(fd);
    ''')

    READ_FILE = Action(0xa, ['buf', 'nbytes', 'fd'], ['nread', 'ret'], '''\
        {
            nread = 0;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nread = read((int)fd, ptr, nbytes);
            ret = nread >= 0 ? 0 : -1;
        }
    ''')

    WRITE_FILE = Action(0xb, ['buf', 'nbytes', 'fd'], ['nwritten', 'ret'], '''\
        {
            nwritten = 0;
            uint8_t *ptr = smite_native_address_of_range(S, buf, nbytes);
            if (ptr)
                nwritten = write((int)fd, ptr, nbytes);
            ret = nwritten >= 0 ? 0 : -1;
        }
    ''')

    FILE_POSITION = Action(0xc, ['fd'], ['pos:off_t', 'ret'], '''\
        pos = lseek((int)fd, 0, SEEK_CUR);
        ret = pos >= 0 ? 0 : -1;
    ''')

    REPOSITION_FILE = Action(0xd, ['pos:off_t', 'fd'], ['ret'], '''\
        ret = lseek((int)fd, pos, SEEK_SET) >= 0 ? 0 : -1;
    ''')

    FLUSH_FILE = Action(0xe, ['fd'], ['ret'], '''\
        ret = fdatasync((int)fd);
    ''')

    RENAME_FILE = Action(0xf, ['old_name', 'new_name'], ['ret'], '''\
        {
            char *s1 = (char *)smite_native_address_of_range(S, old_name, 0);
            char *s2 = (char *)smite_native_address_of_range(S, new_name, 0);
            if (s1 == NULL || s2 == NULL)
                RAISE(5);
            ret = rename(s1, s2);
        }
    ''')

    DELETE_FILE = Action(0x10, ['name'], ['ret'], '''\
        {
            char *s = (char *)smite_native_address_of_range(S, name, 0);
            if (s == NULL)
                RAISE(5);
            ret = remove(s);
        }
    ''')

    FILE_SIZE = Action(0x11, ['fd'], ['size:off_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            size = st.st_size;
        }
    ''')

    RESIZE_FILE = Action(0x12, ['size:off_t', 'fd'], ['ret'], '''\
        ret = ftruncate((int)fd, size);
    ''')

    FILE_STATUS = Action(0x13, ['fd'], ['mode:mode_t', 'ret'], '''\
        {
            struct stat st;
            ret = fstat((int)fd, &st);
            mode = st.st_mode;
        }
    ''')

@unique
class SMiteLib(Enum):
    CURRENT_STATE = Action(0x0, [], ['state:smite_state *'], '''\
        state = S;
    ''')

    LOAD_WORD = Action(0x1, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        ret = smite_load_word(inner_state, addr, &value);
    ''')

    STORE_WORD = Action(0x2, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_store_word(inner_state, addr, value);
    ''')

    LOAD_BYTE = Action(0x3, ['addr', 'inner_state:smite_state *'], ['value', 'ret'], '''\
        {
            smite_BYTE b;
            ret = smite_load_byte(inner_state, addr, &b);
            value = b;
        }
    ''')

    STORE_BYTE = Action(0x4, ['value', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_store_byte(inner_state, addr, (smite_BYTE)value);
    ''')

    REALLOC_MEMORY = Action(0x5, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_memory(inner_state, (size_t)u);
    ''')

    REALLOC_STACK = Action(0x6, ['u', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_realloc_stack(inner_state, (size_t)u);
    ''')

    NATIVE_ADDRESS_OF_RANGE = Action(0x7, ['addr', 'len', 'inner_state:smite_state *'], ['ptr:uint8_t *'], '''\
        ptr = smite_native_address_of_range(inner_state, addr, len);
    ''')

    RUN = Action(0x8, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_run(inner_state);
    ''')

    SINGLE_STEP = Action(0x9, ['inner_state:smite_state *'], ['ret'], '''\
        ret = smite_single_step(inner_state);
    ''')

    LOAD_OBJECT = Action(0xa, ['fd', 'addr', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_load_object(inner_state, (int)fd, addr);
    ''')

    INIT = Action(0xb, ['memory_size', 'stack_size'], ['new_state:smite_state *'], '''\
        new_state = smite_init((size_t)memory_size, (size_t)stack_size);
    ''')

    DESTROY = Action(0xc, ['inner_state:smite_state *'], [], '''\
        smite_destroy(inner_state);
    ''')

    REGISTER_ARGS = Action(0xd, ['argv:char **', 'argc', 'inner_state:smite_state *'], ['ret'], '''\
        ret = smite_register_args(inner_state, (int)argc, argv);
    ''')

class Library(Action):
    '''Wrap an Action enumeration as a library.'''
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
