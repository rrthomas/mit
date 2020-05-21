// Mit features header file
//
// (c) Mit authors 2019-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_MIT_H
#error "mit/mit.h must be included before this header file"
#endif


#ifndef MIT_FEATURES_H
#define MIT_FEATURES_H

mit_word_t mit_trap(mit_word_t code, mit_word_t * restrict stack, mit_uword_t *stack_depth_ptr);

#endif
