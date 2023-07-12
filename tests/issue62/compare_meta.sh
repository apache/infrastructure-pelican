echo Running GFM
pelican content --settings pelican.gfm.py -d --o gfm
echo Running default Markdown
pelican content --settings pelican.def.py -d --o def
diff -r gfm def
