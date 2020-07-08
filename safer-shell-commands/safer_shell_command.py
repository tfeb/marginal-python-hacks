from re import match
from collections import defaultdict

class BogusSSC(Exception):
    pass

class SCCTrouble(Exception):
    pass

class SaferShellCommand(object):
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
        if match(r"[a-zA-Z0-9][a-zA-Z0-9_-]*$", arg) is not None:
            return True
        else:
            return False
    
    def validate_replacement(self, name, value):
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
        if not self.validate_replacements(replacements):
            raise SCCTrouble("bad replacements")
        filled_template = list(self.template)
        for (ti, tr) in ((self.mapper[n], r)
                          for (n, r) in replacements.items()):
            filled_template[ti] = tr
        return filled_template
    
    def command_line(self, iterable):
        return " ".join(iterable)
    
    def fill_command_line(self, replacements):
        return self.command_line(self.fill_template(replacements))
