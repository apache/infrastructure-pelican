# Tools for using Pelican at the ASF

The infrastructure-pelican repository provides a customized process
for working with Pelican-based websites at the ASF. 

_TBD:_ [Get your site started!](Getting_Started.md)

# Running Local Preview Builds

Once your infrastructure-pelican site is deployed to GitHub, you can easily 
deploy it for local testing.

Download the [automatic build tool](https://github.com/apache/infrastructure-pelican/bin/build-pelican-website.sh), and run it, providing the name of your GitHub website repo. 

Example:

./build-pelican-website.sh infrastructure-website

Once the process has completed, you should be able to see the rendered site by opening a web browser to http://localhost:8000/

Contact users@infra.apache.org for any questions or comments.

