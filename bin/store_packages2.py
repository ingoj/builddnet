#!/usr/bin/python
#
# Copyright (c) 2005-2006, Ingo Juergensmann <ij@buildd.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# store_packages2.py comes with ABSOLUTELY NO WARRANTY
#
#

import psycopg
from os import linesep
from string import *
#from time import *
import sys, os
import popen2
from tempfile import *
import rfc822
try:
	import cStringIO
	StringIO=cStringIO
except:
	import StringIO

rdsn = "dbname=buildd user=builddnet"
rdb = psycopg.connect(rdsn)
rcsr = rdb.cursor()

dsn = "dbname=buildd user=builddnet"
db = psycopg.connect(dsn)
#db.set_transaction_level('transaction_read_committed') #psycopg2 stuff
csr = db.cursor()
#csr.autocommit(0)

packpath = "/home/builddnet/packages"
archs=['alpha', 'amd64', 'arm', 'armeb', 'hppa', 'hurd-i386', 'i386', 'ia64', 'kfreebsd-i386', 'm68k', 'mips', 'mipsel', 'powerpc', 's390', 'sparc']
#archs=['amd64', 'armeb']

if len(sys.argv)<>3:
	print "usage: "+sys.argv[0]+" <mode> <file>"
	print "  mode  : can be either 'sources' or 'packages'"
	print "  limit : full || limited || retry"
	sys.exit(1)
else:
	mode = sys.argv[1]
	limit = sys.argv[2]
#mode="packages"
	
branches = ['main', 'contrib', 'non-free']
numupd=0
numinit=0
i=0
#outf = open("packages.sql", "w+")

def scanSources(branch):
	global f, mode, numupd, numinit, packpath
	i=0

	path = packpath+"/%s_Sources" % branch
	try:
		f = open(path, 'r+')
	except: 
		print "File does not exist:", path
		return
		
	packages=[]
	pline=""
	for line in f:
		if len(line)>1:
			pline=pline+line
		else:
			#print pline
			file = StringIO.StringIO(pline)
			readRFC822Sources(file, branch, mode)
			pline=""	
	return


def scanPackages(branch):
	global f, mode, numupd, numinit, archs, i, packpath
	#i=0

	arch={}
	for a in archs:
		fname = packpath+"/%s_%s_Packages" % (a, branch)
		try:
			#print arch
			arch[a] = open(fname, 'r')
			#arch.sort()
			#print arch
		except:
			pass
	#print arch
	sorted=arch.keys()
	sorted.sort()
	#print sorted
	#sys.exit()
	for a in sorted:
		print a
		try:
			f = arch[a]
			packages=[]
			pline=""
			for line in f:
				#print line
				if len(line)>1:
					pline=pline+line
				else:
					file = StringIO.StringIO(pline)
					readRFC822Packages(file, a, branch)
					pline=""
					i=i+1
		except: 
			print "Error: cannot open file for", branch, a 
	return
	
def processPackages(branch):
	global f, mode, numupd, numinit, packpath, limit
	i=0
	packages=[]

	path = packpath+"/%s/" % branch
	#cmd = "cd %s && find . -type f -daystart -mtime 0"  % path 
	if limit=="retry":
		cmd = 'cd %s && find . -type f -iname ".*.retry"'  % (path)
	else:
		cmd = "find %s -type f -newer %s/control"  % (path, packpath)
	r, w = popen2.popen2(cmd)

	packages=split(r.read())
	r.close()
	packages.sort()
	#print packages
	sqlcmd = "begin work"
	csr.execute(sqlcmd)
	for p in packages:
		if limit=="retry":
			package=replace(replace(os.path.basename(p), ".", "", 1), ".retry", "")
			print "retrying", package
			rmretry="rm "+packpath+"/"+branch+"/."+package+".retry"
			os.system(rmretry)
		else:
			package=os.path.basename(p)
		#print package
		path = packpath+"/%s/%s" % (branch, package)
		#print path
		f = open(path, 'r')
		#packages=[]
		pline=""
		#for line in f:
		#	if len(line)>1:
		#		pline=pline+line
		#	else:
		#pline=
		#print pline
		#file = StringIO.StringIO(pline)
		storeRFC822Packages(f, branch)
		pline=""	
		f.close()
	sqlcmd = "commit"
	csr.execute(sqlcmd)
	db.commit()
	return


def readRFC822Packages(filename, arch, branch):
	global csr, db, numupd, numinit, outf, packpath
	#f = open(filename, 'r+')
	f = filename
	m=rfc822.Message(f)
	keys=m.keys()
	n=""
	pline=""
	#komma=""
	#sqladd=""
	#sqlfields=""
	#sqlvalues=""
	package=m['package']
	#print package
	sfile = packpath+"/%s/%s" % ( branch, package)
	try:
		#print "try:"
		s = open(sfile, 'r+')
	except:
		#print "except:"
		s = open(sfile, 'w+')
		s.write(str(m))
		s.flush()
		s.close()
		s = open(sfile, 'r+')
	n = rfc822.Message(s)
	
	nkeys = n.keys()
	archlist = ['version', 'md5sum', 'filename', 'installed-size']
	for k in keys:
		#print k,
		try:
			kvalue = m[k] 
		except: 
			pass
		try:
			nvalue = n[k]  
		except:
			nvalue=kvalue
			s.write(k+": "+nvalue+linesep)
			s.flush()
		#print kvalue
		#print nvalue
		if k in archlist:
			#print "in archlist:", k
			nfield = arch+"_"+k
			if n.has_key(nfield):
				if kvalue<>nvalue:
					#print package,"has changed.",nfield,"updated:",nvalue,"->",kvalue
					n[nfield]=kvalue
					os.unlink(sfile)
					s=open(sfile, 'w+')
					#print n
					s.write(str(n))
					s.flush()
					#sys.exit()
			else:
				foo = "%s: %s" % ( nfield, kvalue )
				s.write(foo+linesep)
	s.close()
	f.close()
	
	#sys.exit()
	
def storeRFC822Packages(filename, branch):
	global csr, db, numupd, numinit, outf, limit, packpath
	#f = open(filename, 'r+')
	f = filename
	m=rfc822.Message(f)
	#print m
	keys=m.keys()
	package=m['package']
	if m.has_key('source'):
		msource=m['source']
	else:
		msource=package
	#print msource
	sqladd=""
	sqlfields=""
	sqlvalues=""
	versionsqladd="package='%s'" % package
	versionsqlfields="package"
	versionsqlvalues="'%s'" % package
	filenamesqladd="package='%s'" % package
	filenamesqlfields="package"
	filenamesqlvalues="'%s'" % package
	md5sumsqladd="package='%s'" % package
	md5sumsqlfields="package"
	md5sumsqlvalues="'%s'" % package
	installedsizesqladd="package='%s'" % package
	installedsizesqlfields="package"
	installedsizesqlvalues="'%s'" % package
	komma=""
	fkomma=", "
	ikomma=", "
	mkomma=", "
	vkomma=", "
	#print package
	#sqlcmd = "start transaction isolation level read committed"
	#csr.execute(sqlcmd)
	#if mode=="update":  select p.maintainer, s.id from packages p, sources s where p.package='locales' and s.package='glibc'
	#sqlcmd = "select maintainer from packages where package='%s'" % (package)
	sqlcmd = "select p.maintainer, s.id from packages p, sources s where p.package='%s' and s.package='%s'" % (package, msource)
	rcsr.execute(sqlcmd)
	try:
		dbid = rcsr.fetchone()
		#print dbid
		mode="update"
	except:
		mode="init"
	for key in keys:
		mvalue=strip(replace(replace(m[key], "|", "!"), "'", ""))
		if mode=="update":
			if key.count("description"):
				#pass
				shortdesc, longdesc = split(mvalue, "\n", 1)
				sqladd = sqladd+komma+"description='"+strip(shortdesc)+"'"
				sqladd = sqladd+komma+"longdescription='"+longdesc+"'"
				komma=", "	
			elif key.count("_filename"):
				varch = replace(split(key, "_")[0], "-", "")
				filenamesqladd = filenamesqladd+fkomma+str(varch)+"='"+mvalue+"'" 
				fkomma=", "	
			elif key.count("_installed-size"):
				varch = replace(split(key, "_")[0], "-", "")
				installedsizesqladd = installedsizesqladd+ikomma+str(varch)+"='"+mvalue+"'" 
				ikomma=", "	
			elif key.count("_md5sum"):
				varch = replace(split(key, "_")[0], "-", "")
				md5sumsqladd = md5sumsqladd+mkomma+str(varch)+"='"+mvalue+"'" 
				mkomma=", "	
			elif key.count("_version"):
				varch = replace(split(key, "_")[0], "-", "")
				versionsqladd = versionsqladd+vkomma+str(varch)+"='"+mvalue+"'" 
				vkomma=", "	
				#print "version update:", varch, mvalue, versionsqladd
			elif key.count("source"):
				#getsql = "select id from sources where package='%s'" % split(mvalue, " ", 1)[0]
				#print getsql
				#try:
					#csr.execute(getsql)
					#getsqlresult = csr.fetchone()[0]
				try: 
					getsqlresult=int(dbid)
					sqladd = sqladd+komma+"source='%s'" % getsqlresult
				except: 
					#getsqlresult = 0
					sqladd = sqladd+komma+"source=Null" #% getsqlresult
				komma=", "	
			elif (key.count("installed-size") or key.count("md5sum") or key.count("filename") or key.count("version")):
				pass
			else:
				#pass 
				sqladd = sqladd+komma+replace(replace(key, "-", ""), "binary", "binaries")+"='"+mvalue+"'"
				komma=", "	
		elif mode=="init":
			if key.count("description"): 
				shortdesc, longdesc = split(mvalue, "\n", 1)
				sqlfields = sqlfields+komma+"description"
				sqlvalues = sqlvalues+komma+"'%s'" % strip(shortdesc)
				sqlfields = sqlfields+komma+"longdescription"
				sqlvalues = sqlvalues+komma+"'%s'" % longdesc
				komma=", "	
			elif key.count("_filename"):
				varch = replace(split(key, "_")[0], "-", "")
				filenamesqlfields = filenamesqlfields+fkomma+"%s" % varch
				filenamesqlvalues = filenamesqlvalues+fkomma+"'%s'" % mvalue
				fkomma=", "	
			elif key.count("_installed-size"):
				varch = replace(split(key, "_")[0], "-", "")
				installedsizesqlfields = installedsizesqlfields+ikomma+"%s" % varch
				installedsizesqlvalues = installedsizesqlvalues+ikomma+"'%s'" % mvalue
				ikomma=", "	
			elif key.count("_md5sum"):
				varch = replace(split(key, "_")[0], "-", "")
				md5sumsqlfields = md5sumsqlfields+mkomma+"%s" % varch
				md5sumsqlvalues = md5sumsqlvalues+mkomma+"'%s'" % mvalue
				mkomma=", "	
			elif key.count("_version"):
				varch = replace(split(key, "_")[0], "-", "")
				versionsqlfields = versionsqlfields+vkomma+"%s" % varch
				versionsqlvalues = versionsqlvalues+vkomma+"'%s'" % mvalue
				vkomma=", "	
				#print "version init:", varch, mvalue
			elif key.count("source"):
				getsql = "select id from sources where package='%s'" % split(mvalue, " ", 1)[0]
				try:
					rcsr.execute(getsql)
					getsqlresult = rcsr.fetchone()[0]
				except:
					getsqlresult = 0
				sqlfields = sqlfields+komma+"source"
				sqlvalues = sqlvalues+komma+"'%s'" % getsqlresult				
				komma=", "	
			elif (key.count("installed-size") or key.count("md5sum") or key.count("filename") or key.count("version")):
				pass
			else:
				sqlfields = sqlfields+komma+replace(replace(key, "binary", "binaries"), "-", "")
				sqlvalues = sqlvalues+komma+"'%s'" % replace(replace(m[key], "|", "!"), "'", "")
				komma=", "	
		
	if mode=="update":
		numupd=numupd+1
		if  not sqladd.count('source'):
			getsql = "select id from sources where package='%s'" % package
			try:
				rcsr.execute(getsql)
				getsqlresult = rcsr.fetchone()[0]
			except: 
				getsqlresult = 0 
			sqladd=sqladd+", source='%s'" % getsqlresult
		sqladd=sqladd+", branch='%s'" % branch
		sqlcmd = "update packages set %s where package='%s'" % (sqladd, package)
		filenamesqlcmd = "update packagefilename set %s where package='%s'" % (filenamesqladd, package)
		installedsizesqlcmd = "update packageinstalledsize set %s where package='%s'" % (installedsizesqladd, package)
		md5sumsqlcmd = "update packagemd5sum set %s where package='%s'" % (md5sumsqladd, package)
		versionsqlcmd = "update packageversion set %s where package='%s'" % (versionsqladd, package)
	elif mode=="init":
		if  not sqlfields.count('source'):
			getsql = "select id from sources where package='%s'" % package
			try: 
				rcsr.execute(getsql)
				getsqlresult = rcsr.fetchone()[0]
			except:
				getsqlresult=0
			sqlfields = sqlfields+", source"
			sqlvalues = sqlvalues+", '%s'" % getsqlresult
		sqlfields = sqlfields+", branch"
		sqlvalues = sqlvalues+", '%s'" % branch
		numinit=numinit+1
		sqlcmd ="insert into packages (%s) values (%s)" % ( sqlfields, sqlvalues)
		filenamesqlcmd ="insert into packagefilename (%s) values (%s)" % ( filenamesqlfields, filenamesqlvalues)
		installedsizesqlcmd ="insert into packageinstalledsize (%s) values (%s)" % ( installedsizesqlfields, installedsizesqlvalues)
		md5sumsqlcmd ="insert into packagemd5sum (%s) values (%s)" % ( md5sumsqlfields, md5sumsqlvalues)
		versionsqlcmd ="insert into packageversion (%s) values (%s)" % ( versionsqlfields, versionsqlvalues)
		print "new package inserted: %s" % package
	#print sqlcmd
	#print filenamesqlcmd
	#print installedsizesqlcmd
	#print md5sumsqlcmd
	#print versionsqlcmd
	try:
		if limit=="full" or limit=="retry":
			csr.execute(sqlcmd)
			csr.execute(filenamesqlcmd)
			csr.execute(md5sumsqlcmd)
		csr.execute(installedsizesqlcmd)
		csr.execute(versionsqlcmd)
	except Exception, e:
		print package+"Exception during SQL:", e
		excmd="touch "+packpath+"/"+branch+"/."+package+".retry"
		os.system(excmd)
		sys.exit()
	#out=sqlcmd+";\n"
	#outf.write(out)
	f.close
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	#db.commit()
	#sys.exit()
	return


def readRFC822Sources(filename, branch, mode):
	global csr, db, numupd, numinit
	f = filename
	#f = open(filename, 'r+')
	m=rfc822.Message(f)
	#print m
	keys=m.keys()
	komma=""
	sqladd=""
	sqlfields=""
	sqlvalues=""
	package=m['package']
	#print "!!! %s:" %package
	#if mode=="update":
	sqlcmd = "select files from sources where package='%s'" % package
	rcsr.execute(sqlcmd)
	try:
		sqlresult = rcsr.fetchone()[0]
		mode="update"
	except:
		mode="init"
	for key in keys:
		if mode=="update":
			sqladd = sqladd+komma+replace(replace(key, "-", ""), "binary", "binaries")+"='"+replace(replace(m[key], "|", "!"), "'", "")+"'"
		elif mode=="init":
			sqlfields = sqlfields+komma+replace(replace(key, "binary", "binaries"), "-", "")
			sqlvalues = sqlvalues+komma+"'%s'" % replace(replace(m[key], "|", "!"), "'", "")
		komma=", "	
		if package=="gcc-4.0": print key, len(m[key])
				
	if mode=="update":
		numupd=numupd+1
		sqladd=sqladd+", branch='%s'" % branch
		sqlcmd = "update sources set %s where package='%s'" % (sqladd, package)
	elif mode=="init":
		sqlfields = sqlfields+", branch"
		sqlvalues = sqlvalues+", '%s'" % branch
		numinit=numinit+1
		sqlcmd ="insert into sources (%s) values (%s)" % ( sqlfields, sqlvalues)
		print "New source inserted:", package
	#print sqlcmd
	csr.execute(sqlcmd)
	f.close
	return
		


#
# Main
#		

tsu=0
tsi=0
tpu=0
tpi=0
if mode=="sources":
	#branch = split(filename, "_")[0]
	#print
	print "Source stats:"
	#sqlcmd = "begin work"
	#csr.execute(sqlcmd)
	for branch in branches:
		scanSources(branch)
		print "  "+branch+" sources updated  \t:", numupd
		print "  "+branch+" sources inserted \t:", numinit
		tsu=tsu+numupd
		tsi=tsi+numinit
		numupd=0
		numinit=0
	sqlcmd = "commit"
	csr.execute(sqlcmd)
	db.commit()
elif mode=="packages":
	#arch, branch, foo = split(filename, "_")
	branch="main"
	arch=archs
	#print arch, branch, foo
	print "Package stats:"
	#for arch in archs: 
	#sqlcmd = "start transaction isolation level serializable"
	#sqlcmd = "begin work"
	#csr.execute(sqlcmd)
	for branch in branches:
	#print branch, arch
		try:
			try:
				if not limit=="retry":
					scanPackages(branch)
				os.system("touch /home/builddnet/bin/.maintenance")
				processPackages(branch)
			except Exception, e:
				print e
			raise EOFError
		except EOFError, e:
			os.system("rm /home/builddnet/bin/.maintenance")
		print "  "+branch+" packages updated \t:", numupd
		print "  "+branch+" packages inserted\t:", numinit
		tpu=tpu+numupd
		tpi=tpi+numinit
		numupd=0
		numinit=0
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	db.commit()

	

print "=====================================\nTotals:"
print "Sources updated  :", tsu
print "Sources inserted :", tsi
print "Packages updated :", tpu
print "Packages inserted:", tpi
print "=====================================\nOverall:"
print "Updated          :", tsu+tpu
print "Inserted         :", tsi+tpi
print


db.commit()
db.close()
#outf.close()

