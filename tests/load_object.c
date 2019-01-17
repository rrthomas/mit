// Test load_object().
//
// (c) Reuben Thomas 1995-2019
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


static int try(state *S, char *file, UWORD address)
{
    int fd = open(file, O_RDONLY);
    int ret;
    if (fd == -1) {
        printf("Could not open file %s\n", file);
        ret = 1; // Expected error codes are all negative
    } else {
        ret = load_object(S, address, fd);
        (void)close(fd); // FIXME: check return value
    }

    printf("load_object(\"%s\", 0) returns %d", file, ret);
    return ret;
}

static char *obj_name(state *S, const char *prefix, const char *file, bool use_endism, unsigned _word_size)
{
    char *suffix = NULL;
    char *endism = NULL;
    if (use_endism)
        endism = xasprintf("-%s", S->ENDISM == 0 ? "le" : "be");
    if (_word_size != 0)
        suffix = xasprintf("-%u", _word_size);
    char *name = xasprintf("%s/%s%s%s", prefix, file, endism ? endism : "", suffix ? suffix : "");
    free(endism);
    free(suffix);
    return name;
}

int main(int argc, char *argv[])
{
    char *src_dir = argv[1];
    char *build_dir = argv[2];

    if (argc != 3) {
        printf("Usage: load_object SOURCE-DIRECTORY BUILD-DIRECTORY\n");
        exit(1);
    }

    state *S = init_default_stacks(256);

    const char *bad_files[] = {
        "badobj1", "badobj2", "badobj3", "badobj4" };
    static int error_code[] = { -2, -2, -1, -3 };
    for (size_t i = 0; i < sizeof(bad_files) / sizeof(bad_files[0]); i++) {
        char *s = obj_name(S, src_dir, bad_files[i], false, word_size);
        int res = try(S, s, 0);
        free(s);
        printf(" should be %d\n", error_code[i]);
        if (res != error_code[i]) {
            printf("Error in load_object() tests: file %s\n", bad_files[i]);
            exit(1);
        }
    }

    const char *good_files[] = {
        "testobj1", "testobj2" };
    for (size_t i = 0; i < sizeof(good_files) / sizeof(good_files[0]); i++) {
        char *s = obj_name(S, src_dir, good_files[i], true, word_size);
        WORD c;
        int res = try(S, s, 0);
        free(s);
        printf(" should be %d\n", 0);
        printf("Word 0 of memory is %"PRI_XWORD"; should be 1020304\n", (UWORD)(load_word(S, 0, &c), c));
        if ((load_word(S, 0, &c), c) != 0x1020304) {
            printf("Error in load_object() tests: file %s\n", good_files[i]);
            exit(1);
        }
        if (res != 0) {
            printf("Error in load_object() tests: file %s\n", good_files[i]);
            exit(1);
        }
        memset(S->memory, 0, S->MEMORY); // Zero memory for next test
    }

    const char *number_files[] = {
        "numbers.obj",
    };
    // FIXME: Generate a single list of numbers for here, numbers.txt and numbers.c
    const WORD correct[][8] =
        {
         {-257, 12345678},
        };
    for (size_t i = 0; i < sizeof(number_files) / sizeof(number_files[0]); i++) {
        char *s = obj_name(S, build_dir, number_files[i], false, 0);
        int res = try(S, s, 0);
        free(s);
        printf(" should be %d\n", 0);
        if (res != 0) {
            printf("Error in load_object() tests: file %s\n", number_files[i]);
            exit(1);
        }
        if (run(S) != 42) {
            printf("Error in load_object() tests: file %s\n", number_files[i]);
            exit(1);
        }
        show_data_stack(S);
        char *correct_stack = xasprint_array(correct[i], ZERO);
        printf("Correct stack: %s\n", correct_stack);
        if (strcmp(correct_stack, val_data_stack(S))) {
            printf("Error in arithmetic tests: PC = %"PRI_UWORD"\n", S->PC);
            exit(1);
        }
        free(correct_stack);
        memset(S->memory, 0, S->MEMORY); // Zero memory for next test
    }

    // Check we get an error trying to load an object file of the wrong
    // WORD_SIZE.
    {
        assert(word_size == 4 || word_size == 8);
        unsigned wrong_word_size = word_size == 4 ? 8 : 4;
        char *s = obj_name(S, src_dir, good_files[0], true, wrong_word_size);
        int res = try(S, s, 0), incorrect_word_size_res = -5;
        free(s);
        printf(" should be %d\n", incorrect_word_size_res);
        if (res != incorrect_word_size_res) {
            printf("Error in load_object() tests: file %s\n", good_files[0]);
            exit(1);
        }
    }

    destroy(S);

    printf("load_object() tests ran OK\n");
    return 0;
}
