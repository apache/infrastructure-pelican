#!/bin/bash
#
# $ mkdir confs ; cd confs
# $ .../grab.sh
#
# for info on this script, please see: https://github.com/apache/infrastructure-pelican/issues/23

# https://github.com/search?p=2&q=org%3Aapache+filename%3Apelicanconf.py&type=Code
sites='template-site
www-site
ctakes-site
openwebbeans-site
river-site
bval-site
gora-site
openjpa-site
olingo-site
infrastructure-website
solr-site
petri
lucene-site
treasurer-site
fundraising-site
xmlgraphics-website
foundation-site
openoffice-project
diversity-site
comdev-wwwsite'

### this is not deployed as a real site.
# infrastructure-p6/modules/pelican_asf/files

#echo $sites

# EXAMPLE:
# https://raw.githubusercontent.com/apache/solr-site/main/pelicanconf.py

for s in $sites; do
    f="$s.pelicanconf.py"

    branch=main
    u="https://raw.githubusercontent.com/apache/$s/$branch/pelicanconf.py"
    echo wget -O $f $u
    wget -q -O $f $u

    # The sites use "main" or "master". Try the other...
    if [ -s $f ]; then true ; else
        branch=master
        u="https://raw.githubusercontent.com/apache/$s/$branch/pelicanconf.py"
        echo RETRY: wget -O $f $u
        wget -q -O $f $u
    fi
done
