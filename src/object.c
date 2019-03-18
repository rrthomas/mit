// The interface calls load_object(file, address) : integer and
// save_object(file, address, length) : integer.
//
// (c) Reuben Thomas 1995-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <unistd.h>
#include <string.h>

#include "smite.h"
#include "aux.h"


#define HEADER_LENGTH 8

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

    // Read and check header
    char header[HEADER_LENGTH] = {'\0'};
    smite_UWORD endism;
    smite_UWORD _WORD_SIZE;
    memcpy(header, buf, nread);
    if ((res = read(fd, &header[nread], sizeof(header) - nread)) == -1)
        return -1;
    if (res != (ssize_t)(sizeof(header) - nread) ||
        memcmp(header, PACKAGE_UPPER, sizeof(PACKAGE_UPPER)) ||
        (endism = header[sizeof(PACKAGE_UPPER)]) > 1)
        return -2;
    if (endism != S->ENDISM ||
        (_WORD_SIZE = header[sizeof(PACKAGE_UPPER) + 1]) != WORD_SIZE)
        return -3;

    // Read and check size, and ensure code will fit in memory
    smite_UWORD length = 0;
    if ((res = read(fd, &length, sizeof(length))) == -1)
        return -1;
    if (res != sizeof(length))
        return -2;
    uint8_t *ptr = smite_native_address_of_range(S, address, length);
    if (ptr == NULL || !smite_is_aligned(address))
        return -4;

    // Read code
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
    smite_BYTE buf[HEADER_LENGTH] = PACKAGE_UPPER;
    buf[sizeof(PACKAGE_UPPER)] = S->ENDISM;
    buf[sizeof(PACKAGE_UPPER) + 1] = WORD_SIZE;

    if (write(fd, hashbang, sizeof(hashbang) - 1) != sizeof(hashbang) - 1 ||
        write(fd, &buf[0], HEADER_LENGTH) != HEADER_LENGTH ||
        write(fd, &length, sizeof(length)) != sizeof(length) ||
        write(fd, ptr, length) != (ssize_t)length)
        return -1;

    return 0;
}
