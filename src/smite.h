// Public data structures and interface calls.
// This is the header file to include in programs using SMite.
//
// (c) SMite authors 1994-2019
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef SMITE_SMITE
#define SMITE_SMITE


#include <stddef.h>
#include <stdint.h>
#include <inttypes.h>


// Types and printf formats
#define DEFAULT_WORD_SIZE SIZEOF_SIZE_T
#ifndef WORD_SIZE
#define WORD_SIZE DEFAULT_WORD_SIZE
#endif
typedef uint8_t smite_BYTE;
#if WORD_SIZE == 4
typedef int32_t smite_WORD;
typedef uint32_t smite_UWORD;
#define smite_WORD_MASK UINT32_MAX
#define smite_UWORD_MAX UINT32_MAX
#define smite_WORD_MIN INT32_MIN
#define smite_WORD_MAX INT32_MAX
#define PRI_WORD PRId32
#define PRI_UWORD PRIu32
#define PRI_XWORD "#"PRIx32
#elif WORD_SIZE == 8
typedef int64_t smite_WORD;
typedef uint64_t smite_UWORD;
#define smite_WORD_MASK UINT64_MAX
#define smite_UWORD_MAX UINT64_MAX
#define smite_WORD_MIN INT64_MIN
#define smite_WORD_MAX INT64_MAX
#define PRI_WORD PRId64
#define PRI_UWORD PRIu64
#define PRI_XWORD "#"PRIx64
#else
#error "WORD_SIZE must be 4 or 8!"
#endif
typedef smite_WORD * smite_WORDP;
#define PRI_XWORDP "p"

// Constants
extern const unsigned smite_word_size;
#define smite_BYTE_BIT 8
extern const unsigned smite_byte_bit;
extern const unsigned smite_byte_mask;
#define smite_BYTE_MASK ((1 << smite_BYTE_BIT) - 1)
extern const unsigned smite_word_bit;
#define smite_WORD_BIT (WORD_SIZE * smite_BYTE_BIT)
extern const smite_UWORD smite_word_mask;
extern const smite_UWORD smite_uword_max;
extern const smite_WORD smite_word_min;
extern const smite_WORD smite_word_max;

// VM registers
typedef struct {
#define R(reg, type, utype) type reg;
#define R_RO(reg, type, utype) R(reg, type, utype)
#include "registers.h"
#undef R
#undef R_RO
    smite_WORD *memory;
    int main_argc;
    char **main_argv;
} smite_state;

#define R_RO(reg, type, utype)                  \
    type smite_get_ ## reg(smite_state *S);
#define R(reg, type, utype)                     \
    R_RO(reg, type, utype)                      \
    void smite_set_ ## reg(smite_state *S, type val);
#include "registers.h"
#undef R
#undef R_RO

// Instructions
#define SMITE_INSTRUCTION_BIT 8
#define SMITE_INSTRUCTION_MASK ((1 << SMITE_INSTRUCTION_BIT) - 1)
extern const smite_UWORD smite_instruction_bit;
extern const smite_UWORD smite_instruction_mask;

// Errors
enum {
    SMITE_ERR_OK = 0,
    SMITE_ERR_INVALID_OPCODE = 1,
    SMITE_ERR_STACK_OVERFLOW = 2,
    SMITE_ERR_STACK_READ = 3,
    SMITE_ERR_STACK_WRITE = 4,
    SMITE_ERR_MEMORY_READ = 5,
    SMITE_ERR_MEMORY_WRITE = 6,
    SMITE_ERR_MEMORY_UNALIGNED = 7,
    SMITE_ERR_DIVISION_BY_ZERO = 8,
    SMITE_ERR_HALT = 128,
};


// Utility functions

smite_UWORD smite_align(smite_UWORD addr);
/* Return `addr` aligned to the next word boundary. */

int smite_is_aligned(smite_UWORD addr);
/* Return 1 if `addr` is aligned, or `0` if not.  */

// Inline functions
_GL_ATTRIBUTE_CONST static inline smite_UWORD align(smite_UWORD addr)
{
    return (addr + WORD_SIZE - 1) & -WORD_SIZE;
}

_GL_ATTRIBUTE_CONST static inline int is_aligned(smite_UWORD addr)
{
    return (addr & (WORD_SIZE - 1)) == 0;
}


// Memory access

uint8_t *smite_native_address_of_range(smite_state *S, smite_UWORD addr, smite_UWORD len);
/* Return a host pointer to the VM address `addr`, or `NULL` if any address
   in the range [addr, addr+len] is invalid.
*/

int smite_load_word(smite_state *S, smite_UWORD addr, smite_WORD *val_ptr);
/* Load the word at `addr` into the word pointed to by `val_ptr`.

   Return 0 if OK, or error code if `addr` is invalid or unaligned.
*/

int smite_store_word(smite_state *S, smite_UWORD addr, smite_WORD val);
/* Store the word `val` at virtual address `addr`.

   Return 0 if OK, or error code if `addr` is invalid or unaligned.
*/

int smite_load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *val_ptr);
/* Load the byte at `addr` into the byte pointed to by `val_ptr`.

   Return 0 if OK, or error code if `addr` is invalid.
*/

int smite_store_byte(smite_state *S, smite_UWORD addr, smite_BYTE val);
/* Store the byte `val` at virtual address `addr`.

   Return 0 if OK, or error code if `addr` is invalid.
*/

// Inline functions
_GL_ATTRIBUTE_PURE static inline uint8_t *native_address_of_range(smite_state *S, smite_UWORD addr, smite_UWORD len)
{
    if (addr >= S->MEMORY || len > S->MEMORY - addr)
        return NULL;
    return ((uint8_t *)(S->memory)) + addr;
}

static inline int load_word(smite_state *S, smite_UWORD addr, smite_WORD *val_ptr)
{
    if (addr >= S->MEMORY) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_READ;
    }
    if (!is_aligned(addr)) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_UNALIGNED;
    }

    *val_ptr = S->memory[addr / WORD_SIZE];
    return SMITE_ERR_OK;
}

static inline int store_word(smite_state *S, smite_UWORD addr, smite_WORD val)
{
    if (addr >= S->MEMORY) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_WRITE;
    }
    if (!is_aligned(addr)) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_UNALIGNED;
    }

    S->memory[addr / WORD_SIZE] = val;
    return SMITE_ERR_OK;
}

static inline int load_byte(smite_state *S, smite_UWORD addr, smite_BYTE *val_ptr)
{
    if (addr >= S->MEMORY) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_READ;
    }

    *val_ptr = ((smite_BYTE *)S->memory)[addr];
    return SMITE_ERR_OK;
}

static inline int store_byte(smite_state *S, smite_UWORD addr, smite_BYTE val)
{
    if (addr >= S->MEMORY) {
        S->BAD = addr;
        return SMITE_ERR_MEMORY_WRITE;
    }

    ((smite_BYTE *)S->memory)[addr] = val;
    return SMITE_ERR_OK;
}


// Stack access

int smite_load_stack(smite_state *S, smite_UWORD pos, smite_WORD *val_ptr);
/* Load the word position `pos` on the stack into the word pointed to by
   `val_ptr`.

   Return 0 if OK, or error code if `pos` is invalid.
*/

int smite_store_stack(smite_state *S, smite_UWORD pos, smite_WORD val);
/* Store the word `val` into the word at position `pos` on the stack.

   Return 0 if OK, or error code if `addr` is invalid.
*/

int smite_pop_stack(smite_state *S, smite_WORD *val_ptr);
/* Load the word at position `0` on the stack into the word pointed to by
   `val_ptr`, and decrement `STACK_DEPTH`.

   Return 0 if OK, or error code if position `0` is invalid.
 */

int smite_push_stack(smite_state *S, smite_WORD val);
/* Increment `STACK_DEPTH`, then store the word `val` value at position 0 on
   the stack.

   Return 0 if OK, or error code if `STACK_DEPTH` is greater than or equal
   to `STACK_SIZE`.
*/

// Unchecked macro: UNSAFE!
#define UNCHECKED_STACK(pos)                    \
    (S->S0 + S->STACK_DEPTH - (pos) - 1)

// Inline functions
static inline int load_stack(smite_state *S, smite_UWORD pos, smite_WORD *vp)
{
    if (pos >= S->STACK_DEPTH) {
        S->BAD = pos;
        return SMITE_ERR_STACK_READ;
    }

    *vp = *UNCHECKED_STACK(pos);
    return SMITE_ERR_OK;
}

static inline int store_stack(smite_state *S, smite_UWORD pos, smite_WORD v)
{
    if (pos >= S->STACK_DEPTH) {
        S->BAD = pos;
        return SMITE_ERR_STACK_WRITE;
    }

    *UNCHECKED_STACK(pos) = v;
    return SMITE_ERR_OK;
}

static inline int pop_stack(smite_state *S, smite_WORD *v)
{
    int ret = load_stack(S, 0, v);
    S->STACK_DEPTH--;
    return ret;
}

static inline int push_stack(smite_state *S, smite_WORD v)
{
    if (S->STACK_DEPTH >= S->STACK_SIZE) {
        S->BAD = S->STACK_SIZE;
        return SMITE_ERR_STACK_OVERFLOW;
    }

    (S->STACK_DEPTH)++;
    return store_stack(S, 0, v);
}


// VM instantiation and control

smite_state *smite_init(size_t memory_size, size_t stack_size);
/* Create and initialize a virtual machine state.

   - memory_size - number of words of memory required
   - stack_size - number of words of stack space required

   Return a pointer to a new state, or `NULL` if memory cannot be
   allocated, or if any requested size is larger than `smite_UWORD_MAX`.

   The memory and stack are zeroed, and the registers are initialized as per
   the spec.
*/

int smite_realloc_memory(smite_state *S, smite_UWORD memory_size);
/* Resize the memory of a state.

   - state - the state to change
   - memory_size - number of words of memory required

   Return 0 on success, or -1 if the requested memory cannot be allocated.

   Any new memory is zeroed.
*/

int smite_realloc_stack(smite_state *S, smite_UWORD stack_size);
/* Resize the stack of a state.

   - state - the state to change
   - stack_size - number of words of stack required

   Return 0 on success, or -1 if the requested memory cannot be allocated.

   Any new memory is zeroed.
*/

void smite_destroy(smite_state *S);
/* Destroy the given state, deallocating its memory. */

smite_WORD smite_run(smite_state *S);
/* Start the execution cycle in the given state as described in the spec.
   If an error is raised, the code is returned.
*/

smite_WORD smite_single_step(smite_state *S);
/* Execute a single pass of the execution cycle in the given state.
   Return 128 if execution completes without error, or the error code.
*/

ptrdiff_t smite_load_object(smite_state *S, smite_UWORD addr, int fd);
/* Load an object file into a state.

   - state - the state to load into
   - addr - the address at which to load the object file
   - fd - the file descriptor to load from

   Return the number of bytes of code loaded, or one of the following
   errors:

   -1: error reading the object file
   -2: module is invalid
   -3: current implementation is incompatible with the module (for example,
       the word size or `ENDISM` is incompatible)
   -4: the code will not fit into memory at the address given, or the
       address is out of range or unaligned.

   As an extension to the specification, if an object file starts with the
   ASCII bytes `#!`, then it is assumed to be the start of a UNIX-style
   “hash bang” line, and the file contents up to and including the first
   newline character is ignored.
*/

int smite_save_object(smite_state *S, smite_UWORD addr, smite_UWORD len, int fd);
/* Save some memory as an object file.

   - state - the state to save from
   - addr, len - the area of memory to save
   - fd - the file descriptor to save to

   Return 0 on success, or one of the following errors:

   -1: error writing the object file
   -2: `addr` or `len` is invalid
*/

int smite_register_args(smite_state *S, int argc, char *argv[]);
/* Register command-line arguments in the given state, which can be
   retrieved using the `ARGC` and `ARG` functions of the `LIBC` extra
   instruction (see `smite_core/ext.py`).

   - state - the state in which to register the arguments
   - argc, argv - as for `main`.

    Return 0.
*/

#if HAVE_ARITHMETIC_RSHIFT
#define ARSHIFT(n, p) \
    ((smite_WORD)(n) >> (p))
#else
#define ARSHIFT(n, p) \
    (((n) >> (p)) | ((smite_UWORD)(-((smite_WORD)(n) < 0)) << (smite_word_bit - (p))))
#endif
/* Arithmetic right shift `n` by `p` places (the behaviour of >> on signed
   quantities is implementation-defined in C99).
*/

int smite_ext(smite_state *S);
/* Implement the EXT instruction. */

#endif
