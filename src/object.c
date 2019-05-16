// Load and save object files.
//
// (c) Mit authors 1995-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#include "config.h"

#include <unistd.h>
#include <string.h>

#include "mit/mit.h"


#define HEADER_LENGTH 8
#define HEADER_MAGIC "MIT\0\0"

ptrdiff_t mit_load_object(mit_state *S, mit_uword addr, int fd)
{
    if (!is_aligned(addr, MIT_SIZE_WORD))
        return MIT_LOAD_ERROR_UNALIGNED_ADDRESS;

    // Skip any #! header
    char buf[sizeof("#!") - 1];
    ssize_t res;
    if ((res = read(fd, &buf[0], sizeof(buf))) == -1)
        return MIT_LOAD_ERROR_FILE_SYSTEM_ERROR;
    else if (res != (ssize_t)sizeof(buf))
        return MIT_LOAD_ERROR_INVALID_OBJECT_FILE;
    size_t nread = 2;
    if (buf[0] == '#' && buf[1] == '!') {
        char eol[1];
        do {
            res = read(fd, &eol[0], 1);
        } while (res == 1 && eol[0] != '\n');
        if (res == -1)
            return MIT_LOAD_ERROR_FILE_SYSTEM_ERROR;
        nread = 0;
    }

    // Read and check header
    char header[HEADER_LENGTH] = {'\0'};
    mit_uword endism;
    mit_uword file_word_bytes;
    memcpy(header, buf, nread);
    if ((res = read(fd, &header[nread], sizeof(header) - nread)) == -1)
        return MIT_LOAD_ERROR_FILE_SYSTEM_ERROR;
    if (res != (ssize_t)(sizeof(header) - nread) ||
        memcmp(header, HEADER_MAGIC, sizeof(HEADER_MAGIC)) ||
        (endism = header[sizeof(HEADER_MAGIC)]) > 1)
        return MIT_LOAD_ERROR_INVALID_OBJECT_FILE;
    if (endism != MIT_ENDISM ||
        (file_word_bytes = header[sizeof(HEADER_MAGIC) + 1]) != MIT_WORD_BYTES)
        return MIT_LOAD_ERROR_INCOMPATIBLE_OBJECT_FILE;

    // Read and check size, and ensure code will fit in memory
    mit_uword len = 0;
    if ((res = read(fd, &len, sizeof(len))) == -1)
        return MIT_LOAD_ERROR_FILE_SYSTEM_ERROR;
    if (MIT_ENDISM != MIT_HOST_ENDISM)
        len = reverse_endianness(MIT_WORD_BIT, len);
    if (res != sizeof(len))
        return MIT_LOAD_ERROR_INVALID_OBJECT_FILE;
    uint8_t *ptr = mit_native_address_of_range(S, addr, len);
    if (ptr == NULL)
        return MIT_LOAD_ERROR_INVALID_ADDRESS_RANGE;

    // Read code
    if ((res = read(fd, ptr, len)) == -1)
        return MIT_LOAD_ERROR_FILE_SYSTEM_ERROR;
    else if (res != (ssize_t)len)
        return MIT_LOAD_ERROR_INVALID_OBJECT_FILE;

    return (ssize_t)len;
}

int mit_save_object(mit_state *S, mit_uword addr, mit_uword len, int fd)
{
    if (!is_aligned(addr, MIT_SIZE_WORD))
        return MIT_SAVE_ERROR_UNALIGNED_ADDRESS;

    uint8_t *ptr = mit_native_address_of_range(S, addr, len);
    if (ptr == NULL)
        return MIT_SAVE_ERROR_INVALID_ADDRESS_RANGE;

    mit_byte buf[HEADER_LENGTH] = HEADER_MAGIC;
    buf[sizeof(HEADER_MAGIC)] = MIT_ENDISM;
    buf[sizeof(HEADER_MAGIC) + 1] = MIT_WORD_BYTES;

    mit_uword len_save = len;
    if (MIT_ENDISM != MIT_HOST_ENDISM)
        len_save = reverse_endianness(MIT_WORD_BIT, len_save);

    if (write(fd, &buf[0], HEADER_LENGTH) != HEADER_LENGTH ||
        write(fd, &len_save, sizeof(len_save)) != sizeof(len_save) ||
        write(fd, ptr, len) != (ssize_t)len)
        return MIT_SAVE_ERROR_FILE_SYSTEM_ERROR;

    return 0;
}
