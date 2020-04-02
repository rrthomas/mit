# Mit

Maintainer: Reuben Thomas <rrt@sc3d.org>  
https://github.com/rrthomas/mit  

Mit is a simple virtual machine designed for study and experiment. It uses a
byte-stream code designed for efficient execution which is binary portable
between implementations. It has been implemented in C for POSIX systems. Mit
is designed to be embedded in other programs; Python 3 bindings are provided
that demonstrate this ability and provide a convenient REPL and debugger. An
I/O library is implemented; access to native code routines is also possible,
allowing Mit and C programs to call each other.

This package comprises the definition of the Mit virtual machine and an
implementation in ISO C11 using POSIX APIs.

The package is distributed under the MIT/X11 License (see the file
`COPYING`). Note that some files are in the public domain, notably the
specification of Mit; they are marked as such.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.


## Compatibility

Mit should work on any POSIX-1.2001-compatible system. Mit has been
tested on x86_64 GNU/Linux with GNU C.

The Python bindings require [PyYAML](https://pyyaml.org/).

Reports on compatibility, whether positive or negative, are welcomed.


### Building from a release tarball

Perl and help2man are required to build from source. For building from git,
see below.

To build Mit from a release tarball, run

`./configure && make && make check`

See `./configure --help` for build options; note in particular the flag
`--enable-package-suffix`.

For the bibliographies in the documentation to be built correctly, GNU Make
should be used.


### Building Mit from git

The GNU autotools are required: automake, autoconf and libtool.
[Gnulib](https://www.gnu.org/software/gnulib/) is also used, with a
third-party `bootstrap` module; these are installed automatically.

To build from a Git repository, first run `./bootstrap`, then see "Building
from source" above.

To build the PDF documentation, a comprehensive TeX system such as TeXLive
is required. This is only necessary when building from Git, as pre-built
PDFs are supplied in release archives. 


## Use

Run `mit OBJECT-FILE` (see `mit --help` for documentation). To run the
shell, `mit-shell`.


## C API

Include `mit/mit.h` (see this file for its documentation), and link with
`libmit`. In addition, `mit/opcodes.h` contains an enumeration type of
Mit’s instruction set.


## Documentation

The documentation consists of:

* _[The Mit Virtual Machine](doc/mit.pdf)_  
The design of the Mit virtual machine is described. Essential reading
for those programming or implementing the VM.
* The comments in `mit.h`.
* Comments in the Python modules.
* `HACKING.md` contains further information for maintainers.

Mit is based on [Beetle](https://github.com/rrthomas/beetle), which I
developed for my BA dissertation project.


## pForth

[pForth](https://github.com/rrthomas/pforth) is an ANSI Forth compiler that
targets Mit.


## Running Mit object files

The C implementation of Mit allows a hash-bang line to be prepended to an
object file, so that they can be run directly. A suggested line is:

```
#!/usr/bin/env mit
```


## Bugs and comments

Please file bugs, if you can, as [GitHub issues](https://github.com/rrthomas/mit/issues).

The maintainer welcomes comments; please see the top of this file for the email address.
