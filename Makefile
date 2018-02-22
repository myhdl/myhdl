install:
	python setup.py install

localinstall:
	python setup.py install --home=$(HOME)

docs:
	tox -e docs html

livedocs:
	tox -e docs livehtml

release:
	- rm MANIFEST 
	- rm CHANGELOG.txt
	hg glog > CHANGELOG.txt
	python setup.py sdist 
