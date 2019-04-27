# Specializer Makefile.am fragment
#
# (c) SMite authors 2011-2019
#
# The package is distributed under the MIT/X11 License.
#
# THIS PROGRAM IS PROVIDED AS IS, WITH NO WARRANTY. USE IS AT THE USER’S
# RISK.

SPECIALIZER_SRCDIR = $(top_srcdir)/feature/30-specializer

nodist_LIB_SRCS += $(SPECIALIZER_SRCDIR)/instructions.c
pkginclude_HEADERS += specializer.h

$(SPECIALIZER_SRCDIR)/instructions.predictor_pickle: smite_core/instruction.py smite_core/vm_data.py $(SPECIALIZER_SRCDIR)/gen-predictor $(SPECIALIZER_SRCDIR)/instructions.trace $(SPECIALIZER_SRCDIR)/specializer.py
	$(PYTHON_WITH_PATH) $(SPECIALIZER_SRCDIR)/gen-predictor $(SPECIALIZER_SRCDIR)/instructions.trace $@

$(SPECIALIZER_SRCDIR)/instructions.labels_pickle: smite_core/instruction.py smite_core/vm_data.py $(SPECIALIZER_SRCDIR)/instructions.predictor_pickle $(SPECIALIZER_SRCDIR)/gen-labels $(SPECIALIZER_SRCDIR)/specializer.py
	$(PYTHON_WITH_PATH) $(SPECIALIZER_SRCDIR)/gen-labels $(SPECIALIZER_SRCDIR)/instructions.predictor_pickle $@

$(SPECIALIZER_SRCDIR)/instructions.c: smite_core/instruction.py smite_core/vm_data.py smite_core/type_sizes.py smite_core/instruction_gen.py $(SPECIALIZER_SRCDIR)/gen-instructions $(SPECIALIZER_SRCDIR)/instructions.labels_pickle
	$(PYTHON_WITH_PATH) $(SPECIALIZER_SRCDIR)/gen-instructions $(SPECIALIZER_SRCDIR)/instructions.labels_pickle > $(SPECIALIZER_SRCDIR)/instructions.c || ( rm -f $(SPECIALIZER_SRCDIR)/instructions.c; exit 1 )

EXTRA_DIST += \
	$(SPECIALIZER_SRCDIR)/specializer.py \
	$(SPECIALIZER_SRCDIR)/gen-labels \
	$(SPECIALIZER_SRCDIR)/gen-predictor \
	$(SPECIALIZER_SRCDIR)/gen-instructions \
	$(SPECIALIZER_SRCDIR)/instructions.trace

DISTCLEANFILES += \
	$(SPECIALIZER_SRCDIR)/instructions.predictor_pickle $(SPECIALIZER_SRCDIR)/instructions.labels_pickle $(SPECIALIZER_SRCDIR)/instructions.c

