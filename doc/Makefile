# Makefile for Python documentation
# ---------------------------------
#
# See also the README file.
#
# This is a bit of a mess.  The documents are identified by short names:
#   api -- Python/C API Reference Manual
#   doc -- Documenting Python
#   ext -- Extending and Embedding the Python Interpreter
#   lib -- Library Reference Manual
#   mac -- Macintosh Library Modules
#   ref -- Python Reference Manual
#   tut -- Python Tutorial
#   inst -- Installing Python Modules
#   dist -- Distributing Python Modules
#
# The LaTeX sources for each of these documents are in subdirectories
# with the three-letter designations above as the directory names.
#
# The main target creates HTML for each of the documents.  You can
# also do "make lib" (etc.) to create the HTML versions of individual
# documents.
#
# The document classes and styles are in the texinputs/ directory.
# These define a number of macros that are similar in name and intent
# as macros in Texinfo (e.g. \code{...} and \emph{...}), as well as a
# number of environments for formatting function and data definitions.
# Documentation for the macros is included in "Documenting Python"; see
# http://www.python.org/doc/current/doc/doc.html, or the sources for
# this document in the doc/ directory.
#
# Everything is processed by LaTeX.  See the file `README' for more
# information on the tools needed for processing.
#
# There's a problem with generating the index which has been solved by
# a sed command applied to the index file.  The shell script fix_hack
# does this (the Makefile takes care of calling it).
#
# Additional targets attempt to convert selected LaTeX sources to
# various other formats.  These are generally site specific because
# the tools used are all but universal.  These targets are:
#
#   ps  -- convert all documents from LaTeX to PostScript
#   pdf -- convert all documents from LaTeX to the
#		Portable Document Format
#
# See the README file for more information on these targets.
#
# The formatted output is located in subdirectories.  For PDF and
# PostScript, look in the paper-$(PAPER)/ directory.  For HTML, look in
# the html/ directory.  If you want to fix the GNU info process, look
# in the info/ directory; please send patches to python-docs@python.org.

# This Makefile only includes information on how to perform builds; for
# dependency information, see Makefile.deps.

# Customization -- you *may* have to edit this

# You could set this to a4:
PAPER=a4

# Ideally, you shouldn't need to edit beyond this point

INFODIR=	info
TOOLSDIR=	tools

# This is the *documentation* release, and is used to construct the file
# names of the downloadable tarballs.
RELEASE=0.2

PYTHON=	   python
DVIPS=	   dvips -N0 -t $(PAPER)

MKDVI=	   $(PYTHON) ../tools/mkhowto --paper=$(PAPER) --dvi
MKHTML=	   $(PYTHON) tools/mkhowto --html --about html/myabout.dat \
		--iconserver ../icons --favicon ../icons/pyfav.gif \
		--address $(MYHDLDOCS) --up-link ../Overview.html \
		--up-title "Overview" \
		--dvips-safe
MKPDF=	   $(PYTHON) ../tools/mkhowto -l --paper=$(PAPER) --pdf
MKPS=	   $(PYTHON) ../tools/mkhowto --paper=$(PAPER) --ps

BUILDINDEX=$(TOOLSDIR)/buildindex.py

MYHDLDOCS="<i><a href=\"about.html\">About this document</a></i>"
HTMLBASE=  file:`pwd`

# The emacs binary used to build the info docs. GNU Emacs 21 is required.
EMACS=     emacs

# The end of this should reflect the major/minor version numbers of
# the release:
WHATSNEW=whatsnew23

# what's what
MANDVIFILES=	paper-$(PAPER)/MyHDL.dvi

HOWTODVIFILES=	paper-$(PAPER)/whatsnew03.dvi 

MANPDFFILES=	paper-$(PAPER)/MyHDL.pdf 

HOWTOPDFFILES=	paper-$(PAPER)/whatsnew03.pdf 

MANPSFILES=	paper-$(PAPER)/MyHDL.ps 

HOWTOPSFILES=	paper-$(PAPER)/whatsnew03.ps 

DVIFILES=	$(MANDVIFILES) $(HOWTODVIFILES)
PDFFILES=	$(MANPDFFILES) $(HOWTOPDFFILES)
PSFILES=	$(MANPSFILES) $(HOWTOPSFILES)

HTMLCSSFILES=html/manual/MyHDL.css 

ALLCSSFILES=$(HTMLCSSFILES) 

INDEXFILES=html/manual/MyHDL.html \
           html/whatsnew03/whatsnew03.html

ALLHTMLFILES=$(INDEXFILES)

COMMONPERL= perl/manual.perl perl/python.perl perl/l2hinit.perl

include Makefile.deps

# These must be declared phony since there
# are directories with matching names:
.PHONY: manual 
.PHONY: html info 


# Main target
default:	all
all:		html ps pdf 

dvi:	$(DVIFILES)
pdf:	$(PDFFILES)
ps:	$(PSFILES)

world:	ps pdf html distfiles


# Rules to build PostScript and PDF formats
.SUFFIXES: .pdf .dvi .ps

#.dvi.ps:
#	$(DVIPS) -o $@ $<

.pdf.ps:
	pdf2ps $< $@


# Targets for each document:



# MyHDL Manual
paper-$(PAPER)/MyHDL.dvi: $(MANUALFILES)
	cd paper-$(PAPER) && $(MKDVI) ../manual/MyHDL.tex

paper-$(PAPER)/MyHDL.pdf: $(MANUALFILES)
	cd paper-$(PAPER) && $(MKPDF) ../manual/MyHDL.tex


# What's new
# in 0.3
paper-$(PAPER)/whatsnew03.dvi: whatsnew03/whatsnew03.tex
	cd paper-$(PAPER) && $(MKDVI) ../whatsnew03/whatsnew03.tex

paper-$(PAPER)/whatsnew03.pdf: whatsnew03/whatsnew03.tex
	cd paper-$(PAPER) && $(MKPDF) ../whatsnew03/whatsnew03.tex

# The remaining part of the Makefile is concerned with various
# conversions, as described above.  See also the README file.

info:
	cd $(INFODIR) && $(MAKE) EMACS=$(EMACS)

# Targets to convert the manuals to HTML using Nikos Drakos' LaTeX to
# HTML converter.  For more info on this program, see
# <URL:http://cbl.leeds.ac.uk/nikos/tex2html/doc/latex2html/latex2html.html>.

# Note that LaTeX2HTML inserts references to an icons directory in
# each page that it generates.  I have placed a copy of this directory
# in the distribution to simplify the process of creating a
# self-contained HTML distribution; for this purpose I have also added
# a (trivial) index.html.  Change the definition of $ICONSERVER in
# perl/l2hinit.perl to use a different location for the icons directory.

# If you have the standard LaTeX2HTML icons installed, the versions shipped
# with this documentation should be stored in a separate directory and used
# instead.  The standard set does *not* include all the icons used in the
# Python documentation.

$(ALLCSSFILES): html/style.css
	cp $< $@

$(INDEXFILES): $(COMMONPERL) html/about.dat tools/node2label.pl

html/acks.html: ACKS $(TOOLSDIR)/support.py $(TOOLSDIR)/mkackshtml
	$(PYTHON) $(TOOLSDIR)/mkackshtml --address $(PYTHONDOCS) \
		--favicon icons/pyfav.gif \
		--output html/acks.html <ACKS


# html/index.html is dependent on $(INDEXFILES) since we want the date
# on the front index to be updated whenever any of the child documents
# are updated and boilerplate.tex uses \today as the date.  The index
# files are not used to actually generate content.

BOILERPLATE=texinputs/boilerplate.tex
html/index.html: $(INDEXFILES)
html/index.html: html/index.html.in $(BOILERPLATE) tools/rewrite.py
	$(PYTHON) tools/rewrite.py $(BOILERPLATE) \
		RELEASE=$(RELEASE) WHATSNEW=$(WHATSNEW) \
		<$< >$@

html/modindex.html: 
	touch html/modindex.html

html:	$(ALLHTMLFILES) $(HTMLCSSFILES)




manual: html/manual/MyHDL.html html/manual/MyHDL.css
html/manual/MyHDL.html: $(MANUALFILES)
	$(MKHTML) --dir html/manual manual/MyHDL.tex

whatsnew03: html/whatsnew03/whatsnew03.html
html/whatsnew03/whatsnew03.html: whatsnew03/whatsnew03.tex
	$(MKHTML) --dir html/whatsnew03 whatsnew03/whatsnew03.tex



# webchecker needs an extra flag to process the huge index from the libref
WEBCHECKER=$(PYTHON) ../Tools/webchecker/webchecker.py
HTMLBASE=  file:`pwd`/html

webcheck: $(ALLHTMLFILES)
	$(WEBCHECKER) $(HTMLBASE)/manual/
	$(WEBCHECKER) $(HTMLBASE)/doc/

fastwebcheck: $(ALLHTMLFILES)
	$(WEBCHECKER) -x $(HTMLBASE)/manual/
	$(WEBCHECKER) -x $(HTMLBASE)/doc/


# Release packaging targets:

paper-$(PAPER)/README: $(PSFILES) $(TOOLSDIR)/getpagecounts
	cd paper-$(PAPER) && ../$(TOOLSDIR)/getpagecounts -r $(RELEASE) >../$@

info-$(RELEASE).tgz: info
	cd $(INFODIR) && tar cf - README python.dir python-*.info* \
		| gzip -9 >$@

info-$(RELEASE).tar.bz2: info
	cd $(INFODIR) && tar cf - README python.dir python-*.info* \
		| bzip2 -9 >$@

latex-$(RELEASE).tgz:
	$(PYTHON) $(TOOLSDIR)/mksourcepkg --gzip $(RELEASE)

latex-$(RELEASE).tar.bz2:
	$(PYTHON) $(TOOLSDIR)/mksourcepkg --bzip2 $(RELEASE)

latex-$(RELEASE).zip:
	rm -f $@
	$(PYTHON) $(TOOLSDIR)/mksourcepkg --zip $(RELEASE)

pdf-$(PAPER)-$(RELEASE).tar: $(PDFFILES)
	rm -f $@
	mkdir Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/*.pdf Python-Docs-$(RELEASE)
	tar cf $@ Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)

pdf-$(PAPER)-$(RELEASE).tgz: pdf-$(PAPER)-$(RELEASE).tar
	gzip -9 <$? >$@

pdf-$(PAPER)-$(RELEASE).tar.bz2: pdf-$(PAPER)-$(RELEASE).tar
	bzip2 -9 <$? >$@

pdf-$(PAPER)-$(RELEASE).zip: pdf
	rm -f $@
	mkdir Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/*.pdf Python-Docs-$(RELEASE)
	zip -q -r -9 $@ Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)

postscript-$(PAPER)-$(RELEASE).tar: $(PSFILES) paper-$(PAPER)/README
	rm -f $@
	mkdir Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/*.ps Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/README Python-Docs-$(RELEASE)
	tar cf $@ Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)

postscript-$(PAPER)-$(RELEASE).tar.bz2: postscript-$(PAPER)-$(RELEASE).tar
	bzip2 -9 <$< >$@

postscript-$(PAPER)-$(RELEASE).tgz: postscript-$(PAPER)-$(RELEASE).tar
	gzip -9 <$< >$@

postscript-$(PAPER)-$(RELEASE).zip: $(PSFILES) paper-$(PAPER)/README
	rm -f $@
	mkdir Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/*.ps Python-Docs-$(RELEASE)
	cp paper-$(PAPER)/README Python-Docs-$(RELEASE)
	zip -q -r -9 $@ Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)

HTMLPKGFILES=*.html */*.css */*.html */*.gif */*.txt

html-$(RELEASE).tar:	$(ALLHTMLFILES) $(HTMLCSSFILES)
	mkdir Python-Docs-$(RELEASE)
	cd html && tar cf ../temp.tar $(HTMLPKGFILES)
	cd Python-Docs-$(RELEASE) && tar xf ../temp.tar
	rm temp.tar
	tar cf html-$(RELEASE).tar Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)

html-$(RELEASE).tgz:	html-$(RELEASE).tar
	gzip -9 <$? >$@

html-$(RELEASE).tar.bz2: html-$(RELEASE).tar
	bzip2 -9 <$? >$@

html-$(RELEASE).zip:	$(ALLHTMLFILES) $(HTMLCSSFILES)
	rm -f $@
	mkdir Python-Docs-$(RELEASE)
	cd html && tar cf ../temp.tar $(HTMLPKGFILES)
	cd Python-Docs-$(RELEASE) && tar xf ../temp.tar
	rm temp.tar
	zip -q -r -9 $@ Python-Docs-$(RELEASE)
	rm -r Python-Docs-$(RELEASE)



# convenience targets:

tarhtml:	html-$(RELEASE).tgz
tarinfo:	info-$(RELEASE).tgz
tarps:		postscript-$(PAPER)-$(RELEASE).tgz
tarpdf:		pdf-$(PAPER)-$(RELEASE).tgz
tarlatex:	latex-$(RELEASE).tgz

tarballs:	tarpdf tarps tarhtml

ziphtml:	html-$(RELEASE).zip
zipps:		postscript-$(PAPER)-$(RELEASE).zip
zippdf:		pdf-$(PAPER)-$(RELEASE).zip
ziplatex:	latex-$(RELEASE).zip

zips:		zippdf zipps ziphtml

bziphtml:	html-$(RELEASE).tar.bz2
bzipinfo:	info-$(RELEASE).tar.bz2
bzipps:		postscript-$(PAPER)-$(RELEASE).tar.bz2
bzippdf:	pdf-$(PAPER)-$(RELEASE).tar.bz2
bziplatex:	latex-$(RELEASE).tar.bz2

bzips:		bzippdf bzipps bziphtml

disthtml:	tarhtml bziphtml ziphtml
distinfo:	tarinfo bzipinfo
distps:		tarps bzipps zipps
distpdf:	tarpdf bzippdf zippdf
distlatex:	tarlatex bziplatex ziplatex

paperdist:	distpdf distps
edist:		disthtml 

distfiles:	paperdist edist
	$(TOOLSDIR)/mksourcepkg --all $(RELEASE)
	$(TOOLSDIR)/mkpkglist >pkglist.html


# Housekeeping targets

# Remove temporary files; all except the following:
# - sources: .tex, .bib, .sty, *.cls
# - useful results: .dvi, .pdf, .ps, .texi, .info
clean:
	rm -f html-$(RELEASE).tar
	cd $(INFODIR) && $(MAKE) clean

# Remove temporaries as well as final products
clobber:
	rm -f html-$(RELEASE).tar
	rm -f html-$(RELEASE).tgz info-$(RELEASE).tgz
	rm -f pdf-$(RELEASE).tgz postscript-$(RELEASE).tgz
	rm -f latex-$(RELEASE).tgz html-$(RELEASE).zip
	rm -f pdf-$(RELEASE).zip postscript-$(RELEASE).zip
	rm -f $(DVIFILES) $(PSFILES) $(PDFFILES)
	cd $(INFODIR) && $(MAKE) clobber
	rm -f paper-$(PAPER)/*.tex paper-$(PAPER)/*.ind paper-$(PAPER)/*.idx
	rm -f paper-$(PAPER)/*.l2h paper-$(PAPER)/*.how paper-$(PAPER)/README
	rm -rf html/index.html html/modindex.html html/acks.html
	rm -rf html/manual/ 
	rm -rf html/whatsnew03/

realclean distclean:  clobber
