# Safer shell commands

This is a Python (3 or 2.7) module which tries to reduce the horrible
danger of running shell commands, in the sense of 'strings you hand to
the shell to interpret for you' from Python.

**It does not make this safe.** It merely tries to make it less
horribly dangerous.  The aim is to make sure that command lines look
like you think they should and do not have unexpected bad characters
etc in them, even when some of the content of the command line comes
from an untrusted source.

It does this by letting you construct command lines from templates:
anything in the template which is not a placeholder is assumed to be
trusted, with replacements being filled with potentially untrusted
values.  There are user-provided validators, together with a fallback
validator which is conservative.  for the various placeholders which
can check that their replacements are OK.  Finally you can check a
replacement is valid and fill a template.

Please read this code carefully before using it: I can't be
responsible for any problems resulting.