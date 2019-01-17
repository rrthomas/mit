// Test save_object().
//
// (c) Reuben Thomas 1995-2019
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "tests.h"


int correct[] = { -1, -1, 0 };


static int try(state *S, const char *file, UWORD address, UWORD length)
{
    int fd = creat(file, S_IRUSR | S_IWUSR);
    int ret;
    if (fd == -1) {
        printf("Could not open file %s\n", file);
        ret = 1; // Expected error codes are all negative
    } else {
        ret = save_object(S, address, length, fd);
        (void)close(fd); // FIXME: check return value
    }

    printf("save_object(\"%s\", %"PRI_UWORD", %"PRI_XWORD") returns %d", file,
           address, length, ret);
    return ret;
}


int main(void)
{
    int exception = 0;
    UWORD adr[] = { 0, 0, 0 };
    UWORD len[] = { 16, 3000, 16 };

    size_t size = 256;
    state *S = init_default_stacks(size);
    adr[0] = (size + 1) * WORD_SIZE;
    store_word(S, 0, 0x01020304);
    store_word(S, WORD_SIZE, 0x05060708);

    for (int i = 0; i < 3; i++) {
        int res = try(S, "saveobj", adr[i], len[i]);
        if (i != 2)
          remove("saveobj");
        printf(" should be %d\n", correct[i]);
        if (res != correct[i]) {
            printf("Error in save_object() test %d\n", i + 1);
            exit(1);
        }
    }

    {
        int fd = open("saveobj", O_RDONLY);
        int ret = load_object(S, 4 * WORD_SIZE, fd);

        if (ret) {
            printf("Error in save_object() tests: %d returned by load_object\n", ret);
            exit(1);
        }

        close(fd);
        remove("saveobj");
    }
    for (int i = 0; i < 4; i++) {
        WORD old, new;
        load_word(S, i * WORD_SIZE, &old);
        load_word(S, (i + 4) * WORD_SIZE, &new);
        printf("Word %d of memory is %"PRI_XWORD"; should be %"PRI_XWORD"\n", i,
               (UWORD)new, (UWORD)old);
        if (new != old) {
            printf("Error in save_object() tests: loaded file does not match data "
                   "saved\n");
            exit(1);
        }
    }

    assert(exception == 0);
    destroy(S);
    printf("save_object() tests ran OK\n");
    return 0;
}
