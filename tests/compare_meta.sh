echo Running GFM
pelican content --settings pelican.gfm.py -dD --o gfm
echo Running default Markdown
pelican content --settings pelican.def.py -dD --o def
diff -r gfm def
