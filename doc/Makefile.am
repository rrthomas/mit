# Docs Makefile.am
#
# (c) Mit authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

LATEX_SRCS = \
	$(srcdir)/bibtex/bib/rrt.bib \
	$(srcdir)/bibtex/bib/vm.bib

LATEX_PDFS = \
	mit.pdf

if HAVE_LATEXMK
dist_doc_DATA = $(LATEX_PDFS)
endif


all: pdf

pdf-local: $(LATEX_PDFS)

MAINTAINERCLEANFILES = $(LATEX_PDFS)

clean-local:
	$(LATEXMK) -r $(srcdir)/latexmkrc -c -f $(LATEX_SRCS) $(srcdir)/mit.tex

EXTRA_DIST = $(LATEX_SRCS) $(LATEX_PDFS) mit.tex latexmkrc

# TODO: mv works around a bug in latexmk < 4.54, which sets $out_dir when it
# shouldn't. Remove when we can require latexmk >= 4.54 (Ubuntu 20.04).
.tex.pdf:
	env BIBINPUTS=$(abs_srcdir)/bibtex/bib $(LATEXMK) -r $(abs_srcdir)/latexmkrc -cd -f $< && \
	if test -e `basename $@` -a ! `basename $@` -ef $@; then \
	    mv `basename $@` $@; \
	fi
