install:
	python setup.py install

localinstall:
	python setup.py install --home=$(HOME)

release:
	- rm MANIFEST 
	- rm CHANGELOG.txt
	hg glog > CHANGELOG.txt
	python setup.py sdist 
