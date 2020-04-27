# TRAP functions.
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
from mit_core.stack import pop_stack


@unique
class LibC(InstructionEnum):
    'Function codes for the LIBC trap.'

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
        fd = open(str, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
        set_binary_mode(fd, O_BINARY); // Best effort
    '''))

    CLOSE = (
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = (mit_word)close(fd);'),
    )

    READ = (
        StackEffect.of(['buf:void *', 'nbytes', 'fd:int'], ['nread:int']),
        Code('nread = read(fd, buf, nbytes);'),
    )

    WRITE = (
        StackEffect.of(['buf:void *', 'nbytes', 'fd:int'], ['nwritten']),
        Code('nwritten = write(fd, buf, nbytes);'),
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


class Library(InstructionEnum):
    '''Wrap an Instruction enumeration as a library.'''
    def __init__(self, opcode, library, includes, extra_types=[]):
        super().__init__(None, Code(
            '''\
            {
                mit_word function;''',
            pop_stack('function'),
            '''
                int ret = trap_{}(S, function);
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
    LIBC = (0x0, LibC, '''
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <string.h>
#include "binary-io.h"
#include "mit/mit.h"
''')
