# Dockerfile to build with infrastructure-pelican.
# Inspired from https://github.com/boonto/docker-pelican
# (which is MIT licensed) for the Pelican-specific bits.
#
# To build the image, use
#
#    docker build -t pelican-asf .
#
# Optionally adding `--build-arg INFRA_PELICAN_COMMIT=<commit_hash>`if
# you need to use a specific commit of the infrastructure-pelican
# repository for the ASF plugins.
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
#    pelican -r -o /site-generated -b 0.0.0.0 -l [-D] # -D: optional debug; noisy
#

# Build Pelican-ASF
FROM python:3.9.5-slim-buster as pelican-asf

RUN apt update && apt upgrade -y
RUN apt install git curl cmake build-essential -y

# Define this *after* initial setup to allow that to be cached
# TODO: document why this needs to be defined and how to choose the commit to be used
ARG INFRA_PELICAN_COMMIT=83e4a5dd6e28a101cc61085d2da6dbaed66e4513

WORKDIR /tmp/pelican-asf
RUN git clone https://github.com/apache/infrastructure-pelican.git .
RUN git -C . checkout ${INFRA_PELICAN_COMMIT}
RUN ./bin/build-cmark.sh | grep LIBCMARKDIR > LIBCMARKDIR.sh

# Standard Pelican stuff
FROM python:3.9.5-slim-buster

RUN apt update && apt upgrade -y
RUN apt install wget unzip fontconfig -y
RUN pip install bs4 requests pyyaml ezt pelican-sitemap BeautifulSoup4

ARG PELICAN_VERSION=4.6.0
ARG MATPLOTLIB_VERSION=3.4.1
RUN pip install pelican==${PELICAN_VERSION}
RUN pip install matplotlib==${MATPLOTLIB_VERSION}

# Copy cmark and ASF plugins here
WORKDIR /tmp/pelican-asf
COPY --from=pelican-asf /tmp/pelican-asf .

# Run Pelican
WORKDIR /site
RUN mkdir -p /site-generated
ENTRYPOINT [ "/bin/bash", "-c", "source /tmp/pelican-asf/LIBCMARKDIR.sh && /tmp/pelican-asf/bin/buildsite.py dir --listen" ]