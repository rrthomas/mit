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
''',
       init_code='bool core_dump = false;',
       parse_code='core_dump = true;',
       exception_handler='''\
default:
    // Core dump on error
    if (core_dump) {
        warn("error %d raised at PC=%"PRI_XWORD"; BAD=%"PRI_XWORD,
             res, S->PC, S->BAD);

        // Ignore errors; best effort only, in the middle of an error exit
        char file_format[] = "smite-core.%lu";
        char file[sizeof(file_format) + sizeof(unsigned long) * CHAR_BIT];
        sprintf(file, "smite-core.%lu", (unsigned long)getpid());
        if (file != NULL) {
            if ((fd = creat(file, S_IRUSR | S_IWUSR | S_IRGRP | S_IWGRP | S_IROTH | S_IWOTH)) >= 0) {
                (void)smite_save_object(S, 0, S->memory_size, fd);
                close(fd);
                warn("core dumped to %s", file);
            } else
                perror("open error");
        }
    }
break;
''')
