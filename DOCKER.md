# Dockerfile

## Build the image:

    docker build -t pelican-asf .

## Run the image

From a folder that contains your pelicanconf.yaml file and ./content folder:

    docker run -it -p8000:8000 -v $PWD:/site pelican-asf

That should build the site, make it available at:

     http://localhost:8000

Any changes you make to the content will rebuild the site.

To run a different command you can override the entrypoint. For example:

    docker run -it -p8000:8000 -v $PWD:/site --entrypoint "pelican-quickstart" pelican-asf

To troubleshoot the image you can get a shell in a container that runs it, with

    docker run -it -p8000:8000 -v $PWD:/site --entrypoint bash pelican-asf

Then run this or anything suitable in that shell to experiment:

    source /tmp/pelican-asf/LIBCMARKDIR.sh
    /tmp/pelican-asf/bin/buildsite.py dir --listen

To build the site from the latest github commit and simply listen.

    docker run -it -p8000:8000 -v $PWD:/site --entrypoint bash pelican-asf
    source /tmp/pelican-asf/LIBCMARKDIR.sh
    git config --global user.email "<git email>"
    git config --global user.name "<git name>"
    /tmp/pelican-asf/bin/buildsite.py git --source https://github.com/apache/<project>-site --sourcebranch main --project <project>
    cd /tmp/<project>/source
    pelican -b '0.0.0.0' -l

## Standard entry point

    # Run Pelican
    WORKDIR /site
    RUN mkdir -p /site-generated
    ENTRYPOINT [ "/bin/bash", "-c", "source /tmp/pelican-asf/LIBCMARKDIR.sh && /tmp/pelican-asf/bin/buildsite.py dir --listen" ]
