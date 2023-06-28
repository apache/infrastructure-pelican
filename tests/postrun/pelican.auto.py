
# Basic information about the site.
SITENAME = 'Apache Software Foundation'
SITEDESC = 'Test run command'
SITEDOMAIN = 'test.apache.org'
SITEURL = 'https://test.apache.org'
SITELOGO = 'https://test.apache.org/None'
SITEREPOSITORY = 'None'
CURRENTYEAR = 2023
TRADEMARKS = 'Apache, the Apache feather logo are trademarks'
TIMEZONE = 'UTC'
# Theme includes templates and possibly static files
THEME = './theme/apache'
# Specify location of plugins, and which to use
PLUGIN_PATHS = [ '/private/var/sebb/git/infra/pelican/bin/../plugins',  ]
PLUGINS = [ 'gfm', 'asfrun',  ]
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





# Configure the asfrun plugin (finalization)
ASF_POSTRUN = [ '/bin/bash postrun.sh',  ]




