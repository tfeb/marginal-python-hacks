# Wrapping Python in tiny shell scripts
`libexec/python-wrapper` is a tiny shell script which is designed to
be the target of a symlink from a file in `bin` which is the
executable program.  It:

- works out its name, `ME` and a root directory, `ROOT` which is one
  level up from where it is;
- points Python at a program, which is `$ROOT/libexec/$ME.py`, first
  prepending `$ROOT/lib/python` to `PYTHONPATH`.

The end result of this is that the Python program gets to run in an
environment where modules in `$ROOT/lib/python` will be found, without
any need for global environment.

There is an example program `bin/pppath` / `libexec/pppath.py`.

## Notes
- If the `PYTHON` environment variable is set it will use this for the
  Python interpreter, otherwise it will use `python`.
- The target program (`$ROOT/libexec/$ME.py`) needs to be executable.
