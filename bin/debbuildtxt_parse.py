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

import logging

from debbuild_structures import PackageInstalledBuildInfo, PackageBuildingBuildInfo, PackageFailedBuildInfo, \
   PackageNot_For_UsBuildInfo, PackageDep_WaitBuildInfo, PackageDep_Wait_RemovedBuildInfo, PackageUploadedBuildInfo, \
   PackageNeeds_BuildBuildInfo, PackageFailed_RemovedBuildInfo

_log = logging.getLogger('dtth.txt_parse')

convertors = {
   'Installed':PackageInstalledBuildInfo,
   'Building':PackageBuildingBuildInfo,
   'Failed':PackageFailedBuildInfo,
   'Not-For-Us':PackageNot_For_UsBuildInfo,
   'Dep-Wait':PackageDep_WaitBuildInfo,
   'Dep-Wait-Removed':PackageDep_Wait_RemovedBuildInfo,
   'Uploaded':PackageUploadedBuildInfo,
   'Needs-Build':PackageNeeds_BuildBuildInfo,
   'Failed-Removed':PackageFailed_RemovedBuildInfo
}

def package_add(results, package):
   if (package.name in results):
      _log.log(44, 'PackageInfo %r for package with name %r to be added to results is already present as %r. Overwriting the old one.' % (package, package.name, results[package.name]))
   results[package.name] = package

def file_parse(f):
   results = {}
   buf = []
   packagename = None
   f.readline() #discard first line
   index = 0
   for line in f:
      if (not line):
         continue
      elif (line[0].isspace()):
         buf.append(line)
         continue
      elif (packagename is not None):
         #additional data lines pertaining to the last package should be finished by now.
         package_add(results, convertors[status](section=section, name=packagename, version=version, data_initial=data_initial, data=tuple(buf), index=index))
         del(buf[:])
         index += 1

      try:
         #print line
         (packagename, status, data_initial) = line.split(None,2)
      except ValueError:
         self.logger.log(40, 'Unable to split line %r in three elements by whitespace. Ignoring the line.' % line)
         continue
      if (packagename.lower() == 'total'):
         packagename = None
         continue

      if (not status in convertors):
         packagename = None
         _log.log(42, "I don't know status %r mentioned in line %r. Ignoring the line." % (status, line))
      else:
         if (packagename[-1] == ':'):
            packagename = packagename[:-1]
         if ('/' in packagename):
            packagename_elements = packagename.split('/')
            packagename = packagename_elements[-1]
            section = '/'.join(packagename_elements[:-1])
         else:
            section = None
         if ('_' in packagename):
            (packagename, version) = packagename.split('_',1)
         else:
            version = None
   else:
      if (packagename is not None):
         package_add(results, convertors[status](section=section, name=packagename, version=version, data_initial=data_initial, data=tuple(buf)), index=index)

   return results
