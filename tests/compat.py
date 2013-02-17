try:
	from django.utils.encoding import force_text
except ImportError:
	from django.utils.encoding import force_unicode as force_text


try:
	from urllib2 import urlopen
except ImportError:
	from urllib.request import urlopen
