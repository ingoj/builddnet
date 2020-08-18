#!/usr/bin/python

import psycopg
from os import linesep, environ
from string import *
from time import *
import cgi, sys
import popen2

homedir=environ['HOME']
f = open(homedir+"/conf.d/database.conf")
while 1:
	line = f.readline()
	if len(line)==0: break
	if line.count("host"):
		host = split(line,"=")[1]
	elif line.count("port"):
		port = split(line,"=")[1]
	elif line.count("username"):
		username = split(line,"=")[1]
	elif line.count("password"):
		password = split(line,"=")[1]
	elif line.count("database"):
		database = split(line,"=")[1]


dsn = "dbname=%s host=%s user=%s password=%s" % ( database, host, username, password )
db = psycopg.connect(dsn)
csr = db.cursor()

#print sys.argv

try:
	mode = sys.argv[1]
except:
	mode = ""
try:
	flavour = sys.argv[2]
except:
	flavour = "unstable"
try:
	arch = sys.argv[3]
except:
	arch = ""
	
	
fpath = "/home/builddnet/%s/listdir/" % flavour

def init():
	global flavour
	sqlcmd = "truncate graphhistory"
	#"CREATE TABLE graphhistory (id serial NOT NULL, arch character varying(24) NOT NULL, uxtime timestamp without time zone NOT NULL, installed integer DEFAULT 0 NOT NULL, needsbuild integer NOT NULL, building integer NOT NULL, uploaded integer NOT NULL, failed integer NOT NULL, depwait integer NOT NULL, reuploadwait integer NOT NULL, installwait integer NOT NULL, failedremoved integer NOT NULL, depwaitremoved integer NOT NULL, notforus integer NOT NULL, total integer NOT NULL)"
	csr.execute(sqlcmd)
	db.commit()
	return
	
def addfullhist(arch):
	global flavour
	f = open(fpath+arch+"_stats-full-history",'r')
	#print f
	while 1:
		line = f.readline()
		if not len(line):
			break
		line.replace("\r\n", "")
		#print line
		uxtime2, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total = line.split(" ")
		itotal=int(total)
		uxtime=asctime(localtime(float(uxtime2)))
		#print itotal
		sqlcmd = "insert into graphhistory (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total, flavour) values ('%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, itotal, flavour)
		#print sqlcmd
		csr.execute(sqlcmd)
	db.commit()
	f.close()

def addentry(arch):
	global flavour
	uxtime   		= asctime(localtime(float(sys.argv[4])))
	installed	 	= sys.argv[5]
	needsbuild		= sys.argv[6]
	building		= sys.argv[7]
	uploaded		= sys.argv[8]
	failed			= sys.argv[9]
	depwait 		= sys.argv[10]
	reuploadwait	= sys.argv[11]
	installwait 	= sys.argv[12]
	failedremoved	= sys.argv[13]
	depwaitremoved	= sys.argv[14]
	notforus		= sys.argv[15]
	total			= int(sys.argv[16])
	
	#try:
		
	sqlcmd = "insert into graphhistory (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total, flavour) values ('%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total, flavour)
	#print sqlcmd
	csr.execute(sqlcmd)
	db.commit()

def printhelp():
	print "builddgraph.py - (c) 2004 by Ingo Juergensmann <ij@buildd.net>"
	print ""
	print "usage: builddgraph.py <mode> <arch> [<stats>]"
	print ""
	print "       mode can be either init, addfull or add. "
	print "           * init: initializes the db"
	print "           * addfull: adds full history file to the db"
	print "           * add: adds a single line of stats given as argument (<stats>)"
	print ""
	sys.exit(1)


if mode=="init":
	init()
elif (mode=="addfull" and arch<>""):
	addfullhist(arch)
elif (mode=="add" and arch<>""):
	addentry(arch)
else:
	printhelp()
	
db.close()

sys.exit(0)





