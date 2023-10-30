import datetime
import os
import sys


# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "_ext")))

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'pytestdocs',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'pytest-django'
copyright = f'{datetime.datetime.now(tz=datetime.timezone.utc).year}, Andreas Pelme and contributors'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'sphinx_rtd_theme'

# Output file base name for HTML help builder.
htmlhelp_basename = 'pytest-djangodoc'

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'django': ('https://docs.djangoproject.com/en/stable/',
               'https://docs.djangoproject.com/en/stable/_objects/'),
    'pytest': ('https://docs.pytest.org/en/stable/', None),
}

# Warn about all references where the target cannot be found
nitpicky = True


def setup(app):
    # Allow linking to pytest's confvals.
    app.add_object_type(
        "confval",
        "pytest-confval",
        objname="configuration value",
        indextemplate="pair: %s; configuration value",
    )
