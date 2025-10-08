# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../python'))

# -- Project information -----------------------------------------------------

project = 'microsync'
copyright = '2025, Roman Kiselev'
author = 'Roman Kiselev'

# The full version, including alpha/beta/rc tags
# Import version from the package
import sys
import os
sys.path.insert(0, os.path.abspath('../python'))
from microsync.__version__ import __version__
release = __version__
version = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinx.ext.githubpages',
    'breathe',
    'exhale',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# -- Options for autodoc ----------------------------------------------------

# Automatically extract typehints when specified and place them in
# descriptions of the relevant function/method.
autodoc_typehints = "description"

# Don't show type hints in the signature
autodoc_typehints_format = "short"

# Include both class docstring and __init__ docstring
autodoc_class_content = "both"

# Show the module name in the documentation
add_module_names = False

# -- Options for autodoc ----------------------------------------------------

# Exclude internal functions and classes from documentation
autodoc_default_options = {
    'exclude-members': 'cu8,cu16,cu32,c32,UInt32,UInt64,uint32_to_py,uint64_to_py,pad,us2cts,cts2us,close_lost_serial_port,_compare_versions,LoggingSerial,Port,SyncDeviceError',
    'private-members': False,
    'special-members': '__init__,__enter__,__exit__',
}

# Exclude patterns for autodoc
autodoc_mock_imports = []
exclude_patterns = ['*.log', '*.ipynb']

# -- Options for napoleon ---------------------------------------------------

# Use Google style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# -- Options for intersphinx -------------------------------------------------

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
}

# -- Options for todo extension ----------------------------------------------

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- HTML theme options -----------------------------------------------------

html_theme_options = {
    'navigation_depth': 4,
    'titles_only': False,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'includehidden': True,
    'logo_only': False,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'vcs_pageview_mode': '',
    'style_nav_header_background': '#2980B9',
}

# -- Breathe configuration -------------------------------------------------

# Breathe is the extension that parses the Doxygen XML output
breathe_projects = {
    "microsync": "_doxygen/xml"
}
breathe_default_project = "microsync"
breathe_default_members = ('members', 'undoc-members')

# -- Exhale configuration -------------------------------------------------

# Setup the exhale extension
exhale_args = {
    # These arguments are required
    "containmentFolder":     "./cpp_api",
    "rootFileName":          "library_root.rst",
    "rootFileTitle":         "C++ API Reference",
    "doxygenStripFromPath":  "..",
    # Suggested optional arguments
    "createTreeView":        True,
    "exhaleExecutesDoxygen": True,
    "exhaleUseDoxyfile":     True,
    # Additional settings for better function resolution
    "verboseBuild":          True,
}

# -- Additional settings ----------------------------------------------------

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'index'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
language = 'en'

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
modindex_common_prefix = ['microsync.']

# -- GitHub Pages specific settings -----------------------------------------

# Ensure proper base URL for GitHub Pages
html_baseurl = 'https://stjude-smc.github.io/microsync/'

# Add canonical URL
html_use_index = True
html_split_index = False

# Ensure proper encoding
html_output_encoding = 'utf-8'

# Add meta tags for better SEO
html_meta = {
    'viewport': 'width=device-width, initial-scale=1',
    'description': 'Documentation for microsync - A synchronization device library',
    'keywords': 'synchronization, device, library, documentation',
} 