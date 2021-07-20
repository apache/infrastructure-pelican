# Dockerfile to build with infrastructure-pelican.
# Inspired from https://github.com/boonto/docker-pelican
# (which is MIT licensed) for the Pelican-specific bits.
#
# To build the image, use
#
#    docker build -t pelican-asf .
#
# You can then run the image with
#
#    docker run -it -p8000:8000 -v $PWD:/site pelican-asf
#
# from a folder that contains your pelicanconf.yaml file and ./content folder.
#
# That should build the site, make it available at http://localhost:8000 and rebuild
# if you make changes to the content.
#
# To run a different command you can override the entrypoint, like for example:
#
#    docker run -it -p8000:8000 -v $PWD:/site --entrypoint "pelican-quickstart" pelican-asf
#
# To troubleshoot the image you can get a shell in a container that runs it, with
#
#    docker run -it -p8000:8000 -v $PWD:/site --entrypoint bash pelican-asf
#
# And then run this or anything suitable in that shell to experiment:
#
#    source /tmp/pelican-asf/LIBCMARKDIR.sh
#    /tmp/pelican-asf/bin/buildsite.py dir --listen
#
#    or
#
#    pelican -r -o /site-generated -b 0.0.0.0 -l [-D] # -D: optional debug; noisy
#
# To build the site from the latest commit and simply listen.
#
#    docker run -it -p8000:8000 -v $PWD:/site --entrypoint bash pelican-asf
#    source /tmp/pelican-asf/LIBCMARKDIR.sh
#    git config --global user.email "<git email>"
#    git config --global user.name "<git name>"
#    /tmp/pelican-asf/bin/buildsite.py git --source . --sourcebranch main --project <project>
#    cd /tmp/<project>/source
#    pelican -b '0.0.0.0' -l
#
# Build basic Pelican image
FROM python:3.9.5-slim-buster as pelican-asf

RUN apt update && apt upgrade -y
RUN apt install curl cmake build-essential -y

# Copy the current ASF code
WORKDIR /tmp/pelican-asf
# copy only the GFM build code initially, to reduce rebuilds
COPY bin bin
# build gfm
RUN ./bin/build-cmark.sh | grep LIBCMARKDIR > LIBCMARKDIR.sh
# we also need the plugins
COPY plugins plugins
# we may need to explain how to create a pelicanconf.yaml
COPY pelicanconf.md pelicanconf.md

# Standard Pelican stuff - rebase the image to save 230MB of image size
FROM python:3.9.5-slim-buster

RUN apt update && apt upgrade -y
RUN apt install git subversion wget unzip fontconfig -y

ARG PELICAN_VERSION=4.6.0
ARG MATPLOTLIB_VERSION=3.4.1
RUN pip install pelican==${PELICAN_VERSION}
RUN pip install matplotlib==${MATPLOTLIB_VERSION}

# Copy the built cmark and ASF 
WORKDIR /tmp/pelican-asf
COPY --from=pelican-asf /tmp/pelican-asf .

COPY requirements.txt .
RUN pip install -r requirements.txt --no-deps

# If the site needs authtokens to build, copy them into the file .authtokens
# and it will be picked up at build time
# N.B. make sure the .authtokens file is not committed to the repo!
RUN ln -s /site/.authtokens /root/.authtokens

# Run Pelican
WORKDIR /site
RUN mkdir -p /site-generated
ENTRYPOINT [ "/bin/bash", "-c", "source /tmp/pelican-asf/LIBCMARKDIR.sh && /tmp/pelican-asf/bin/buildsite.py dir --listen" ]
