# -*- coding: utf-8 -*-

import os
import sys
import datetime

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "_ext")))

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    'sphinx.ext.doctest',
    'pytestdocs',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'pytest-django'
copyright = u'%d, Andreas Pelme and contributors' % datetime.date.today().year

exclude_patterns = ['_build']

pygments_style = 'sphinx'
html_theme = 'flask'
html_theme_options = {
    # 'index_logo': '',
    'github_fork': 'pytest-dev/pytest-django',
}
html_sidebars = {
    'index': [
        'sidebarintro.html',
        'globaltoc.html',
        'searchbox.html'
    ],
    '**': [
        'globaltoc.html',
        'relations.html',
        'searchbox.html'
    ]
}
# html_style = 'rtd.css'
# RTD_NEW_THEME = True

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Output file base name for HTML help builder.
htmlhelp_basename = 'pytest-djangodoc'
