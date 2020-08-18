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
import urllib
import cgi
import string

_log = logging.getLogger('dtth.structures')

SORTBY_NAMESTRING = 1
SORTBY_INPUTORDER = 2

class OutputSpecification:
   def __init__(self, filename, data=None):
      self.filename = filename
      self.data = data

   def __hash__(self):
      return hash((self.__class__, self.filename))

   def __cmp__(self, other):
      if (self.filename < other.filename):
         return -1
      elif (self.filename > other.filename):
         return 1
      else:
         return 0

class PackageGenericBuildInfo:
   url_buildphp = 'http://127.0.0.1/build.php'
   url_deb_bugreport = 'http://bugs.debian.org/cgi-bin/bugreport.cgi'
   arch = ''
   def __init__(self, section, name, version, data_initial, data, index):
      self.section = section
      self.name = name
      self.version = version
      self.index = index
      self.data_initial_process(data_initial)
      self.data_process(data)

   def data_initial_process(self, data_initial):
      data_initial_split = data_initial.split(None,2)
      if ((len(data_initial_split) >= 2) and (data_initial_split[0].lower() == 'by')):
         self.host = data_initial_split[1]
         if (len(data_initial_split) >= 3):
            data_initial = data_initial_split[2]
         else:
            data_initial = ''
      else:
         self.host = None

      self.data_initial = data_initial

   def data_process(self, data):
      self.data = data

   def output_spec_return(class_self):
      return tuple([OutputSpecification(args[0] % {'arch':class_self.arch}, *args[1:]) for args in class_self.output_data])

   output_spec_return = classmethod(output_spec_return)

   def url_return_deb_bugreport(self_class, bug_number):
      return ('%s?bug=%d' % (self_class.url_deb_bugreport, bug_number))
   url_return_deb_bugreport = classmethod(url_return_deb_bugreport)

   def url_return_buildphp(self):
      return ('%s?arch=%s&pkg=%s&ver=%s' % ((self.url_buildphp,) + tuple([urllib.quote(element) for element in (self.arch, self.name, self.version)]))).replace('&', '&amp;')

   def link_return(url, linktext):
      return '<a href="%s">%s</a>' % (url, cgi.escape(linktext))
   link_return = staticmethod(link_return)

   def link_return_buildphp(self):
      return self.link_return(self.url_return_buildphp(), '%s_%s' % (self.name, self.version))

   def link_return_deb_bugreport(self_class, bug_number):
      return self_class.link_return(self_class.url_return_deb_bugreport(bug_number), '#%d' % (bug_number,))
   link_return_deb_bugreport = classmethod(link_return_deb_bugreport)

   html_return = link_return_buildphp

   def deb_bug_link(self, line):
      numbers_used = []
      for word in line.split():
         if (word[0] == '#'):
            word = word.rstrip(string.punctuation)
         else:
            continue
         if (len(word) == 0):
            continue
         try:
            bug_number = int(word[1:])
         except:
            continue
         else:
            if (bug_number in numbers_used):
               continue
            line = line.replace(word, self.link_return_deb_bugreport(bug_number))
            numbers_used.append(bug_number)

      return line

   def __cmp__(self, other):
      if (self.name < other.name):
         return -1
      elif (self.name > other.name):
         return 1
      else:
         return 0

   def __hash__(self):
     hash(self.name)

   def __str__(self):
      return '%s(section=%r, name=%r, version=%r, ...)' % (self.__class__.__name__, self.section, self.name, self.version)

   __repr__ = __str__
   #def __repr__(self):
   #   return '%s(section=%r, name=%r, version=%r, data_initial=%r, data=%r)' % (self.__class__.__name__, self.section, self.name, self.version, self.data_initial, self.data)


class PackageGeneric_PrintDataBuildInfo(PackageGenericBuildInfo):
   def data_process(self, data):
      PackageGenericBuildInfo.data_process(self, data)
      data_processed = []
      for line in data:
         line_stripped = line.rstrip()
         if ((line_stripped != '') and (not line_stripped.isspace())):
            data_processed.append(line_stripped)

      self.data_processed = tuple(data_processed)

   def html_return(self, host_write=True):
      lines = [self.link_return_buildphp()]
      if (host_write):
         lines[0] += '  [%s]' % (self.host,)

      lines[0] += '<span>'
      for line in self.data_processed:
         line = cgi.escape(line)
         lines.append(self.deb_bug_link(line))
      lines.append('</span>\n')

      return '\n'.join(lines)


class PackageGeneric_PrintDataStartStrippedBuildInfo(PackageGeneric_PrintDataBuildInfo):
   def data_process(self, data):
      PackageGeneric_PrintDataBuildInfo.data_process(self, data)

      data = list(self.data_processed)
      stripping_complete = False
      for linestripstart in ('reasons for failing:', '[category:'):
         if (len(data) <= 1):
            break
         if (data[0].lower().lstrip().startswith(linestripstart)):
            del(data[0])
         else:
            break
      else:
         stripping_complete = True

      if not (stripping_complete):
         _log.log(35, 'Unable to find line whose lowercased version would start with %r in data-entry %r for package %r. Aborting strip-attempts for this package-entry here, but otherwise trying to continue processing package data as normal.' % (linestripstart, data, self.name))

      self.data_processed = tuple(data)


class PackageInstalledBuildInfo(PackageGenericBuildInfo):
   status_string = 'Installed'
   output_data = (('output/%(arch)s_Installed.html', None),)

class PackageBuildingBuildInfo(PackageGenericBuildInfo):
   status_string = 'Build'
   output_data = (('output/%(arch)s_Building.html', None),)

class PackageFailedBuildInfo(PackageGeneric_PrintDataStartStrippedBuildInfo):
   status_string = 'Failed'
   output_data = (('output/%(arch)s_Failed.html', None),)
   def data_process(self, data):
      PackageGeneric_PrintDataStartStrippedBuildInfo.data_process(self, data)
      data_processed = []
      for data_line in self.data_processed:
         data_processed.append(data_line)
         if (data_line.lower().lstrip().startswith('previous state was ')):
            break

      self.data_processed = data_processed

class PackageNot_For_UsBuildInfo(PackageGeneric_PrintDataBuildInfo):
   status_string = 'Not-For-Us'
   output_data = (('output/%(arch)s_Not-For-Us.html', None),)
   def html_return(self):
      #We shouldn't know the host for packages with this status, so don't try to show it
      return PackageGeneric_PrintDataBuildInfo.html_return(self, host_write=False)

class PackageDep_WaitBuildInfo(PackageGenericBuildInfo):
   status_string = 'Dep-Wait'
   output_data = (('output/%(arch)s_Dep-Wait.html', None),)

   def data_process(self, data):
      PackageGenericBuildInfo.data_process(self, data)
      trigger_string = 'dependencies:'
      self.dependencies = {}
      for line_raw in data:
         line = line_raw.strip()
         if (line.lower().startswith(trigger_string)):
            line_split = line.split(None, 1)
            if (len(line_split) <= 1):
               _log.log(35, 'Unable to extract any dependencies from line %r whose lower-cased version starts with %r, located in data section to package %r. Ignoring.' % (line_raw, trigger_string, self.name))
               continue

            for dependency_string in line_split[1].split(','):
               dependency_string_split = dependency_string.strip().split(None, 1)
               if (not dependency_string_split):
                  continue
               elif (len(dependency_string_split) > 1):
                  additional_info = dependency_string_split[1]
               else:
                  additional_info = None
               self.dependencies[dependency_string_split[0]] = additional_info

   def html_return(self):
      return '%s  [%s]' % (self.link_return_buildphp(), self.host)

   def html_return_extended(self, dependency):
      if (self.dependencies[dependency] is None):
         return self.html_return()
      else:
         return '%s  {%s}' % (self.html_return(), self.dependencies[dependency])


class PackageDep_Wait_RemovedBuildInfo(PackageGeneric_PrintDataBuildInfo):
   status_string = 'Dep-Wait-Removed'
   output_data = (('output/%(arch)s_Dep-Wait-Removed.html', None),)

class PackageUploadedBuildInfo(PackageGenericBuildInfo):
   status_string = 'Uploaded'
   output_data = (('output/%(arch)s_Uploaded.html', None),)

class PackageNeeds_BuildBuildInfo(PackageGenericBuildInfo):
   status_string = 'Needs-Build'
   output_data = (('output/%(arch)s_Needs-Build_stringsorted.html', SORTBY_NAMESTRING),('output/%(arch)s_Needs-Build_queueorder.html', SORTBY_INPUTORDER))

class PackageFailed_RemovedBuildInfo(PackageGeneric_PrintDataStartStrippedBuildInfo):
   status_string = 'Failed-Removed'
   output_data = (('output/%(arch)s_Failed-Removed.html', None),)
