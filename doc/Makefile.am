# Docs Makefile.am
#
# (c) Reuben Thomas 2011-2018
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

LATEX_SRCS = \
	$(srcdir)/bibtex/bib/rrt.bib \
	$(srcdir)/bibtex/bib/vm.bib \
	$(srcdir)/bibtex/bib/ertl.bib

LATEX_PDFS = \
	@PACKAGE@.pdf \
	c@PACKAGE@.pdf

if HAVE_LATEXMK
dist_doc_DATA = $(LATEX_PDFS)
endif


all: pdf

pdf-local: $(LATEX_PDFS)

MAINTAINERCLEANFILES = $(LATEX_PDFS)

clean-local:
	$(LATEXMK) -r $(srcdir)/latexmkrc -C -f $(LATEX_SRCS) \
		$(builddir)/@PACKAGE@.tex $(builddir)/c@PACKAGE@.tex

EXTRA_DIST = $(LATEX_SRCS) $(LATEX_PDFS) @PACKAGE@.tex.in c@PACKAGE@.tex.in latexmkrc

# TODO: mv works around a bug in latexmk < 4.54, which sets $out_dir when it
# shouldn't. Remove when we can require latexmk >= 4.54 (Ubuntu 20.04).
.tex.pdf:
	env BIBINPUTS=$(abs_srcdir)/bibtex/bib $(LATEXMK) -r $(abs_srcdir)/latexmkrc -cd -f $< && \
	if test -e `basename $@` -a ! `basename $@` -ef $@; then \
	    mv `basename $@` $@; \
	fi
