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

#include <stdio.h>
#include <string.h>
#include <assert.h>

#include "public.h"
#include "aux.h"


int load_object(FILE *file, UWORD address)
{
    if (!IS_ALIGNED(address))
        return -1;

    size_t len = strlen(PACKAGE_UPPER);
    char magic[MAGIC_LENGTH];
    assert(len <= sizeof(magic));

    // Skip any #! header
    if (fread(&magic[0], 1, 2, file) != 2)
        return -3;
    size_t read = 2;
    if (magic[0] == '#' && magic[1] == '!') {
        while (getc(file) != '\n')
            ;
        read = 0;
    }

    if (fread(&magic[read], 1, sizeof(magic) - read, file) != sizeof(magic) - read)
        return -3;
    if (strncmp(magic, PACKAGE_UPPER, sizeof(magic)))
        return -2;
    for (size_t i = len; i < MAGIC_LENGTH; i++)
        if (magic[i] != '\0')
            return -2;

    WORD endism;
    if (decode_instruction_file(file, &endism) != INSTRUCTION_NUMBER)
        return -2;
    if (endism != 0 && endism != 1)
        return -2;
    int reversed = endism ^ ENDISM;

    WORD word_size;
    if (decode_instruction_file(file, &word_size) != INSTRUCTION_NUMBER)
        return -2;
    if (word_size != WORD_SIZE)
        return -4;

    UWORD length = 0;
    if (decode_instruction_file(file, (WORD *)&length) != INSTRUCTION_NUMBER)
        return -2;

    uint8_t *ptr = native_address_range_in_one_area(address, length, true);
    if (ptr == NULL)
        return -1;

    if (fread(ptr, 1, length, file) != length)
        return -3;

    if (reversed)
        reverse(address, length);

    return 0;
}
