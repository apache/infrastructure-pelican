# Configuring Pelican ASF

Conversion of pelicanconf.py to pelicanconf.yaml.

See github.com/apache/template-site and inspect a full pelicanconf.yaml

These are the sections:

## Required

```
site:
  name: Apache Template
  description: Provides a template for projects wishing to use the Pelican ASF static content system
  domain: template.apache.org
  logo: images/logo.png
  repository: https://github.com/apache/template-site/blob/main/content/
  trademarks: Apache, the Apache feather logo, and "Project" are trademarks or registered trademarks

theme: theme/apache
```

## Options

### Plugins

If you are using the standard plugins included in Pelican ASF then you can leave this section out.
Your build will automatically include the `gfm` plugin.

```
plugins:
  paths:
    - theme/plugins
  use:
    - gfm
```

### Special setup

These configure four different special features.

```
setup:
  data: asfdata.yaml
  run:
    - /bin/bash shell.sh
  ignore:
    - README.md
    - include
    - docs
  copy:
    - docs
```

1. data - uses `asfdata` plugin to build a data model to use in `ezmd` files. www-site is the best example.
2. run - uses `asfshell` plugin to run scripts. httpd-site's security vulnerability processing is the best example.
3. ignore - sets Pelican's IGNORE_FILES setting.
4. copy - uses `asfcopy` plugin to copy static files outside of the pelican process. Include these in ignore as well.
   This is useful if you have large files or many static files.

## Generate ID

The `asfgenid` plugin performs a number of fixups and enhancements. See ASF_GENID in your `pelicanconf.py` and convert.

```
genid:
  unsafe: yes
  metadata: yes
  elements: yes
  headings_depth: 4
  permalinks: yes
  toc_depth: 4
  tables: yes
```
