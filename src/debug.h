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


void ass_action(WORD instr);	// assemble an action
void ass_number(WORD n);	// assemble a number
void ass_native_pointer(void (*pointer)(void));  // assemble a native function pointer
void ass_byte(BYTE byte);	// assemble a literal byte
void start_ass(UWORD addr);	// start assembly, initialising variables
UWORD ass_current(void);	// return address of WORD currently being assembled to
const char *disass(enum instruction_type type, WORD opcode);  // disassemble an instruction
UWORD toass(const char *token);    // convert an action to its opcode

char *val_data_stack(void); // return the current data stack as a string
void show_data_stack(void); // show the current contents of the data stack
void show_return_stack(void);	// show the current contents of the return stack


#endif
