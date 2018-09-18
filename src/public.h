// Public data structures and interface calls specified in the VM definition.
// This is the header file to include in programs using an embedded VM.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef PACKAGE_UPPER_PACKAGE_UPPER
#define PACKAGE_UPPER_PACKAGE_UPPER


#include "config.h"

#include <stdio.h>      // for the FILE type
#include <stdbool.h>
#include <stdint.h>
#include <limits.h>


// Basic types
typedef uint8_t BYTE;
typedef int32_t WORD;
typedef uint32_t UWORD;
typedef uint64_t DUWORD;
#define BYTE_BIT 8
#define BYTE_MASK ((1 << BYTE_BIT) - 1)
#undef WORD_BIT // FIXME: prefix this and other symbols
#define WORD_BIT (sizeof(WORD_W) * BYTE_BIT)
#define WORD_MAX (UINT32_MAX)
#define WORD_MASK WORD_MAX

// VM registers

// ENDISM is fixed at compile-time, which seems reasonable, as
// machines rarely change endianness while switched on!
#ifdef WORDS_BIGENDIAN
#define ENDISM ((BYTE)1)
#else
#define ENDISM ((BYTE)0)
#endif

extern UWORD PC;
extern BYTE I;
extern WORD A;
extern UWORD MEMORY;
extern UWORD SP, RP;
extern UWORD S0, R0;
extern UWORD HASHS, HASHR;
extern UWORD THROW;
extern UWORD BAD;
extern UWORD NOT_ADDRESS;

// Memory access

// Return value is 0 if OK, or exception code for invalid or unaligned address
int load_word(UWORD addr, WORD *value);
int store_word(UWORD addr, WORD value);
int load_byte(UWORD addr, BYTE *value);
int store_byte(UWORD addr, BYTE value);

int pre_dma(UWORD from, UWORD to, bool write);
int post_dma(UWORD from, UWORD to);

// Memory mapping
UWORD mem_here(void);
UWORD mem_allot(void *p, size_t n, bool writable);
UWORD mem_align(void);

// Interface calls
uint8_t *native_address(UWORD addr, bool writable);
WORD run(void);
WORD single_step(void);
int load_object(FILE *file, UWORD address);

// Additional implementation-specific routines, macros, types and quantities
int init(WORD *c_array, size_t size);
int register_args(int argc, char *argv[]);

#define PACKAGE_UPPER_TRUE WORD_MASK            // VM TRUE flag
#define PACKAGE_UPPER_FALSE ((WORD)0)           // VM FALSE flag

#define WORD_W 4    // the width of a word in bytes
#define POINTER_W (sizeof(void *) / WORD_W)   // the width of a machine pointer in words

// A union to allow storage of machine pointers in VM memory
union _WORD_pointer {
    WORD words[POINTER_W];
    void (*pointer)(void);
};
typedef union _WORD_pointer WORD_pointer;

#endif
