// Manage trap plugins, and dispatch traps.
//
// (c) Mit authors 2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <stdlib.h>
#include <string.h>

#include <ltdl.h>

#include "dirname.h"
#include "hash.h"

#include "mit/mit.h"

#include "run.h"


// The table in which trap modules are registered.
MIT_THREAD_LOCAL Hash_table *mit_traps;


// Register traps.
typedef struct trap
{
    const char *name;
    mit_fn_t *entry; // Entry point
} trap;

static size_t
str_hash (const void *s, size_t n)
{
    return hash_string(((trap *)s)->name, n);
}

static bool
str_cmp (const void *s, const void *t)
{
    return strcmp(((trap *)s)->name, ((trap *)t)->name) == 0;
}

int mit_register_trap(const char *file, Hash_table *traps)
{
    char *name = strdup(last_component(file));
    trap *xinst = malloc(sizeof(trap));
    if (name == NULL || xinst == NULL)
        goto error;

    lt_dlhandle module = lt_dlopenext(file);
    if (module != NULL) {
        void *entry = lt_dlsym(module, "mit_trap");
        if (entry != NULL) {
            xinst->name = name;
            xinst->entry = entry;
            if (hash_insert(traps, xinst) == NULL)
                goto error;
        }
    }
    return 0;

 error:
    free(name);
    free(xinst);
    return MIT_ERROR_REGISTER_LIBRARY_FAILED;
}

int mit_register_traps(void)
{
    if (lt_dlinit() != 0)
        return MIT_ERROR_REGISTER_LIBRARY_FAILED;

    free(mit_traps);
    mit_traps = hash_initialize(32, NULL, str_hash, str_cmp, NULL);

    char *env_path = secure_getenv("MIT_TRAP_PATH");
    char *path;
    if (asprintf(&path, "%s%c%s", env_path, LT_PATHSEP_CHAR, PATH_PKGLIBDIR) == -1)
        return MIT_ERROR_REGISTER_LIBRARY_FAILED;

    lt_dlforeachfile(path,
                     (int (*)(const char *, void *))(mit_register_trap),
                     (void *)mit_traps);

    free(path);
    return MIT_ERROR_OK;
}


// Execute a trap.
mit_word_t mit_trap(mit_word_t *pc, mit_word_t ir,
                            mit_word_t * restrict stack,
                            mit_uword_t stack_words,
                            mit_uword_t *stack_depth_ptr)
{
    mit_word_t error = MIT_ERROR_OK;
    mit_uword_t opcode = ir >> 8;

    /* if (opcode == XXX) { */
    /*     if (unlikely(S->stack_depth < 1)) */
    /*         RAISE(MIT_ERROR_INVALID_STACK_READ); */
    /*     mit_word_t function = *UNCHECKED_STACK(S->stack, S->stack_depth, 0); */
    /*     S->stack_depth -= 1; */

    /*     int ret = mit_trap_xxx(S, function); */
    /*     if (ret != 0) */
    /*         RAISE(ret); */
    /* } else */
        return MIT_ERROR_INVALID_LIBRARY;

error:
    return error;
}
