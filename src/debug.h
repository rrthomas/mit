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


int byte_size(WORD v); // return number of significant bytes in a WORD quantity

void ass(BYTE instr);	// assemble an instruction
void lit(WORD literal);	// assemble a word literal
void plit(void (*literal)(void));  // assemble a machine-dependent function pointer literal,
                                   // including the relevant LITERAL instructions
void start_ass(UWORD addr);	// start assembly, initialising variables
UWORD ass_current(void);	// return address of WORD currently being assembled to
const char *disass(BYTE opcode);  // disassemble an instruction
BYTE toass(const char *token);    // convert a instruction to its opcode

char *val_data_stack(void); // return the current data stack as a string
void show_data_stack(void); // show the current contents of the data stack
void show_return_stack(void);	// show the current contents of the return stack


#endif
