SITEMAP = {}
# Basic information about the site.
SITENAME = 'Apache Template'
SITEDESC = 'Provides a template for projects wishing to use the Pelican ASF static content system'
SITEDOMAIN = 'template.apache.org'
SITEURL = 'https://template.apache.org'
SITELOGO = 'https://template.apache.org/images/logo.png'
SITEREPOSITORY = 'https://github.com/apache/template-site/blob/main/content/'
CURRENTYEAR = 2023
TRADEMARKS = 'Apache, the Apache feather logo, and "Project" are trademarks or registered trademarks'
TIMEZONE = 'UTC'
# Theme includes templates and possibly static files
THEME = 'themes/trivial'
# Specify location of plugins, and which to use
# All content is located at '.' (aka content/ )
PAGE_PATHS = [ '.' ]
STATIC_PATHS = [ '.',  ]
# Where to place/link generated pages

PATH_METADATA = '(?P<path_no_ext>.*)\\..*'

PAGE_SAVE_AS = '{path_no_ext}.html'
# Don't try to translate
PAGE_TRANSLATION_ID = None
# Disable unused Pelican features
# N.B. These features are currently unsupported, see https://github.com/apache/infrastructure-pelican/issues/49
FEED_ALL_ATOM = None
INDEX_SAVE_AS = ''
TAGS_SAVE_AS = ''
CATEGORIES_SAVE_AS = ''
AUTHORS_SAVE_AS = ''
ARCHIVES_SAVE_AS = ''
# Disable articles by pointing to a (should-be-absent) subdir
ARTICLE_PATHS = [ 'blog' ]
# needed to create blogs page
ARTICLE_URL = 'blog/{slug}.html'
ARTICLE_SAVE_AS = 'blog/{slug}.html'
# Disable all processing of .html files
READERS = { 'html': None, }
# TODO: find out how to disable the sitemap
SITEMAP = {'format': 'txt'}







