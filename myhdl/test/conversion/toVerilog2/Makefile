all: cver icarus

icarus:
	py.test icarus.py test_*.py

cver:
	py.test cver.py test_*.py

clean:
	- rm *.o *.out *.v *.vhd *.pyc *~ *.vcd* *.log
