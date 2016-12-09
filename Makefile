install:
	python setup.py install

package:
	python setup.py clean
	python setup.py sdist

test:
	python setup.py test

clean:
	rm -rf build
	rm -rf dist/
	rm -rf wificontrol.egg-info
