// The interface call load_object(file, address) : integer.
//
// (c) Reuben Thomas 1995-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include "external_syms.h"

#include <assert.h>
#include <unistd.h>
#include <string.h>

#include "public.h"
#include "aux.h"


int load_object(state *S, int fd, UWORD address)
{
    if (!IS_ALIGNED(address))
        return -1;

    size_t len = strlen(PACKAGE_UPPER);
    char magic[MAGIC_LENGTH];
    assert(len <= sizeof(magic));

    // Skip any #! header
    if (read(fd, &magic[0], 2) != 2)
        return -3;
    size_t nread = 2;
    if (magic[0] == '#' && magic[1] == '!') {
        char eol[1];
        while (read(fd, &eol[0], 1) == 1 && eol[0] != '\n')
            ;
        nread = 0;
    }

    if (read(fd, &magic[nread], sizeof(magic) - nread) != (ssize_t)(sizeof(magic) - nread))
        return -3;
    if (strncmp(magic, PACKAGE_UPPER, sizeof(magic)))
        return -2;
    for (size_t i = len; i < MAGIC_LENGTH; i++)
        if (magic[i] != '\0')
            return -2;

    UWORD endism;
    if (decode_instruction_file(fd, (WORD *)(&endism)) != INSTRUCTION_NUMBER ||
        endism > 1)
        return -2;
    if (endism != S->ENDISM)
        return -4;

    WORD _word_size;
    if (decode_instruction_file(fd, &_word_size) != INSTRUCTION_NUMBER)
        return -2;
    if (_word_size != WORD_SIZE)
        return -5;

    UWORD length = 0;
    if (decode_instruction_file(fd, (WORD *)&length) != INSTRUCTION_NUMBER)
        return -2;

    uint8_t *ptr = native_address_range_in_one_area(S, address, length, true);
    if (ptr == NULL)
        return -1;

    if (read(fd, ptr, length) != length)
        return -3;

    return 0;
}
