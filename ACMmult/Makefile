#
# LaTeX Makefile
# --------------
#
# Author : s.m.vandenoord@student.utwente.nl (Stefan van den Oord)
# Date   : July 15, 1999
#
# Radically modified by Douglas Eck doug@idsia.ch 2002
# And againt to support pdflatex by default
# Massive amounts of cruft!

# This Makefile is a generic makefile for LaTeX documents. Distribute it
# as you wish, but please don't edit or remove this initial comment.
#


#to make ps file

WEBTARGET=/u/eckdoug/www/papers
TRASHTARGET=/u/eckdoug/trashcan
SHELL=/bin/bash

ifndef LATEX
LATEX=pdflatex
endif

ifndef HTLATEX
HTLATEX=htlatex
endif

ifndef BIBTEX
BIBTEX=bibtex
endif

ifndef CP
CP=cp
endif

ifndef DVIPS
DVIPS=dvips
endif

ifndef GZIP
GZIP=gzip -f
endif

ifndef PS2PDF
PS2PDF=ps2pdf
endif

ifndef TWOUP
TWOUP=nup -2 -f
endif

ifndef MAKEINDEX
MAKEINDEX=makeindex
endif

ifndef MV
MV=mv
endif

FIGURES=$(wildcard *.fig)

FIGUREOBJS=$(FIGURES:.fig=.eps)

TEXFILES=$(wildcard *.tex */*.tex)


YEAR=`basename \`dirname $$PWD\``

#Set the latex target
TGT=`echo $$PWD|tr '/' '\n'|tail -1`
DEFAULT_ACTION=pdf
ifeq ($(wildcard $(TGT).tex),)
	ifeq ($(wildcard $(TGT).lytex),)
	else
		DEFAULT_ACTION=lilypond
	endif	
endif





# Default behavior is to make latex then the ps version. Otherwise you can do make all or make both
test: $(DEFAULT_ACTION) 
all: both 
both: ps pdf 

# Final makes everything and creates final web files with dates
install: pdf ps webfiles

# Disable standard pattern rule:
%.dvi: %.tex

# Do not delete the following targets:
.PRECIOUS: %.aux %.bbl %.eps %.ind


%.aux: %.tex $(FIGUREOBJS) $(TEXFILES)
	@$(LATEX) $*
        # Look for citations. Make sure grep never returns an error code.
	@grep "^\\\\citation" *.aux > .btmp.new || true

        # If the citations are not changed, don't do anything. Otherwise replace
        # the .btmp file to make sure Bibtex will be run.
	@if ( diff .btmp.new .btmp >& /dev/null ); then \
		rm .btmp.new; \
	else \
		mv .btmp.new .btmp; \
	fi

	@if [ -f $*.idx ]; then cp $*.idx .itmp.new; else touch .itmp.new; fi
	@if ( diff .itmp.new .itmp >& /dev/null ); then \
		rm .itmp.new; \
	else \
		mv .itmp.new .itmp; \
	fi

.btmp:


lilypond:
	lilypond-book $(TGT).lytex
	$(MAKE) $(TGT).dvi LATEX=latex;
	$(MAKE) pdffromps


pdffromps:
	$(DVIPS) -t a4 -Ppdf -G0 -o $(TGT).ps $(TGT).dvi
	ps2pdf -dPDFSETTINGS=/prepress $(TGT).ps




%.bbl: $(BIBFILES) .btmp
# Only use BibTeX if \bibliography occurs in the document. In that case,
# run BibTeX and recompile. .btmp is touched to prevent useless making
# next time.
# Overriding this if-statement because nobibliography is often used. .. .
	@if ( grep "^\\\\bibliography{" $*.tex > /dev/null ); then \
		$(BIBTEX) $*; \
		$(LATEX) $*; \
		$(LATEX) $*; \
		touch .rerun; \
	fi
	@touch .btmp

.itmp:

%.ind: .itmp
	@if [ -f $*.idx ]; then \
		$(MAKEINDEX) $*; \
		touch .rerun; \
		touch .itmp; \
	fi

%.eps:%.fig
	@echo Generating figure $@...
	@fig2dev -L ps $< $@



latex:
	$(MAKE) $(TGT).dvi LATEX=$(LATEX); 

pdf: 
	$(MAKE) $(TGT).pdf LATEX=pdflatex;

ps:
	echo "here"
	$(MAKE) $(TGT).dvi LATEX=latex;
	$(MAKE) $(TGT).ps  LATEX=latex;
	$(MAKE) $(TGT).ps.gz LATEX=latex;



latexfigures:
	@for i in $(FIGUREOBJS); do \
		$(MAKE) $$i; \
	done

%.ps: %.dvi
	echo "Ps rule triggered"
	$(DVIPS) -Ppdf -G0 -o $@ $< 


%.dvi: %.aux %.ind %.bbl
# Make sure the dvi-file exists; if not: recompile.
	@if [ ! -f $*.dvi ]; then \
		touch .rerun; \
	fi

	@if [ -f .rerun ]; then \
		rm .rerun; \
		$(LATEX) $*; \
	else \
		$(MAKE) $*.aux; \
	fi

# While references et al. are changed: recompile.
	@while ( grep Rerun $*.log > /dev/null ); do \
		$(LATEX) $*; \
	done

# Touch the figureobjects to prevent making next time
	@if [ -n "$(FIGUREOBJS)" ]; then \
		touch $(FIGUREOBJS); \
		touch $*.aux; \
	fi

	@if [ -f $*.ind ]; then \
		touch $*.ind; \
	fi

# While references et al. are changed: recompile.
	@while ( grep Rerun $*.log > /dev/null ); do \
		$(LATEX) $*; \
	done

# Touch the figureobjects to prevent making next time
	@if [ -n "$(FIGUREOBJS)" ]; then \
		touch $(FIGUREOBJS); \
		touch $*.aux; \
	fi

	@if [ -f $*.ind ]; then \
		touch $*.ind; \
	fi


%.pdf: %.aux %.ind %.bbl
# Make sure the dvi-file exists; if not: recompile.
	@if [ ! -f $*.pdf ]; then \
		touch .rerun; \
	fi

	@if [ -f .rerun ]; then \
		rm .rerun; \
		$(LATEX) $*; \
	else \
		$(MAKE) $*.aux; \
	fi

# While references et al. are changed: recompile.
	@while ( grep Rerun $*.log > /dev/null ); do \
		$(LATEX) $*; \
	done

# Touch the figureobjects to prevent making next time
	@if [ -n "$(FIGUREOBJS)" ]; then \
		touch $(FIGUREOBJS); \
		touch $*.aux; \
	fi

	@if [ -f $*.ind ]; then \
		touch $*.ind; \
	fi

# While references et al. are changed: recompile.
	@while ( grep Rerun $*.log > /dev/null ); do \
		$(LATEX) $*; \
	done

# Touch the figureobjects to prevent making next time
	@if [ -n "$(FIGUREOBJS)" ]; then \
		touch $(FIGUREOBJS); \
		touch $*.aux; \
	fi

	@if [ -f $*.ind ]; then \
		touch $*.ind; \
	fi


%.ps.gz: %.ps
	$(GZIP) $<


webfiles: 
	@$(MV) $(TGT).pdf  $(YEAR)_$(TGT).pdf; 
	@$(MV) $(TGT).ps  $(YEAR)_$(TGT).ps; 
	@$(GZIP) $(YEAR)_$(TGT).ps
	@$(MV) $(YEAR)_$(TGT).pdf $(WEBTARGET) && true; 
	@$(MV) $(YEAR)_$(TGT).ps.gz $(WEBTARGET) && true; 
	@$(RM) $(TGT).aux $(TGT).aux $(TGT).bbl	$(TGT).blg $(TGT).dvi $(TGT).log;
	@echo "Installed $(YEAR)_$(TGT).ps and $(YEAR)_$(TGT).pdf in $(WEBTARGET)";


html: .html

%.html:
	$(HTLATEX) $(TGT) 
	@$(RM) $(TGT).4ct $(TGT).4tc $(TGT).idv	$(TGT).lg $(TGT).xref $(TGT).tmp;



clean: tidy


outputclean:
	@rm -f $(TGT).ps $(TGT).pdf $(TGT).ps.gz 

#tidy leaves behind output files
tidy:
	@rm -f $(TGT).aux $(TGT).bbl $(TGT).blg $(TGT).out $(TGT).log $(TGT).dvi .html .btmp .itmp .rerun lily-*.* missfont.log stdin.log stdin.aux












