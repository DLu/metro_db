# -- Path setup --------------------------------------------------------------
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
project = 'MetroDB'
copyright = '2022, David V. Lu!!'
author = 'David V. Lu!!'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
]

# -- Options for HTML output -------------------------------------------------
html_theme = 'scrolls'
autoclass_content = 'both'
html_static_path = ['_static']
