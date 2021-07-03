#!/usr/bin/python -B
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
# asfshell.py - Pelican plugin that runs shell scripts during initialization
#

import sys
import subprocess
import shlex
import io
import os
import traceback

import pelican.plugins.signals
import pelican.settings


# open a subprocess
def os_run(args):
    return subprocess.Popen(args, stdout=subprocess.PIPE, universal_newlines=True)


# run shell
def run_script(pel_ob):
    asf_run = pel_ob.settings.get('ASF_RUN')
    if asf_run:
        print('-----\nasfshell')
        for command in asf_run:
            print(f'-----\n{command}')
            args = shlex.split(command)
            print(args)
            with os_run(args) as s:
                for line in s.stdout:
                    line = line.strip()
                    print(f'{line}')


def tb_initialized(pel_ob):
    """ Print any exception, before Pelican chews it into nothingness."""
    try:
        run_script(pel_ob)
    except Exception:
        print('-----', file=sys.stderr)
        traceback.print_exc()
        # exceptions here stop the build
        raise


def register():
    pelican.plugins.signals.initialized.connect(tb_initialized)
