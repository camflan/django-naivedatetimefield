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
	pip3 install -e .

install:
	pip3 install .

uninstall:
	pip3 uninstall .

$(DIST_DIR): setup.cfg setup.py naivedatetimefield/**
	python3 setup.py sdist
	python3 setup.py bdist_wheel

publish: setup.py $(DIST_DIR)
	twine upload $(DIST_DIR)/*
