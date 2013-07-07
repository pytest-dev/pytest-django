try:
    from django.utils.encoding import force_text  # noqa
except ImportError:
    from django.utils.encoding import force_unicode as force_text  # noqa


try:
    from urllib2 import urlopen  # noqa
except ImportError:
    from urllib.request import urlopen  # noqa
