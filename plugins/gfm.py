#!/usr/bin/python
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
#
# gfm_reader.py -- GitHub-Flavored Markdown reader for Pelican
#

import sys
import os.path
import re

import pelican.utils
import pelican.plugins.signals
import pelican.readers
import pycmarkgfm


class GFMReader(pelican.readers.BaseReader):
    enabled = True
    """GFM-flavored Reader for the Pelican system.

    Pelican looks for all subclasses of BaseReader, and automatically
    registers them for the file extensions listed below. Thus, nothing
    further is required by users of this Reader.
    """

    # NOTE: the builtin MarkdownReader must be disabled. Otherwise, it will be
    #       non-deterministic which Reader will be used for these files.
    file_extensions = ['md', 'markdown', 'mkd', 'mdown']

    # Metadata is specified as a single, colon-separated line, such as:
    #
    # Title: this is the title
    #
    # Note: name starts in column 0, no whitespace before colon, will be
    #       made lower-case, and value will be stripped
    #
    RE_METADATA = re.compile('^([A-za-z]+): (.*)$')

    def read_source(self, source_path):
        "Read metadata and content from the source."

        # Prepare the "slug", which is the target file name. It will be the
        # same as the source file, minus the leading ".../content/(articles|pages)"
        # and with the extension removed (Pelican will add .html)
        relpath = os.path.relpath(source_path, self.settings['PATH'])
        parts = relpath.split(os.sep)
        parts[-1] = os.path.splitext(parts[-1])[0]  # split off ext, keep base
        slug = os.sep.join(parts[1:])

        metadata = {
            'slug': slug,
        }
        # Fetch the source content, with a few appropriate tweaks
        with pelican.utils.pelican_open(source_path) as text:

            # Extract the metadata from the header of the text
            lines = text.splitlines()
            for i in range(len(lines)):
                line = lines[i]
                match = GFMReader.RE_METADATA.match(line)
                if match:
                    name = match.group(1).strip().lower()
                    if name != 'slug':
                        value = match.group(2).strip()
                        if name == 'date':
                            value = pelican.utils.get_date(value)
                    metadata[name] = value
                    #if name != 'title':
                    #  print 'META:', name, value
                elif not line.strip():
                    # blank line
                    continue
                else:
                    # reached actual content
                    break

            # Redo the slug for articles.
            # depending on pelicanconf.py this will change the output filename
            if parts[0] == 'articles' and 'title' in metadata:
                metadata['slug'] = pelican.utils.slugify(
                    metadata['title'],
                    self.settings.get('SLUG_SUBSTITUTIONS', ()))

            # Reassemble content, minus the metadata
            text = '\n'.join(lines[i:])

            return text, metadata

    def read(self, source_path):
        "Read metadata and content then render into HTML."

        # read metadata and markdown content
        text, metadata = self.read_source(source_path)
        assert text
        assert metadata
        # Render the markdown into HTML
        if sys.version_info >= (3, 0):
            text = text.encode('utf-8')
            content = self.render(text).decode('utf-8')
        else:
            content = self.render(text)
        assert content

        return content, metadata

    def render(self, text):
        "Use cmark-gfm to render the Markdown into an HTML fragment."
        return pycmarkgfm.gfm_to_html(text.decode("utf-8")).encode("utf-8")



def add_readers(readers):
    readers.reader_classes['md'] = GFMReader


def register():
    pelican.plugins.signals.readers_init.connect(add_readers)
