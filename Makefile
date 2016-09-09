install:
	python setup.py install

package:
	python setup.py clean
	python setup.py sdist

clean:
	rm -rf build
	rm -rf dist/
	rm -rf wificontrol.egg-info
