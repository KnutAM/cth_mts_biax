# Configuration file for the Sphinx documentation builder.
# For a full list see the documentation:
# http://www.sphinx-doc.org/en/master/config
import os
import sys

# -- Input to be updated for each new project --------------------------
# Settings put here for convenience, this can be deleted if not 
# all references to it in this file are removed. 
tl_set = {# Name of python package, i.e. top level import <package_name>
          'package': 'cth_mts_biax',
          # Name of project (i.e. header in documentation)
          'project': 'CTH Tension-Torsion Testing Machine Scripts',
          # Name of authors
          'author': 'Knut Andreas Meyer',
          # Copyright year
          'copyyear': '2021',
          # Version
          'version': '0.1'}

# -- Path setup --------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another 
# directory, add these directories to sys.path here. If the directory 
# is relative to the documentation root, use os.path.abspath to make 
# it absolute, like shown here.

repo = os.path.abspath('../..')
src = repo + '/' + tl_set['package']

project_paths = [src]
for p in project_paths:
    sys.path.insert(0, p)

# -- Project information -----------------------------------------------
project = tl_set['project']
author = tl_set['author']
copyright = tl_set['copyyear'] + ', ' + author
version = tl_set['version']    # The short X.Y version
release = tl_set['version']    # The full version, including 
                               # alpha/beta/rc tags

show_authors = False # display values of .. codeauthor:: directive.

# -- General configuration ---------------------------------------------
autodoc_member_order = 'bysource'   # Requires v>=1.0

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

# Mock imports that are not available at build time:
autodoc_mock_imports = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = None


# -- Options for HTML output -------------------------------------------
html_last_updated_fmt = "%Y-%m-%d %H:%M"
# The theme to use for HTML and HTML Help pages.  
# See the documentation for a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Theme-specific options
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) 
# here, relative to this directory. They are copied after the builtin 
# static files, so a file named "default.css" will overwrite the 
# builtin "default.css".
html_static_path = ['_static']


# -- Options for LaTeX output ------------------------------------------
latex_elements = {
                  'papersize': 'a4paper',
                  'pointsize': '10pt',
                # 'preamble': '',
                # 'figure_align': 'htbp',
                 }

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'manual.tex', project,
     author, 'manual'),
]


# -- Extension configuration -------------------------------------------

# -- Options for todo extension ----------------------------------------
# If true, `todo` and `todoList` produce output, else they produce 
# nothing.
todo_include_todos = True