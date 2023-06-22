This directory contains files to test issue62

* compare_meta.sh - runs pelican with GFM and default markdown and compares output
* content/one.md - test file with various meta-data entries
* pelican.def.py - pelican config for the default (non-GFM) markdown
* pelican.gfm.py - pelican config for GFM markdown plugin
* themes/trivial/templates/base.html - template to show how the markdown source is handled 
