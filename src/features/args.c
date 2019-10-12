// Register command-line arguments.
//
// (c) Mit authors 2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include "mit/mit.h"
#include "mit/features.h"
#include "mit/extra-opcodes.h"


static int _argc;
static const char **_argv;

_GL_ATTRIBUTE_PURE int mit_argc(void)
{
    return _argc;
}

_GL_ATTRIBUTE_PURE const char *mit_argv(int arg)
{
    if (arg >= 0 && arg < _argc)
        return _argv[arg];
    return NULL;
}

int mit_register_args(int argc, const char *argv[])
{
    // Check argc is non-negative
    if (argc >= 0) {
        // Check first argc elements of argv are non-NULL.
        for (int i = 0; i < argc; i++)
            if (argv[i] == NULL)
                goto error;

        _argc = argc;
        _argv = argv;
        return MIT_ERROR_OK;
    }

 error:
    return MIT_REGISTER_ARGS_ERROR_TOO_FEW_ARGUMENTS;
}
