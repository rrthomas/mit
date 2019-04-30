# Basic command-line flags, and extra documentation

Option('help',
       'display this help message and exit',
       parse_code='usage();'
)

Option('version',
       'display version information and exit',
       top_level_code='''\
#include <stdio.h>
#include <stdlib.h>
''',
       parse_code='''\
{
    printf(PACKAGE_NAME " " VERSION " (%d-byte word, %s-endian)\\n"
           "(c) SMite authors 1994-2019\\n"
           PACKAGE_NAME " comes with ABSOLUTELY NO WARRANTY.\\n"
           "You may redistribute copies of " PACKAGE_NAME "\\n"
           "under the terms of the MIT/X11 License.\\n",
           WORD_BYTES, ENDISM ? "big" : "little");
    exit(EXIT_SUCCESS);
}
''')

Arg('OBJECT-FILE', 'load and run object OBJECT-FILE')
Doc('')
Doc('"The ARGUMENTS are available to "PACKAGE_NAME"."')
Doc('')
Doc('If an error occurs during execution, the exit status is the error code; if')
Doc('execution HALTs normally, the exit status is the top-most stack value.')
Doc('')
Doc('"Report bugs to "PACKAGE_BUGREPORT"."')
