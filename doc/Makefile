NAME = MyHDL

default: $(NAME).dvi $(NAME).ps $(NAME).pdf

#%.pdf: %.ps
#	ps2pdf $<; \

%.ps: %.dvi
	dvips -o $@ -t a4 -Ppdf -G0 $<

%.dvi: %.tex
	latex $<; \
	python tools/toc2bkm.py -c chapter $(NAME).toc
	latex $<; \
	pdflatex $<

clean:
	-rm *.dvi *.log *.toc *.ps *.pdf *.aux *.out
