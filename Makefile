default:
	@true

docs:
	python3 setup.py build_sphinx

install:
	python3 setup.py -q install --root=$(DESTDIR) --prefix=$(PREFIX)

clean:
	python3 setup.py clean
	rm -rf docs/_build

.PHONY: docs
all: install
