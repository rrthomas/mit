// Load and save object files.
//
// (c) SMite authors 1995-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <unistd.h>
#include <string.h>

#include "smite.h"


#define HEADER_LENGTH 8

ptrdiff_t smite_load_object(smite_state *S, smite_UWORD addr, int fd)
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
    smite_UWORD _WORD_BYTES;
    memcpy(header, buf, nread);
    if ((res = read(fd, &header[nread], sizeof(header) - nread)) == -1)
        return -1;
    if (res != (ssize_t)(sizeof(header) - nread) ||
        memcmp(header, PACKAGE_UPPER, sizeof(PACKAGE_UPPER)) ||
        (endism = header[sizeof(PACKAGE_UPPER)]) > 1)
        return -2;
    if (endism != S->ENDISM ||
        (_WORD_BYTES = header[sizeof(PACKAGE_UPPER) + 1]) != WORD_BYTES)
        return -3;

    // Read and check size, and ensure code will fit in memory
    smite_UWORD len = 0;
    if ((res = read(fd, &len, sizeof(len))) == -1)
        return -1;
    if (res != sizeof(len))
        return -2;
    uint8_t *ptr = smite_native_address_of_range(S, addr, len);
    if (ptr == NULL || !smite_is_aligned(addr, smite_SIZE_WORD))
        return -4;

    // Read code
    if ((res = read(fd, ptr, len)) == -1)
        return -1;
    else if (res != (ssize_t)len)
        return -2;

    return (ssize_t)len;
}

int smite_save_object(smite_state *S, smite_UWORD addr, smite_UWORD len, int fd)
{
    uint8_t *ptr = smite_native_address_of_range(S, addr, len);
    if (!smite_is_aligned(addr, smite_SIZE_WORD) || ptr == NULL)
        return -2;

    char hashbang[] = "#!/usr/bin/env smite\n";
    smite_BYTE buf[HEADER_LENGTH] = PACKAGE_UPPER;
    buf[sizeof(PACKAGE_UPPER)] = S->ENDISM;
    buf[sizeof(PACKAGE_UPPER) + 1] = WORD_BYTES;

    if (write(fd, hashbang, sizeof(hashbang) - 1) != sizeof(hashbang) - 1 ||
        write(fd, &buf[0], HEADER_LENGTH) != HEADER_LENGTH ||
        write(fd, &len, sizeof(len)) != sizeof(len) ||
        write(fd, ptr, len) != (ssize_t)len)
        return -1;

    return 0;
}
