import pkg_resources

# FIXME: this but less bad
VERSION = pkg_resources.require('bike')[0].version
