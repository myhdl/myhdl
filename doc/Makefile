NAME = manual

default: $(NAME).dvi $(NAME).ps $(NAME).pdf

%.pdf: %.ps
	ps2pdf $<

%.ps: %.dvi
	dvips -o $@ -t a4 -Ppdf -G0 $<

%.dvi: %.tex
	latex $<; \
	latex $<

clean:
	-rm *.dvi *.log *.toc *.ps *.pdf *.aux *.out
