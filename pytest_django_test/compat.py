try:
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.request import urlopen, HTTPError  # noqa: F401
