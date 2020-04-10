// Mit features header file
//
// (c) Mit authors 2019-2020
//
// The package is distributed under the MIT/X11 License.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
// RISK.

#ifndef MIT_WORD_BYTES
#error "mit/mit.h must be included before this header file"
#endif


#ifndef MIT_FEATURES
#define MIT_FEATURES

extern int mit_argc;
/* The registered value of `argc`. */
extern char **mit_argv;
/* The registered value of `argv`. */

mit_word mit_extra_instruction(mit_state * restrict S);

mit_word mit_run_specializer(mit_state * restrict S);
/* Like `mit_run_simple`, but (hopefully) faster. */

// N.B. The profiler is per-thread, not per-`mit_state`.
void mit_profile_reset(void);
/* Clears the profile. */
mit_word mit_run_profile(mit_state * restrict S);
/* Like `mit_run_specializer`, but records profiling information. */
int mit_profile_dump(int fd);
/* Dump profiling information to file descriptor `fd`. */

mit_word mit_step_to(mit_state * restrict S, mit_uword *n, mit_uword addr, int auto_NEXT);

#endif
