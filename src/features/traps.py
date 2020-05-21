# Trap functions.
#
# (c) Mit authors 1994-2020
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

from enum import Enum, unique

from code_util import Code
from action import Action, ActionEnum
from stack import StackEffect, pop_stack


@unique
class LibC(ActionEnum):
    'Function codes for the LIBC trap.'

    STRLEN = Action(StackEffect.of(['s:const char *'], ['len']), Code('''\
        len = (mit_word_t)(mit_uword_t)strlen(s);
    '''))

    STRNCPY = Action(StackEffect.of(['dest:char *', 'src:const char *', 'n'], ['ret:char *']),
        Code('ret = strncpy(dest, src, (size_t)n);'),
    )

    STDIN = Action(StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word_t)STDIN_FILENO;
    '''))

    STDOUT = Action(StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word_t)STDOUT_FILENO;
    '''))

    STDERR = Action(StackEffect.of([], ['fd:int']), Code('''\
        fd = (mit_word_t)STDERR_FILENO;
    '''))

    O_RDONLY = Action(StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word_t)O_RDONLY;
    '''))

    O_WRONLY = Action(StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word_t)O_WRONLY;
    '''))

    O_RDWR = Action(StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word_t)O_RDWR;
    '''))

    O_CREAT = Action(StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word_t)O_CREAT;
    '''))

    O_TRUNC = Action(StackEffect.of([], ['flag']), Code('''\
        flag = (mit_word_t)O_TRUNC;
    '''))

    OPEN = Action(StackEffect.of(['str:char *', 'flags'], ['fd:int']), Code('''\
        fd = open(str, flags, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH);
        set_binary_mode(fd, O_BINARY); // Best effort
    '''))

    CLOSE = Action(
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = (mit_word_t)close(fd);'),
    )

    READ = Action(
        StackEffect.of(['buf:void *', 'nbytes', 'fd:int'], ['nread:int']),
        Code('nread = read(fd, buf, nbytes);'),
    )

    WRITE = Action(
        StackEffect.of(['buf:void *', 'nbytes', 'fd:int'], ['nwritten']),
        Code('nwritten = write(fd, buf, nbytes);'),
    )

    SEEK_SEAT = Action(StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word_t)SEEK_SET;
    '''))

    SEEK_CUR = Action(StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word_t)SEEK_CUR;
    '''))

    SEEK_END = Action(StackEffect.of([], ['whence']), Code('''\
        whence = (mit_word_t)SEEK_END;
    '''))

    LSEEK = Action(
        StackEffect.of(['fd:int', 'offset:off_t', 'whence'], ['pos:off_t']),
        Code('pos = lseek(fd, offset, whence);'),
    )

    FDATASYNC = Action(
        StackEffect.of(['fd:int'], ['ret:int']),
        Code('ret = fdatasync(fd);'),
    )

    RENAME = Action(
        StackEffect.of(['old_name:char *', 'new_name:char *'], ['ret:int']),
        Code('ret = rename(old_name, new_name);'),
    )

    REMOVE = Action(
        StackEffect.of(['name:char *'], ['ret:int']),
        Code('ret = remove(name);')
    )

    # TODO: Expose stat(2). This requires struct mapping!
    FILE_SIZE = Action(
        StackEffect.of(['fd:int'], ['size:off_t', 'ret:int']),
        Code('''\
            {
                struct stat st;
                ret = fstat(fd, &st);
                size = st.st_size;
            }
        '''),
    )

    RESIZE_FILE = Action(
        StackEffect.of(['size:off_t', 'fd:int'], ['ret:int']),
        Code('ret = ftruncate(fd, size);'),
    )

    FILE_STATUS = Action(
        StackEffect.of(['fd:int'], ['mode:mode_t', 'ret:int']),
        Code('''\
            {
                struct stat st;
                ret = fstat(fd, &st);
                mode = st.st_mode;
            }
        '''),
    )


class LibraryEnum(ActionEnum):
    '''Wrap an ActionEnum as a library.'''
    def __init__(self, opcode, library, includes):
        super().__init__(Action(None, Code(
            '''\
            {
                mit_word_t function;''',
            pop_stack('function'),
            f'''
                int ret = trap_{self.name.lower()}(function, stack, &stack_depth);
                if (ret != 0)
                    RAISE(ret);
            }}'''
        )), opcode=opcode)
        self.library = library
        self.includes = includes

    def types(self):
        '''Return a list of all types used in the library.'''
        return list(set(
            [item.type
             for function in self.library
             if function.action.effect is not None
             for item in function.action.effect.by_name.values()
            ]
        ))

@unique
class LibInstructions(LibraryEnum):
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
