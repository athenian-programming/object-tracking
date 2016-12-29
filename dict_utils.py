# As described at http://legacy.python.org/dev/peps/pep-0469/

try:
    dict.iteritems
except AttributeError:
    # Python 3
    def itervalues(d):
        return iter(d.values())


    def iteritems(d):
        return iter(d.items())


    def listvalues(d):
        return list(d.values())


    def listitems(d):
        return list(d.items())
else:
    # Python 2
    def itervalues(d):
        return d.itervalues()


    def iteritems(d):
        return d.iteritems()


    def listvalues(d):
        return d.values()


    def listitems(d):
        return d.items()
