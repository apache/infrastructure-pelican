echo Running GFM
pelican content --settings pelican.gfm.py -d --o gfm
echo Running default Markdown
pelican content --settings pelican.def.py -d --o def
rm def/sitemap.txt # not needed
diff -r gfm def
