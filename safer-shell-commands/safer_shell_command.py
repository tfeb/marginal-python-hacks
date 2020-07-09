"""Safer shell commands.

The purpose of this module is to make things which need to create
shell command lines less dangerous.  It is extremely hard to create
shell command lines which are really safe because the shell has so
many edge cases (and there are so many shells), but sometimes (for
instance when using ``ssh`` for remote execution) they are all-but
unavoidable.  This module tries to make them less dangerous: it does
not make them safe.

Examples
--------
>>> valid_switches = {"-i", "-n"}
>>> def valid_switch(s):
...     return s in valid_switches
...
>>> grepper = SaferShellCommand(("grep", {"switch"}, {"pattern"}, {"file"}),
...                             validators={"switch": valid_switch})
>>> grepper.validate_replacement("switch", "-i")
True
>>> grepper.validate_replacement("switch", "-x")
False
>>> replacements = {"switch": "-i", "pattern": "x", "file": "y"}
>>> grepper.validate_replacements(replacements)
True
>>> grepper.fill_template(replacements)
['grep', '-i', 'x', 'y']
>>> grepper.fill_command_line(replacements)
'grep -i x y'
>>> bad_replacements = {"switch": "-q", "pattern": "x", "file": "y"}
>>> grepper.validate_replacements(bad_replacements)
False
>>> grepper.fill_command_line(bad_replacements)
Traceback (most recent call last):
  ...
SCCTrouble: bad replacements

Approach
--------
This module assumes that there are two sources of information which go
to make up an eventual shell command line:

* the program using the module, which is assumed to be trusted;
* user input or any other source external to the program, which needs
  to be validated.

The program provides a template for the shell command, with
placeholders which will be filled in from external sources.  *Only the
replacements for the placeholders are checked*: the rest of the
template is assumed to be trusted.  The template is given as some
iterable object (probably a ``tuple`` or ``list``, but the code does
not care), where normally each element is expected to be one argument.
Placeholders are indicated by the element being a `set`, with the
elements of the set being the names used for the replacement.  Any
other type of object is not treated specially and is assumed to be
trusted.

Validators can be provided: they can either check named replacement
elements, or there can be a fallback validator.  If no validators are
provided then there is a default fallback validator which is rather
conservative: it insists that the replacement matches
``/^[a-zA-Z0-9][a-zA-Z0-9_-]*$/``, which should be reasonably safe.

There are methods to check whether a proposed replacement or set of
replacements is valid, and methods to perform the replacment and
return the filled template either as a ``list`` or as a single string
ready to hand to the shell.

Public interface
----------------
There is one main class, and two exception classes.

``SaferShellCommand`` (class)
    This class implements safer shell commands.

``BogusSCC`` (exception)
    This is an exception class raised if an attempt to create a
    ``SaferShellCommand`` is horribly incorrect.

``SCCTrouble`` (exception)
    Exceptions of this class are raised when a template is being
    filled with replacements which fail validation.

Compatibility
-------------
This module should work in either Python 2.7 or 3: it was written in
Python 3 but has been tested in Python 2.7.
"""

from re import match
from collections import defaultdict

class BogusSSC(Exception):
    """Exception raised when creating a ``SaferShellCommand``.

    Instances of this class are raised if you try to create a
    ``SaferShellCommand`` but botch the arguments in some way.

    """
    pass

class SCCTrouble(Exception):
    """Exception raised when a shell command fails validation.

    Instances of this class are raised if you try to construct a shell
    command from a ``SaferShellCommand`` but it fails validation.

    """
    pass

class SaferShellCommand(object):
    """Safer shell commands.

    Instances of this class wrap a template command line, and some
    validators.  Mathods allow you to check whether replacements are
    valid and to perform replacements ont the template command.

    Parameters
    ---------
    template
        The template for the command.  This is some iterable object
        whose elements are either fixed values, or placeholders.  A
        placeholder is recognised as it is a ``set`` containing one or
        more names for the place (typically only one).  An example
        template might be ``("grep", "-i", "root", {"filename"})``:
        this has a single placeholder with a single name.
   validators
        A ``dict`` mapping names to validators for the placeholder
        with that name.  See below for what a validator can be.  You
        do not need to provide validators for all placeholders, or for
        any in fact.
   fallback_validator
        The fallback validator used to validate any placeholder
        replacements which do not have their own validators.  This is
        optional and there is a default which insists that a
        replacement's value matches ``/[a-zA-Z0-9][a-zA-Z0-9_-]*$/``,
        which is intended to be rather conservative.

    A *validator* is either a function of a single argument which
    should return true if it is valid, or an iterable of such
    functions, all of which should return true if it is valid.

    Attributes
    ----------
    Most of these attributes are provided for inspection purposes:
    none should be changed.  Some should probably be considered private.

    mapper
        A dictionary which maps replacement names onto indices in the
        template.

    targets
        A set of the indices in the template which must be replaced.

    template
        A tuple of the template, with the slots for replacement replaced by
        their indices.

    validators
        A dictionary mapping placeholder names to validators.

    fallback_validator
        The fallback validator.

    Exceptions
    ----------
    If you try to make an instance with arguments which are botched
    somehow a ``BogusSCC`` exception is raised.

    """

    def __init__(self, template, validators=None,
                 fallback_validator=None):
        
        mapper = {}
        targets = set()
        for (i, e) in enumerate(template):
            if isinstance(e, set):
                if len(e) == 0:
                    raise BogusSSC("template variable with no names")
                targets.add(i)
                for k in e:
                    mapper[k] = i
        self.mapper = mapper
        self.targets = targets
        self.template = tuple(i if isinstance(e, set) else e
                              for (i, e) in enumerate(template))
        
        if validators is not None:
            if isinstance(validators, dict):
                for k in validators.keys():
                    if k not in mapper:
                        raise BogusSSC("unmapped validator")
                self.validators = defaultdict((lambda: 
                                               self.fallback_validator),
                                              validators)
            else:
                raise BogusSSC("validators isn't a dict")
        else:
            self.validators = defaultdict((lambda:
                                           self.fallback_validator))
        
        if fallback_validator is not None:
            self.fallback_validator = fallback_validator
        else:
            self.fallback_validator = self.default_fallback_validator
        
    @staticmethod
    def default_fallback_validator(arg):
        """The default fallback validator.

        This is a static method.  See the class definition for what it
        does.

        """
        if match(r"[a-zA-Z0-9][a-zA-Z0-9_-]*$", arg) is not None:
            return True
        else:
            return False
    
    def validate_replacement(self, name, value):
        """Validate a single proposed replacement.

        Returns true if the replacement if valid, false otherwise.

        Arguments
        ---------
        name
            The placeholder name.
        value
            The replacement for the placeholder.

        """
        if name not in self.mapper:
            return False
        validator = self.validators[name]
        if callable(validator):
            return validator(value)
        else:
            for v in validator:
                if not v(value):
                    return False
            return True
    
    def validate_replacements(self, replacements):
        """Validate a ``dict`` of replacements.

        This returns true if the replacements are acceptable, false
        otherwise.

        This is not the same as simply calling
        ``validate_replacement`` on every key and value in the
        argument: it also insists that *all* the replacements needed
        are present.

        Arguments
        ---------
        replacements
            a ``dict`` mapping replacement name to replaement value.

        """
        targets = set()
        for (name, replacement) in replacements.items():
            if not self.validate_replacement(name, replacement):
                return False
            elif self.mapper[name] in targets:
                return False
            else:
                targets.add(self.mapper[name])
        return targets == self.targets
    
    def fill_template(self, replacements):
        """Fill a template with replacements.

        This fills a template with replacements, which must be valid,
        and returns the filled template as a ``list``.

        Arguments
        ---------
        replacements
            A ``dict`` of replacements.

        Exceptions
        ----------
        If the replacements are not valid a ``SCCTrouble`` exception
        is raised.

        """
        if not self.validate_replacements(replacements):
            raise SCCTrouble("bad replacements")
        filled_template = list(self.template)
        for (ti, tr) in ((self.mapper[n], r)
                          for (n, r) in replacements.items()):
            filled_template[ti] = tr
        return filled_template
    
    def command_line(self, iterable):
        """Given an iterable, return a shell command line.

        This method could be used on the result of ``fill_template``,
        but see ``fill_command_line``.  All it does is join the
        elements of the iterable with a single space character.

        """
        return " ".join(iterable)
    
    def fill_command_line(self, replacements):
        """Fill a template and return a command line.

        This uses ``fill_template`` to fill the template and then
        calls ``command_line`` on the result.

        """
        return self.command_line(self.fill_template(replacements))
