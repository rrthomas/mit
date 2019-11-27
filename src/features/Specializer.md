Building a specialized interpreter
==================================

See `features.am` under `Specializer` for the build targets and commands
used.

Some explanatory notes follow.


The profile
-----------

"mit --profile" runs some code and calculates a profile: a lookup table that
records the number of times certain sequences of instructions were executed.
The profile will be more specific if the interpreter is already specialized
for the code being run.


The labels file
---------------

The script "simulate-jit" reads a profile file and constructs a suitable
control-flow graph for the specialized interpreter.

The script is fast, but it has nonetheless been separated out from the rest
of the procedure, so that it is possible to generate a "_labels.pickle" file
in other ways, if desired, or to distribute them.


The interpreter
---------------

The script "gen-specializer" reads a labels file and writes out a C source
file.


Bootstrapping
-------------

To build mit from scratch, first make a profile file with the contents "[]",
representing no knowledge. Then repeatedly build Mit and and run your code with
"mit --profile". Typically, the first three or four iterations will improve
performance significantly.