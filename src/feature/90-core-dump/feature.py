Option('core-dump',
       'dump core on memory exception',
       short_name='c', arg='no_argument',
       top_level_code='''\
#include <stdio.h>
#include <stdbool.h>
#include <limits.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>

#define REGISTER_STRLEN (WORD_BYTES * 2)

static char hex[] = "0123456789abcdef";

static void register_to_str(mit_WORD reg, char *s)
{
    for (unsigned i = 0; i < REGISTER_STRLEN; i++) {
        s[REGISTER_STRLEN - i - 1] = hex[reg & 0xf];
        reg >>= 4;
    }
}
''',
       init_code='bool core_dump = false;',
       parse_code='core_dump = true;',
       exception_handler='''\
default:
    // Core dump on error
    if (core_dump) {
        char pc_str[REGISTER_STRLEN];
        char bad_str[REGISTER_STRLEN];
        register_to_str(S->PC, &pc_str[0]);
        register_to_str(S->BAD, &bad_str[0]);
        warn("error %d raised at PC=0x%.*s; BAD=0x%.*s", res,
            REGISTER_STRLEN, pc_str, REGISTER_STRLEN, bad_str);

        // Ignore errors; best effort only, in the middle of an error exit
        char file_format[] = "mit-core.%lu";
        char file[sizeof(file_format) + sizeof(unsigned long) * CHAR_BIT];
        sprintf(file, "mit-core.%lu", (unsigned long)getpid());
        if (file != NULL) {
            if ((fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH)) >= 0) {
                (void)mit_save_object(S, 0, S->memory_size, fd);
                close(fd);
                warn("core dumped to %s", file);
            } else
                perror("open error");
        }
    }
break;
''')
