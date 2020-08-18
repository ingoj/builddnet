#!/usr/bin/python2.3 -OO

import psycopg
#from os import linesep
from string import *
#from time import *
import sys, os
#import popen2
from tempfile import *
import rfc822
try:
	import cStringIO
	StringIO=cStringIO
except:
	import StringIO

dsn = "dbname=buildd user=builddnet"
db = psycopg.connect(dsn)
csr = db.cursor()

#archs=['alpha', 'amd64', 'arm', 'armeb', 'hppa', 'hurd-i386', 'i386', 'ia64', 'm68k', 'mips', 'mipsel', 'powerpc', 's390', 'sparc']
#archs=['amd64', 'armeb']

if len(sys.argv)<>3:
	print "usage: "+sys.argv[0]+" <mode> <file>"
	print "  mode: can be either 'sources' or 'packages'"
	print "  file: sources/packages path/file to process"
	sys.exit(1)
else:
	mode = sys.argv[1]
	filename = sys.argv[2]

	
#branches = ['main', 'contrib', 'non-free']
numupd=0
numinit=0

#outf = open("packages.sql", "w+")

def scanSources(branch):
	global f, mode, numupd, numinit
	i=0
		
	path = "/home/builddnet/packages/%s_Sources" % branch
	f = open(path, 'r+')
	
	#sqlcmd = "begin work"
	#csr.execute(sqlcmd)

	packages=[]
	pline=""
	for line in f:
		if len(line)>1:
			pline=pline+line
		else:
			#print pline
			file = StringIO.StringIO(pline)
			#tmpfile=mktemp()
			#tf = open(tmpfile, 'w+')
			#tf.write(pline)
			#print tmpfile
			#tf.flush()
			readRFC822Sources(file, branch, mode)
			#tf.close
			#os.remove(tmpfile)
			pline=""	
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	#db.commit()
	return


def scanPackages(branch, arch):
	global f, mode, numupd, numinit
	i=0
	print arch 		
	path = "/home/builddnet/packages/%s_%s_Packages" % (arch, branch)
	try:
		f = open(path, 'r+')
	except: 
		print "Error: cannot open", path
		return
	packages=[]
	pline=""
	for line in f:
		#print line
		if len(line)>1:
			pline=pline+line
		else:
			file = StringIO.StringIO(pline)
			readRFC822Packages(file, arch, branch, mode)
			pline=""
	return
	
def readRFC822Packages(filename, arch, branch, mode):
	global csr, db, numupd, numinit, outf
	#f = open(filename, 'r+')
	f = filename
	m=rfc822.Message(f)
	keys=m.keys()
	komma=""
	sqladd=""
	sqlfields=""
	sqlvalues=""
	package=m['package']
	#print package
	#sqlcmd = "start transaction isolation level read committed"
	#csr.execute(sqlcmd)
	#if mode=="update":
	sqlcmd = "select filename from packages where package='%s'" % (package)
	csr.execute(sqlcmd)
	try:
		sqlresult = csr.fetchone()[0]
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
			elif key.count("version"):
				sqladd = sqladd+komma+str(arch)+"='"+mvalue+"'" 
			elif key.count("source"):
				getsql = "select id from sources where package='%s'" % split(mvalue, " ", 1)[0]
				#print getsql
				try:
					csr.execute(getsql)
					getsqlresult = csr.fetchone()[0]
					sqladd = sqladd+komma+"source='%s'" % getsqlresult
				except: 
					#getsqlresult = 0
					sqladd = sqladd+komma+"source=Null" #% getsqlresult
			else:
				#pass 
				sqladd = sqladd+komma+replace(replace(key, "-", ""), "binary", "binaries")+"='"+mvalue+"'"
		elif mode=="init":
			if key.count("description"): 
				shortdesc, longdesc = split(mvalue, "\n", 1)
				sqlfields = sqlfields+komma+"description"
				sqlvalues = sqlvalues+komma+"'%s'" % strip(shortdesc)
				sqlfields = sqlfields+komma+"longdescription"
				sqlvalues = sqlvalues+komma+"'%s'" % longdesc
			elif key.count("version"):
				sqlfields = sqlfields+komma+"%s" % arch
				sqlvalues = sqlvalues+komma+"'%s'" % mvalue
			elif key.count("source"):
				getsql = "select id from sources where package='%s'" % split(mvalue, " ", 1)[0]
				try:
					csr.execute(getsql)
					getsqlresult = csr.fetchone()[0]
				except:
					getsqlresult = 0
				sqlfields = sqlfields+komma+"source"
				sqlvalues = sqlvalues+komma+"'%s'" % getsqlresult				
			else:
				sqlfields = sqlfields+komma+replace(replace(key, "binary", "binaries"), "-", "")
				sqlvalues = sqlvalues+komma+"'%s'" % replace(replace(m[key], "|", "!"), "'", "")
		komma=", "	
		
	if mode=="update":
		numupd=numupd+1
		if  not sqladd.count('source'):
			getsql = "select id from sources where package='%s'" % package
			try:
				csr.execute(getsql)
				getsqlresult = csr.fetchone()[0]
			except: 
				getsqlresult = 0 
			sqladd=sqladd+", source='%s'" % getsqlresult
		sqladd=sqladd+", branch='%s'" % branch
		sqlcmd = "update packages set %s where package='%s'" % (sqladd, package)
	elif mode=="init":
		if  not sqlfields.count('source'):
			getsql = "select id from sources where package='%s'" % package
			try: 
				csr.execute(getsql)
				getsqlresult = csr.fetchone()[0]
			except:
				getsqlresult=0
			sqlfields = sqlfields+", source"
			sqlvalues = sqlvalues+", '%s'" % getsqlresult
		sqlfields = sqlfields+", branch"
		sqlvalues = sqlvalues+", '%s'" % branch
		numinit=numinit+1
		sqlcmd ="insert into packages (%s) values (%s)" % ( sqlfields, sqlvalues)
		print "%s: new package inserted: %s" %(arch, package)
	#print sqlcmd
	csr.execute(sqlcmd)
	#out=sqlcmd+";\n"
	#outf.write(out)
	f.close
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	#db.commit()
	return


def readRFC822Sources(filename, branch, mode):
	global csr, db, numupd, numinit
	f = filename
	#f = open(filename, 'r+')
	m=rfc822.Message(f)
	keys=m.keys()
	komma=""
	sqladd=""
	sqlfields=""
	sqlvalues=""
	package=m['package']
	#print package
	#if mode=="update":
	sqlcmd = "select files from sources where package='%s'" % package
	csr.execute(sqlcmd)
	try:
		sqlresult = csr.fetchone()[0]
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

sqlcmd = "begin work"
csr.execute(sqlcmd)


if mode=="sources":
	branch = split(filename, "_")[0]
	#print
	print "Source stats:"
	#sqlcmd = "begin work"
	#csr.execute(sqlcmd)
	#for branch in branches:
	scanSources(branch)
	print "  "+branch+" sources updated  \t:", numupd
	print "  "+branch+" sources inserted \t:", numinit
	tsu=tsu+numupd
	tsi=tsi+numinit
	numupd=0
	numinit=0
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	db.commit()
elif mode=="packages":
	arch, branch, foo = split(filename, "_")
	print arch, branch, foo
	print "Package stats:"
	#for arch in archs: 
	#sqlcmd = "start transaction isolation level serializable"
	#sqlcmd = "begin work"
	#csr.execute(sqlcmd)
	#for branch in branches:
	print branch, arch
	scanPackages(branch, arch)
	print "  "+branch+" packages updated \t:", numupd
	print "  "+branch+" packages inserted\t:", numinit
	tpu=tpu+numupd
	tpi=tpi+numinit
	numupd=0
	numinit=0
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)
	db.commit()

sqlcmd = "commit"
csr.execute(sqlcmd)

#print "=====================================\nTotals:"
#print "Sources updated  :", tsu
#print "Sources inserted :", tsi
#print "Packages updated :", tpu
#print "Packages inserted:", tpi
print "=====================================\nOverall:"
print "Updated          :", tsu+tpu
print "Inserted         :", tsi+tpi
print

sqlcmd = "vacuum analyze %s" % mode
csr.execute(sqlcmd)
db.commit()
db.close()
#outf.close()

