default:
	@true

docs:
	python setup.py build_sphinx

install:
	python setup.py -q install --root=$(DESTDIR) --prefix=$(PREFIX)

clean:
	python setup.py clean
	rm -rf docs/_build

.PHONY: docs
all: install
