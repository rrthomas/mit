// Test load_object().
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


static int try(char *file, UWORD address)
{
    FILE *fp = fopen(file, "r");
    int ret = load_object(fp, address);

    printf("load_object(\"%s\", 0) returns %d", file, ret);
    fclose(fp);

    return ret;
}

static char *obj_name(const char *prefix, const char *file, unsigned word_size)
{
    return xasprintf("%s/%s-%u", prefix, file, word_size);
}

int main(int argc, char *argv[])
{
    char *prefix = argv[1];

    if (argc != 2) {
        printf("Usage: load_object DIRECTORY\n");
        exit(1);
    }

    size_t size = 256;
    WORD *memory = (WORD *)calloc(256, WORD_SIZE);
    init(memory, size);

    const char *bad_files[] = {
        "badobj1", "badobj2", "badobj3", "badobj4" };
    static int error_code[] = { -2, -2, -1, -3 };
    for (size_t i = 0; i < sizeof(bad_files) / sizeof(bad_files[0]); i++) {
        char *s = obj_name(prefix, bad_files[i], WORD_SIZE);
        int res = try(s, 0);
        free(s);
        printf(" should be %d\n", error_code[i]);
        if (res != error_code[i]) {
            printf("Error in load_object() tests: file %s\n", bad_files[i]);
            exit(1);
        }
    }

    const char *good_files[] = {
        "testobj1", "testobj2", "testobj3" };
    for (size_t i = 0; i < sizeof(good_files) / sizeof(good_files[0]); i++) {
        char *s = obj_name(prefix, good_files[i], WORD_SIZE);
        WORD c;
        int res = try(s, 0);
        free(s);
        printf(" should be %d\n", 0);
        printf("Word 0 of memory is %"PRI_XWORD"; should be 1020304\n", (UWORD)(load_word(0, &c), c));
        if ((load_word(0, &c), c) != 0x1020304) {
            printf("Error in load_object() tests: file %s\n", good_files[i]);
            exit(1);
        }
        if (res != 0) {
            printf("Error in load_object() tests: file %s\n", good_files[i]);
            exit(1);
        }
        memset(memory, 0, MEMORY); // Zero memory for next test
    }

    // Check we get an error trying to load an object file of the wrong
    // WORD_SIZE.
    {
#if WORD_SIZE == 4
#define WRONG_WORD_SIZE 8
#elif WORD_SIZE == 8
#define WRONG_WORD_SIZE 4
#else
#error "WORD_SIZE is not 4 or 8!"
#endif
        char *s = obj_name(prefix, good_files[0], WRONG_WORD_SIZE);
        int res = try(s, 0), incorrect_word_size_res = -4;
        free(s);
        printf(" should be %d\n", incorrect_word_size_res);
        if (res != incorrect_word_size_res) {
            printf("Error in load_object() tests: file %s\n", good_files[0]);
            exit(1);
        }
    }

    free(memory);

    printf("load_object() tests ran OK\n");
    return 0;
}
