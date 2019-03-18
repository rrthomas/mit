// Auxiliary public functions.
// These are undocumented and subject to change.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef SMITE_AUX
#define SMITE_AUX


// Memory

// FIXME: These macros should take ENDISM into account and store the
// quantities on the stack in native order (though perhaps not native
// alignment). Current code is correct for ENDISM=0; need to reverse the
// directions of the loops for ENDISM=1. (Generate unrolled loops from
// Python!)
// Note: One might expect casts to smite_UWORD rather than size_t below. The
// latter avoid warnings when the value `v` is a pointer and sizeof(void *)
// > smite_word_size, but the effect (given unsigned sign extension &
// truncation) is identical.
#define UNCHECKED_LOAD_STACK_TYPE(pos, ty, vp)                          \
    *vp = 0;                                                            \
    for (unsigned i = 0; i < smite_align(sizeof(ty)) / smite_word_size; i++) { \
        smite_WORD w;                                                   \
        UNCHECKED_LOAD_STACK(pos - i, &w);                              \
        *vp = (ty)(((size_t)(*vp) << smite_word_bit) | (smite_UWORD)w); \
    }
#define UNCHECKED_STORE_STACK_TYPE(pos, ty, v)                          \
    for (unsigned i = smite_align(sizeof(ty)) / smite_word_size; i > 0; i--) { \
        UNCHECKED_STORE_STACK(pos - i + 1, (smite_UWORD)((size_t)v & smite_word_mask)); \
        v = (ty)((size_t)v >> smite_word_bit);                          \
    }


#endif