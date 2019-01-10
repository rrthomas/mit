// VM debugging functions
// These are undocumented and subject to change.
//
// (c) Reuben Thomas 1994-2018
//
// The package is distributed under the GNU Public License version 3, or,
// at your option, any later version.
//
// THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER‘S
// RISK.

#ifndef PACKAGE_UPPER_DEBUG
#define PACKAGE_UPPER_DEBUG


void ass_action(state *S, WORD instr);	// assemble an action
void ass_number(state *S, WORD n);	// assemble a number
void ass_native_pointer(state *S, void *ptr);  // assemble a native pointer
void ass_byte(state *S, BYTE byte);	// assemble a literal byte
void start_ass(state *S, UWORD addr);	// start assembly, initialising variables
UWORD ass_current(state *S);	// return address of WORD currently being assembled to
const char *disass(enum instruction_type type, WORD opcode);  // disassemble an instruction
UWORD toass(const char *token);    // convert an action to its opcode

char *val_data_stack(state *S); // return the current data stack as a string
void show_data_stack(state *S); // show the current contents of the data stack
void show_return_stack(state *S);	// show the current contents of the return stack


#endif
