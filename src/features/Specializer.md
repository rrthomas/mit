Building a specialized interpreter
==================================

See `features.am` under `Specializer` for the build targets and commands
used.

Some explanatory notes follow.


The trace
---------

The trace file is a raw binary dump of instruction opcodes, one per byte. An
empty file can be used; this is useful to bootstrap a new instruction
encoding.


The predictor
-------------

The script "gen-predictor" reads a trace file and approximates it by a
predictor: a lookup table that guesses the next instruction based on the
previous instructions. Run it like this:

The script is slow, because it has to replay the whole trace. You may want to
keep a library of predictor files, which are typically small (tens of
kilobytes). It is for this reason that the "gen-predictor" script has been
separated out from the rest of the procedure.


The labels file
---------------

The script "gen-labels" reads a predictor file and constructs a suitable
control-flow graph for the specialized interpreter.

The script is fast, but it has nonetheless been separated out from the rest
of the procedure, so that it is possible to generate a ".labels_pickle" file
in other ways, if desired, or to distribute them.


The interpreter
---------------

The script "gen-specializer" reads a labels file and writes out a C source
file.
