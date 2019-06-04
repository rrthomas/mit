Building a specialized interpreter
==================================

See `features.am` under `Specializer` for the build targets and commands
used.

Some explanatory notes follow.


The predictor
-------------

The script "gen-predictor" runs some code and calculates a predictor: a
lookup table that guesses the next instruction based on the previous
instructions.


The labels file
---------------

The script "gen-labels" reads a predictor file and constructs a suitable
control-flow graph for the specialized interpreter.

The script is fast, but it has nonetheless been separated out from the rest
of the procedure, so that it is possible to generate a "_labels.pickle" file
in other ways, if desired, or to distribute them.


The interpreter
---------------

The script "gen-specializer" reads a labels file and writes out a C source
file.
