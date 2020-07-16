PYTHON = python

.PHONY: test build install clean

test:
	@$(PYTHON) -m doctest -v safer_shell_command.py

build:
	@./setup.py build

install:
	@./setup.py install

clean:
	@rm -f *~ *.pyc
