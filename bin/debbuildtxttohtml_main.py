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
import datetime
import logging

import debbuildtxt_parse
import debbuildhtml_write
from debbuildhtml_write import StatsOutput
import debbuild_structures
from debbuild_structures import OutputSpecification


time_fmt_string = '%Y-%m-%d %H:%M:%S'
stats_filenamemask = 'output/%(architecture)s_stats.html'

_log = logging.getLogger('dtth.main')

def results_order_output(results_all, filename_parameters):
   resultsbyoutput = {}
   for convertor in debbuildtxt_parse.convertors.values():
      for output_spec in convertor.output_spec_return():
         #files should be rewritten even if the current input doesn't contain any matching packages
         resultsbyoutput[output_spec] = [convertor]

   for result in results_all:
      for output_spec in result.output_spec_return():
         if not (output_spec in resultsbyoutput):
            resultsbyoutput[output_spec] = [result.__class__]
         resultsbyoutput[output_spec].append(result)

   resultsbyoutput[OutputSpecification(stats_filenamemask % filename_parameters, None)] = (StatsOutput,) + results_all

   return resultsbyoutput



def txttohtml(architecture, flavor, buildphp_host, source_filename):
   debbuild_structures.PackageGenericBuildInfo.arch = architecture
   debbuild_structures.PackageGenericBuildInfo.url_buildphp = 'http://%s/build.php' % (buildphp_host,)

   #_log.log(20, 'Stating %r.' % (source_filename,))
   source_datetime = datetime.datetime.fromtimestamp(os.stat(source_filename)[8])
   if (source_datetime > datetime.datetime.now()):
      _log.log(35, 'Datetime %r which appears to be last modification datetime of %r lies in the future relevant to now. Using it anyway.' % (source_datetime.strftime(time_fmt_string), source_filename))
   else:
      _log.log(20, '%r appears to have been last modified at %r.' % (source_filename, source_datetime.strftime(time_fmt_string)))

   #_log.log(20, 'Opening %r for reading.' % (source_filename))
   source_file = file(source_filename)
   results_all = debbuildtxt_parse.file_parse(source_file)
   #_log.log(20, 'Closing %r.' % (source_filename,))
   source_file.close()
   resultsbyoutput = results_order_output(tuple(results_all.values()), {'architecture':architecture, 'flavor':flavor, 'buildphp_host':buildphp_host, 'source_filename':source_filename})
   for output_spec in resultsbyoutput.keys():
      filename = output_spec.filename
      #_log.log(20, 'Opening file %r for writing.' % filename)
      targetfile = file(filename, 'w')
      resultclass = resultsbyoutput[output_spec][0]
      try:
         debbuildhtml_write.html_write(targetfile, output_spec.data, resultclass, resultsbyoutput[output_spec][1:], source_datetime, source_filename, results_all)
      except StandardError:
         _log.log(40, 'Write-html failure on writing to %r:' % (filename,), exc_info=True)

      #_log.log(20, 'Closing file %r.' % filename)
      targetfile.close()

   stats_out = file(stats_filenamemask % locals())


