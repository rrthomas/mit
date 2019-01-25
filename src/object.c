// The interface call load_object(file, address) : integer.
//
// (c) Reuben Thomas 1995-2019
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#include "config.h"

#include <assert.h>
#include <unistd.h>
#include <string.h>

#include "smite.h"
#include "aux.h"


ptrdiff_t smite_load_object(smite_state *S, smite_UWORD address, int fd)
{
    if (!smite_is_aligned(address))
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

    smite_UWORD endism;
    if (smite_decode_instruction_file(fd, (smite_WORD *)(&endism)) != INSTRUCTION_NUMBER ||
        endism > 1)
        return -2;
    if (endism != S->ENDISM)
        return -4;

    smite_UWORD _smite_word_size;
    if (smite_decode_instruction_file(fd, (smite_WORD *)&_smite_word_size) != INSTRUCTION_NUMBER)
        return -2;
    if (_smite_word_size != smite_word_size)
        return -5;

    smite_UWORD length = 0;
    if (smite_decode_instruction_file(fd, (smite_WORD *)&length) != INSTRUCTION_NUMBER)
        return -2;

    uint8_t *ptr = smite_native_address_of_range(S, address, length);
    if (ptr == NULL)
        return -1;

    if (read(fd, ptr, length) != (ssize_t)length)
        return -3;

    return (ssize_t)length;
}

int smite_save_object(smite_state *S, smite_UWORD address, smite_UWORD length, int fd)
{
    uint8_t *ptr = smite_native_address_of_range(S, address, length);
    if (!smite_is_aligned(address) || ptr == NULL)
        return -1;

    char hashbang[] = "#!/usr/bin/env smite\n";
    smite_BYTE buf[MAGIC_LENGTH] = PACKAGE_UPPER;

    if (write(fd, hashbang, sizeof(hashbang) - 1) != sizeof(hashbang) - 1 ||
        write(fd, &buf[0], MAGIC_LENGTH) != MAGIC_LENGTH ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, S->ENDISM) < 0 ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, smite_word_size) < 0 ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, length) < 0 ||
        write(fd, ptr, length) != (ssize_t)length)
        return -2;

    return 0;
}
