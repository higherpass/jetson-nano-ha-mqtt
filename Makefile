.PHONY: init test clean build

init:
	pip install -r requirements.txt

test:
	py.test tests

clean:
	rm -rf build dist src/*.egg-info

build:
	python3 -m build
