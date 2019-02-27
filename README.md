# SMite

by Reuben Thomas <rrt@sc3d.org>  
https://github.com/rrthomas/smite  

SMite is a simple virtual machine designed for study and experiment. It uses
a byte-stream code designed for efficient execution which is binary portable
between implementations. It has been implemented in C for POSIX systems.
SMite is designed to be embedded in other programs; Python 3 bindings are
provided that demonstrate this ability and provide a convenient REPL and
debugger. In the C implementation, all memory references are bounds checked.
An I/O library is implemented; access to native code routines is also
possible, allowing SMite and C programs to call each other.

This package comprises the definition of the SMite virtual machine and an
implementation in ISO C99 using POSIX APIs. Detailed documentation is in the
`doc` directory; installation instructions follow. Maintainers should read
`HACKING.md`.

The package is distributed under the GNU Public License version 3, or,
at your option, any later version.

THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
RISK.


## Compatibility

SMite should work on any POSIX-1.2001-compatible system. SMite has been
tested on x86_64 GNU/Linux with GNU C.

Reports on compatibility, whether positive or negative, are welcomed.


### Building from a release tarball

Perl and help2man are required to build from source. For building from git,
see below.

To build SMite from a release tarball, run

`./configure && make && make check`

For the bibliographies in the documentation to be built correctly, GNU Make
should be used.


### Building SMite from git

The GNU autotools are required: automake, autoconf and libtool.
[Gnulib](https://www.gnu.org/software/gnulib/) is also used, with a
third-party `bootstrap` module; these are installed automatically.

To build from a Git repository, first run

```
git submodule update --init --recursive
./bootstrap
```

Then see "Building from source" above.

To build the PDF documentation, a comprehensive TeX system such as TeXLive
is required. This is only necessary when building from Git, as pre-built
PDFs are supplied in release archives. 


## Use

Run `smite OBJECT-FILE` (see `smite --help` for documentation). To run the
shell, `python3 -i -m smite`.


## Documentation

The documentation consists of:

* _[The SMite Virtual Machine](doc/smite.pdf)_  
The design of the SMite virtual machine is described. Essential reading
for those programming or implementing the VM.
* _[An implementation of the SMite virtual machine for POSIX](doc/csmite.pdf)_  
A portable implementation of SMite is described, with instructions for
porting, compiling and running it.

SMite is based on [Beetle](https://github.com/rrthomas/beetle), which I
developed for my BA dissertation project.


## pForth

[pForth](https://github.com/rrthomas/pforth) is an ANSI Forth compiler that
targets SMite.


## Running SMite object files

The C implementation of SMite allows a hash-bang line to be prepended to an object file, so that they can be run directly. A suggested line is:

```
#!/usr/bin/env smite
```

A magic file for the file(1) command is also provided: smite.magic.


## Bugs and comments

Please send bug reports (preferably as [GitHub issues](https://github.com/rrthomas/smite/issues))
and comments. I’m especially interested to know of portability bugs.
