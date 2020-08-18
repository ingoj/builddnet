#!/usr/bin/env python
# Copyright 2005 Sebastian Hagen
# This file is part of deb_txttohtml.
#
# deb_txttohtml is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# deb_txttohtml is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with deb_txttohtml; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import os
import sys
import logging
import optparse

import debbuildtxttohtml_main

source_filenamemask_default = 'input/%(architecture)s-all.txt'

rootlogger = logging.getLogger()
rootlogger.setLevel(0)
rootlogger_handler = logging.StreamHandler()
rootlogger_handler.setFormatter(logging.Formatter('%(asctime)s %(levelno)s %(message)s'))
rootlogger.addHandler(rootlogger_handler)
_log = rootlogger


self_dir = os.path.dirname(sys.argv[0])
_log.log(20, 'Changing directory to %r.' % (self_dir,))
os.chdir(self_dir)

parser = optparse.OptionParser(usage="%prog <flavor> <architecture> <buildphp-host> [options]", option_list = (
   optparse.Option("-s", "--source", dest="source_filename", help="Read raw text data from file (default: %r)" % (source_filenamemask_default,), metavar="FILE", default=None),
   )
)


(options, arguments) = parser.parse_args()

source_filename = options.source_filename

if (len(arguments) <= 2):
   _log.log(50, 'Insufficient positional arguments; expected <flavor> <architecture> <buildphp-host>. Aborting.')
   sys.exit(1)

(flavor, architecture, buildphp_host) = arguments[:3]

if (source_filename is None):
   source_filename = source_filenamemask_default % locals()


if (__name__ == '__main__'):
   debbuildtxttohtml_main.txttohtml(architecture, flavor, buildphp_host, source_filename)

