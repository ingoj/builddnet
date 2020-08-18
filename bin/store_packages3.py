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
# store_packages3.py comes with ABSOLUTELY NO WARRANTY
#


import psycopg
from os import linesep
from string import *
#from time import *
from copy import copy
import sys, os
import popen2
from tempfile import *
import rfc822
#from zlib import *
import zlib
try:
	import cStringIO
	StringIO=cStringIO
except:
	import StringIO

pid=os.getpid()

if len(sys.argv)<>4:
	print "usage: "+sys.argv[0]+" <flavour> <mode> <file>"
	print "  flavour : can be either 'unstable', 'etchbpo', 'experimental', ..."
	print "  mode    : can be either 'sources' or 'packages'"
	print "  limit   : full || limited || retry"
	sys.exit(1)
else:
	flavour	= sys.argv[1]
	mode 	= sys.argv[2]
	limit 	= sys.argv[3]

rdsn = "dbname=buildd host=db.windfluechter.net user=builddnet"
rdb = psycopg.connect(rdsn)
rcsr = rdb.cursor()

dsn = "dbname=buildd host=db.windfluechter.net user=builddnet"
db = psycopg.connect(dsn)
#db.set_transaction_level('transaction_read_committed') #psycopg2 stuff
csr = db.cursor()
#csr.autocommit(0)

packpath = "/home/builddnet/%s/packages" % flavour
archs=['alpha', 'amd64', 'arm', 'armeb', 'hppa', 'hurd-i386', 'i386', 'ia64', 'kfreebsd-amd64', 'kfreebsd-i386', 'm68k', 'mips', 'mipsel', 'powerpc', 's390', 'sparc']
#archs=['amd64', 'armeb']
discPackages={} # packages held in memory instead of disk
procPackages={} # package currently processed
chanPackages={} # packages that have been changed

rcsr.execute("set client_encoding to unicode")
csr.execute("set client_encoding to unicode")

#mode="packages"
	
branches = ['main', 'contrib', 'non-free']
#branches = ['contrib', 'non-free']
numupd=0
numinit=0
i=0
#outf = open("packages.sql", "w+")

def scanSources(branch):
	global f, mode, numupd, numinit, packpath, flavour
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
	global f, mode, numupd, numinit, archs, i, packpath, discPackages, flavour
	#i=0

	arch={}
	#
	# open the $arch_$branch_Package files and store them into a list
	#
	for a in archs:
		fname = packpath+"/%s_%s_Packages" % (a, branch)
		#print fname
		try:
			#print arch
			# get the filehandle for that Packages file
			arch[a] = open(fname, 'r')
			#arch.sort()
			#print arch
		except:
			pass
	#print arch
	# sort the list to process it alphabetically (alpha, amd64, arm, ... s390, sparc)
	sorted=arch.keys()
	sorted.sort()
	#print sorted
	#sys.exit()
	#
	# walk through the sorted arch list
	#
	for a in sorted:
		print a
		if i>-1:
		#try:
			# assign the filehandle to a variable. apparently unneccessary, but easier to read
			f = arch[a]
			packages=[]
			pline=""
			#
			# rfc822 module is only able to process until a blank line, so we parse the file line for line
			# until a blank line occurs and pass it then to the next step
			#
			for line in f:
				#print line
				if len(line)>1:
					pline=pline+line
					if line.count('Package:'):
						#print line 
						package=strip(split(line, ":")[1])
						#print package
				else:
					#print "in else"
					file = StringIO.StringIO(pline)
					procPackages[package]=pline
					#print i, len(procPackages)
					#readRFC822Packages(file, a, branch)
					readRFC822Packages(package, a, branch)
					pline=""
					i=i+1
				#if i==10: 
					#print procPackages
					#sys.exit()
			f.close()
	#print len(procPackages)
	#sortedPackages=chanPackages.keys
	#sortedPackages.sort()
	#print "before writing to disk..."
	#print len(chanPackages)
	for z in chanPackages:
		#print z, zlib.decompress(discPackages[z])
		print packpath+"/"+branch+"/"+z
		c = open(packpath+"/"+branch+"/"+z, 'w+')
		c.write(str(zlib.decompress(discPackages[z])))
		c.close

		#except IOError, e:
		#	print e 
		#	print "Error: cannot open file for", branch, a 
	#f.close()
	return
	
#def readRFC822Packages(filename, arch, branch):
def readRFC822Packages(package, arch, branch):
	global csr, db, numupd, numinit, outf, packpath, discPackages, procPackages, flavour
	#f = open(filename, 'r+')
	#print "in readrfc822Packages"
	#f = filename
	m=rfc822.Message(StringIO.StringIO(procPackages[package]))
	keys=m.keys()
	#print len(procPackages)
	n=""
	pline=""
	#komma=""
	#sqladd=""
	#sqlfields=""
	#sqlvalues=""
	#if arch!="alpha": print arch, package
	if discPackages.has_key(package):
		pass
		#print "in if discPackages"
		#s = StringIO.StringIO(discPackages[package])
		#print zlib.decompress(discPackages[package])
	else:
		sfile = packpath+"/%s/%s" % ( branch, package)
		try:
			#print "try:"
			s = open(sfile, 'r+')
			discPackages[package]=zlib.compress(s.read())
		except Exception, e:
			print "except:", e
			s = open(sfile, 'w+')
			s.write(str(m))
			s.flush()
			s.close()
			s = open(sfile, 'r+')
			discPackages[package]=zlib.compress(s.read())
	
	try:
		n = rfc822.Message(StringIO.StringIO(zlib.decompress(discPackages[package])))
		#print "in try", n
		#sys.exit()
	except TypeError:
		print type(discPackages[package]), discPackages[package]
		n=zlib.decompress(str(copy(discPackages[package])))
			
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
			#s.write(k+": "+nvalue+linesep)
			#s.flush()
			#print k
			#foo=zlib.decompress(str(discPackages[k]))
			#print foo
			discPackages[k]=nvalue
		#print kvalue
		#print nvalue
		if k in archlist:
			#print "in archlist:", k
			nfield = arch+"_"+k
			#print nfield
			if n.has_key(nfield):
				nvalue=n[nfield]
				if kvalue<>nvalue:
					#print package,"has changed.",nfield,"updated:",nvalue,"->",kvalue
					n[nfield]=kvalue
					#os.unlink(sfile)
					#s=open(sfile, 'w+')
					discPackages[package]=zlib.compress(str(copy(n)))
					chanPackages[package]=package
					#print len(chanPackages)
					#print "mark 1"
					#s.write(str(n))
					#s.flush()
					#print discPackages[package]
					#sys.exit()
			else:
				foo = "%s: %s" % ( nfield, kvalue )
				#s.write(foo+linesep)
				n[nfield]=kvalue
				#print n
				discPackages[package]=zlib.compress(str(copy(n)))
				chanPackages[package]=package
				#print "new field", package, nfield
	try:
		s.close()
	except UnboundLocalError:
		pass
	#f.close()
	
	#sys.exit()
	
def processPackages(branch):
	global f, mode, numupd, numinit, packpath, limit, flavour
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
		if (p == """^[aA].*" -- Package Version'""" or p == "--"):
			pass
		else:
			if limit=="retry":
				package=replace(replace(os.path.basename(p), ".", "", 1), ".retry", "")
				print "retrying", package
				rmretry="rm "+packpath+"/"+branch+"/."+package+".retry"
				os.system(rmretry)
			else:
				package=os.path.basename(p)
		#print package
			path = packpath+"/%s/%s" % (branch, package)
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
		#print discPackages
		#sys.exit()
			storeRFC822Packages(f, branch)
			pline=""	
			f.close()
	sqlcmd = "commit"
	csr.execute(sqlcmd)
	db.commit()
	return

def storeRFC822Packages(filename, branch):
	global csr, db, numupd, numinit, outf, limit, packpath, flavour
	#f = open(filename, 'r+')
	f = filename
	m=rfc822.Message(f)
	#print m
	#print flavour
	keys=m.keys()
	try: 
		package=m['package']
	except Exception, e: 
		print "!!!", e
		print "!!!", filename
		print m
		sys.exit()
	if m.has_key('source'):
		msource=split(m['source'], " ")[0]
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
	sqlcmd = "select p.maintainer, s.id from packages p, sources s where p.package='%s' and s.package='%s' and p.flavour=s.flavour and p.flavour='%s'" % (package, msource, flavour)
	print "!!!", sqlcmd
	rcsr.execute(sqlcmd)
	try:
		dbid = rcsr.fetchone()[1]
		print dbid
		foo = int(dbid)
		#print dbid
		mode="update"
	except:
		print "!!! mode init", package
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
		sqlcmd = "update packages set %s where package='%s' and flavour='%s'" % (sqladd, package, flavour)
		filenamesqlcmd = "update packagefilename set %s where package='%s' and flavour='%s'" % (filenamesqladd, package, flavour)
		installedsizesqlcmd = "update packageinstalledsize set %s where package='%s' and flavour='%s'" % (installedsizesqladd, package, flavour)
		md5sumsqlcmd = "update packagemd5sum set %s where package='%s' and flavour='%s'" % (md5sumsqladd, package, flavour)
		versionsqlcmd = "update packageversion set %s where package='%s' and flavour='%s'" % (versionsqladd, package, flavour)
	elif mode=="init":
		if  not sqlfields.count('source'):
			getsql = "select id from sources where package='%s' and flavour='%s'" % (package, flavour)
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
		sqlcmd ="insert into packages (%s, flavour) values (%s, '%s')" % ( sqlfields, sqlvalues, flavour)
		filenamesqlcmd ="insert into packagefilename (%s, flavour) values (%s, '%s')" % ( filenamesqlfields, filenamesqlvalues, flavour)
		installedsizesqlcmd ="insert into packageinstalledsize (%s, flavour) values (%s, '%s')" % ( installedsizesqlfields, installedsizesqlvalues, flavour)
		md5sumsqlcmd ="insert into packagemd5sum (%s, flavour) values (%s, '%s')" % ( md5sumsqlfields, md5sumsqlvalues, flavour)
		versionsqlcmd ="insert into packageversion (%s, flavour) values (%s, '%s')" % ( versionsqlfields, versionsqlvalues, flavour)
		print "new package inserted: %s" % package
	#print sqlcmd
	print filenamesqlcmd
	print installedsizesqlcmd
	print md5sumsqlcmd
	print versionsqlcmd
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
		#sys.exit()
	#out=sqlcmd+";\n"
	#outf.write(out)
	f.close
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	#db.commit()
	#sys.exit()
	return


def readRFC822Sources(filename, branch, mode):
	global csr, db, numupd, numinit, flavour
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
	#print package
	#if mode=="update":
	sqlcmd = "select files from sources where package='%s' and flavour='%s'" % (package, flavour)
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
		
	if mode=="update":
		numupd=numupd+1
		sqladd=sqladd+", branch='%s'" % branch
		sqlcmd = "update sources set %s where package='%s' and flavour='%s'" % (sqladd, package, flavour)
	elif mode=="init":
		sqlfields = sqlfields+", branch"
		sqlvalues = sqlvalues+", '%s'" % branch
		numinit=numinit+1
		sqlcmd ="insert into sources (%s, flavour) values (%s, '%s')" % ( sqlfields, sqlvalues, flavour)
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
		#try:
			#try:
		if not limit=="retry":
			scanPackages(branch)
		os.system("touch /home/builddnet/bin/.maintenance")
		processPackages(branch)
			#except Exception, e:
			#	print e
			#raise EOFError
		#except EOFError, e:
		os.system("rm /home/builddnet/bin/.maintenance")
		print "  "+branch+" packages updated \t:", numupd
		print "  "+branch+" packages inserted\t:", numinit
		tpu=tpu+numupd
		tpi=tpi+numinit
		numupd=0
		numinit=0
		chanPackages={}
		#discPackages={}
		#procPackages={}
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	#db.commit()


print "=====================================\nTotals:"
print "Sources updated  :", tsu
print "Sources inserted :", tsi
print "Packages updated :", tpu
print "Packages inserted:", tpi
print "=====================================\nOverall:"
print "Updated          :", tsu+tpu
print "Inserted         :", tsi+tpi
print

print "Finished."
#db.commit()
db.close()
#outf.close()
#os.system("kill "+str(pid))
sys.exit()

