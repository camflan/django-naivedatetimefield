.PHONY = clean

DIST_DIR := ./dist
BUILD_DIR := ./build

all: $(DIST_DIR) publish

clean:
	rm -rf $(DIST_DIR)
	rm -rf $(BUILD_DIR)
	rm -rf *.egg-info

$(DIST_DIR): setup.cfg setup.py naivedatetimefield/**
	python setup.py sdist
	python setup.py bdist_wheel

publish: setup.py $(DIST_DIR)
	twine upload $(DIST_DIR)/*
