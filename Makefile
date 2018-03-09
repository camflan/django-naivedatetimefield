.PHONY: clean install-dev install uninstall publish

DIST_DIR := ./dist
BUILD_DIR := ./build

all: build
build: $(DIST_DIR)

clean:
	rm -rf $(DIST_DIR)
	rm -rf $(BUILD_DIR)
	rm -rf *.egg-info

install-dev:
	pip install -e .

install:
	pip install .

uninstall:
	pip uninstall .

$(DIST_DIR): setup.cfg setup.py naivedatetimefield/**
	python setup.py sdist
	python setup.py bdist_wheel

publish: setup.py $(DIST_DIR)
	twine upload $(DIST_DIR)/*
