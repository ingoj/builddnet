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


import time
import logging

from debbuild_structures import \
   SORTBY_NAMESTRING, SORTBY_INPUTORDER, PackageGenericBuildInfo, \
   PackageInstalledBuildInfo, PackageBuildingBuildInfo, PackageFailedBuildInfo, PackageNot_For_UsBuildInfo, \
   PackageDep_WaitBuildInfo, PackageDep_Wait_RemovedBuildInfo, PackageUploadedBuildInfo, \
   PackageNeeds_BuildBuildInfo, PackageFailed_RemovedBuildInfo

time_fmt_string = '%Y-%m-%d %H:%M:%S'
list_line_breaker = '<li class="empty"><br /></li>\n'
_log = logging.getLogger('dtth.write')

class StatsOutput:
   status_string = 'statistics'

def header_write(target, status_string, packagecount, timestamp, sourcefilename):
   timestamp_string = timestamp.strftime(time_fmt_string)
   target.write('''<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
 <head>
  <title>%(sourcefilename)s %(status_string)s -- %(timestamp_string)s</title>
  <link rel="stylesheet" href="http://buildd.net/builddnet.css" type="text/css" />
 </head>
 <body>
  <h1>%(status_string)s -- %(packagecount)d -- %(timestamp_string)s %(sourcefilename)s</h1>
   <hr />
   <ul>
''' % locals()
   )
   target.flush()


def footer_write(target):
   target.write('''
   </ul>
 </body>
</html>
''')
   target.flush()


def html_write(target, output_data, packageinfotype, packageinfos, timestamp, sourcefilename, packageinfos_all):
   header_write(target, packageinfotype.status_string, len(packageinfos), timestamp, sourcefilename)
   if (packageinfos):
      html_writer = html_writers[packageinfotype]

      if (packageinfotype == PackageNeeds_BuildBuildInfo):
         if (output_data == SORTBY_INPUTORDER):
            packageinfo_helplist = [(packageinfo.index, packageinfo) for packageinfo in packageinfos]
            packageinfo_helplist.sort()
            packageinfos = [element[1] for element in packageinfo_helplist]
            extra_separator = ''
         else:
            if (output_data != SORTBY_NAMESTRING):
               _log.log(40, 'Unable to interpret output_data %r for packageinfotype %r; falling back to sorting by namestring.' % (output_data, packageinfotype))
            packageinfos.sort()
            extra_separator = list_line_breaker

         html_writer(target, packageinfos, sort=False, extra_separator=extra_separator)
      else:
         html_writer(target, packageinfos, packageinfos_all)
   else:
      #necessary to keep the document valid
      target.write('<li class="empty">\n</li>\n')

   footer_write(target)

def html_write_generic(target, packageinfos, packageinfos_all):
   packageinfos_write_generic(target, packageinfos)


def packageinfos_write_generic(target, packageinfos, package_start='<li class="packageinfo">', package_finish='</li>\n', extra_separator=list_line_breaker, sort=True):
   packagenamestart_last = None
   if (sort):
      packageinfos.sort()
   for packageinfo in packageinfos:
      if (packageinfo.name):
         if ((packagenamestart_last) and (packageinfo.name[0] != packagenamestart_last)):
            target.write(extra_separator)

         packagenamestart_last = packageinfo.name[0]
      target.write('%s%s' % (package_start, packageinfo.html_return()))
      target.write(package_finish)
      target.flush()


def html_write_data(target, packageinfos, packageinfos_all):
   packageinfos_write_generic(target, packageinfos)


def html_write_building(target, packageinfos, packageinfos_all):
   hosts = {}
   for packageinfo in packageinfos:
      if not (packageinfo.host in hosts):
         hosts[packageinfo.host] = []
      hosts[packageinfo.host].append(packageinfo)

   hosts_list = hosts.keys()
   hosts_list.sort()

   for host in hosts_list:
      target.write('<li class="buildhost_group">%s<hr />\n<ul>\n' % (host,))
      packageinfos_write_generic(target, hosts[host])
      target.write('</ul>\n<br /></li>\n')

def html_write_depwait(target, packageinfos, packageinfos_all):
   dependencies = {}
   for packageinfo in packageinfos:
      if (not packageinfo.dependencies):
         package_dependencies = (None,)
      else:
         package_dependencies = packageinfo.dependencies
      for dependency in package_dependencies:
         if not (dependency in dependencies):
            dependencies[dependency] = []
         dependencies[dependency].append(packageinfo)

   dependency_list = dependencies.keys()
   dependency_list.sort()

   for depended_string in dependency_list:
      target.write('<li class="dependency">\n')
      if (depended_string in packageinfos_all):
         target.write(packageinfos_all[depended_string].link_return_buildphp()+' is needed by:')
      else:
         if (depended_string is None):
             target.write('Package(s) with Dep-Wait set, but without a given package name:') 
         else:
             target.write(str(depended_string))
             target.write(' is needed by:')
      target.write('<ul>\n')
      for packageinfo in dependencies[depended_string]:
         if (depended_string != None):
            packageinfo_string = packageinfo.html_return_extended(depended_string)
         else:
            packageinfo_string = packageinfo.html_return()

         target.write('<li class="packageinfo">%s</li>\n' % (packageinfo_string))
      target.write('</ul><br /><br /></li>')

def html_write_stats(target, packageinfos, packageinfos_all):
   packageinfos_by_class = {}
   for html_write_class in html_writers:
      if (issubclass(html_write_class, PackageGenericBuildInfo)):
         packageinfos_by_class[html_write_class] = []
      
   for packageinfo in packageinfos:
      if not (packageinfo.__class__ in packageinfos_by_class):
         packageinfos_by_class[packageinfo.__class__] = []

      packageinfos_by_class[packageinfo.__class__].append(packageinfo)

   packageinfo_classes_sorted = packageinfos_by_class.keys()
   packageinfo_classes_sorted.sort()

   for packageinfo_class in packageinfo_classes_sorted:
      packageinfos_relevant = packageinfos_by_class[packageinfo_class]
      packageinfos_relevant_count = len(packageinfos_relevant)
      target.write('<li class="build_status">%s: %d\n' % (packageinfo_class.status_string, packageinfos_relevant_count))

      packageinfos_relevant_hosts = {}
      for packageinfo in packageinfos_relevant:
         if not (packageinfo.host in packageinfos_relevant_hosts):
            packageinfos_relevant_hosts[packageinfo.host] = 1
         else:
            packageinfos_relevant_hosts[packageinfo.host] += 1

      if ((packageinfos_relevant_count > 0) and ((not (None in packageinfos_relevant_hosts)) or (packageinfos_relevant_hosts[None] < packageinfos_relevant_count))):
         #We have at least one packageinfo that we know a host to.
         target.write('<ul>\n')
         packageinfos_relevant_hosts_sorted = packageinfos_relevant_hosts.keys()
         packageinfos_relevant_hosts_sorted.sort()
         for packageinfo_host in packageinfos_relevant_hosts_sorted:
            if (packageinfo_host is None):
               packageinfo_host_output = 'Unknown'
            else:
               packageinfo_host_output = packageinfo_host
            target.write('<li class="buildhost_single">%s: %d</li>\n' % (packageinfo_host_output, packageinfos_relevant_hosts[packageinfo_host]))
         target.write('</ul>\n')

      target.write('<br /><br /></li>')
   
   target.write('</ul>\n<ul>\n')
   packageinfo_count = len(packageinfos)
   percentage_fmt_string = '%.2f'
   percentage_width = len(percentage_fmt_string % 100.0)
   count_fmt_string = '(%d)'
   packageinfo_count_width = len(count_fmt_string % packageinfo_count)
   
   for (group_count, description) in (
      (len(packageinfos_by_class[PackageInstalledBuildInfo]), 'up-to-date [Installed]'),
      (len(packageinfos_by_class[PackageInstalledBuildInfo]) + len(packageinfos_by_class[PackageUploadedBuildInfo]), 'up-to-date including uploaded [Installed, Uploaded]'),
      (len(packageinfos_by_class[PackageNeeds_BuildBuildInfo]), 'need building [Needs-Build]'),
      (len(packageinfos_by_class[PackageBuildingBuildInfo]), 'currently building [Building]'),
      (len(packageinfos_by_class[PackageFailedBuildInfo]) + len(packageinfos_by_class[PackageDep_WaitBuildInfo]), 'failed/dep-wait [Failed, Dep-Wait]'),
      (len(packageinfos_by_class[PackageDep_Wait_RemovedBuildInfo]) + len(packageinfos_by_class[PackageFailed_RemovedBuildInfo]), 'old failed/dep-wait [Dep-Wait-Removed, Failed-Removed]'),
      (len(packageinfos_by_class[PackageNot_For_UsBuildInfo]), 'need porting or cause the buildd serious grief [Not-For-Us]')
   ):
      if (packageinfo_count == 0):
         #don't try to divide through it...
         percentage_string = '?'
      else:
         percentage_string = percentage_fmt_string % ((float(group_count)/packageinfo_count)*100,)
      count_string = count_fmt_string % (group_count,)
       
      target.write('<li class="stats_percentage">%*s%% %*s %s</li>' % (percentage_width, percentage_string, packageinfo_count_width, count_string, description))


html_writers = {
   PackageInstalledBuildInfo:html_write_generic,
   PackageBuildingBuildInfo:html_write_building,
   PackageFailedBuildInfo:html_write_data,
   PackageNot_For_UsBuildInfo:html_write_data,
   PackageDep_WaitBuildInfo:html_write_depwait,
   PackageDep_Wait_RemovedBuildInfo:html_write_data,
   PackageUploadedBuildInfo:html_write_generic,
   PackageNeeds_BuildBuildInfo:packageinfos_write_generic,
   PackageFailed_RemovedBuildInfo:html_write_data,
   StatsOutput:html_write_stats,
}

