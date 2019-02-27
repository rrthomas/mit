// The interface calls load_object(file, address) : integer and
// save_object(file, address, length) : integer.
//
// (c) Reuben Thomas 1995-2019
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <assert.h>
#include <unistd.h>
#include <string.h>

#include "smite.h"
#include "aux.h"


ptrdiff_t smite_load_object(smite_state *S, smite_UWORD address, int fd)
{
    // Skip any #! header
    char buf[sizeof("#!") - 1];
    ssize_t res;
    if ((res = read(fd, &buf[0], sizeof(buf))) == -1)
        return -1;
    else if (res != (ssize_t)sizeof(buf))
        return -2;
    size_t nread = 2;
    if (buf[0] == '#' && buf[1] == '!') {
        char eol[1];
        do {
            res = read(fd, &eol[0], 1);
        } while (res == 1 && eol[0] != '\n');
        if (res == -1)
            return -1;
        nread = 0;
    }

    // Read and check magic
    char magic[MAGIC_LENGTH] = "";
    memcpy(magic, buf, nread);
    char correct_magic[MAGIC_LENGTH] = PACKAGE_UPPER;
    assert(strlen(PACKAGE_UPPER) <= sizeof(magic));
    if ((res = read(fd, &magic[nread], sizeof(magic) - nread)) == -1)
        return -1;
    if (res != (ssize_t)(sizeof(magic) - nread) ||
             memcmp(magic, correct_magic, sizeof(magic)))
        return -2;

    // Read and check endism
    smite_UWORD endism;
    if (smite_decode_instruction_file(fd, (smite_WORD *)(&endism)) != INSTRUCTION_NUMBER)
        return -1;
    if (endism > 1)
        return -2;
    else if (endism != S->ENDISM)
        return -3;

    // Read and check word size
    smite_UWORD _smite_word_size;
    ssize_t ty = smite_decode_instruction_file(fd, (smite_WORD *)&_smite_word_size);
    if (ty == -1)
        return -1;
    else if (ty != INSTRUCTION_NUMBER)
        return -2;
    if (_smite_word_size != smite_word_size)
        return -3;

    // Read and check size, and ensure module will fit in memory
    smite_UWORD length = 0;
    ty = smite_decode_instruction_file(fd, (smite_WORD *)&length);
    if (ty == -1)
        return -1;
    if (ty != INSTRUCTION_NUMBER)
        return -2;
    uint8_t *ptr = smite_native_address_of_range(S, address, length);
    if (ptr == NULL || !smite_is_aligned(address))
        return -4;

    // Read module in
    if ((res = read(fd, ptr, length)) == -1)
        return -1;
    else if (res != (ssize_t)length)
        return -2;

    return (ssize_t)length;
}

int smite_save_object(smite_state *S, smite_UWORD address, smite_UWORD length, int fd)
{
    uint8_t *ptr = smite_native_address_of_range(S, address, length);
    if (!smite_is_aligned(address) || ptr == NULL)
        return -2;

    char hashbang[] = "#!/usr/bin/env smite\n";
    smite_BYTE buf[MAGIC_LENGTH] = PACKAGE_UPPER;

    if (write(fd, hashbang, sizeof(hashbang) - 1) != sizeof(hashbang) - 1 ||
        write(fd, &buf[0], MAGIC_LENGTH) != MAGIC_LENGTH ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, S->ENDISM) < 0 ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, smite_word_size) < 0 ||
        smite_encode_instruction_file(fd, INSTRUCTION_NUMBER, length) < 0 ||
        write(fd, ptr, length) != (ssize_t)length)
        return -1;

    return 0;
}
