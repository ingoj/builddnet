#!/usr/bin/python2.3

import psycopg
from os import linesep
from string import *
from time import *
import cgi, sys
import popen2

dsn = "dbname=buildd"
db = psycopg.connect(dsn)
csr = db.cursor()

try:
	mode = sys.argv[1]
except:
	mode = ""
try:
	arch = sys.argv[2]
except:
	arch = ""
	
	
fpath = "/home/younie/listdir/"

def init():
	sqlcmd = "CREATE TABLE graphhistory (id serial NOT NULL, arch character varying(24) NOT NULL, uxtime timestamp without time zone NOT NULL, installed integer DEFAULT 0 NOT NULL, needsbuild integer NOT NULL, building integer NOT NULL, uploaded integer NOT NULL, failed integer NOT NULL, depwait integer NOT NULL, reuploadwait integer NOT NULL, installwait integer NOT NULL, failedremoved integer NOT NULL, depwaitremoved integer NOT NULL, notforus integer NOT NULL, total integer NOT NULL)"
	csr.execute(sqlcmd)
	db.commit()
	return
	
def addfullhist(arch):
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
		sqlcmd = "insert into graphhistory (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total) values ('%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, itotal)
		#print sqlcmd
		csr.execute(sqlcmd)
	db.commit()
	f.close()

def addentry(arch):
	uxtime   		= asctime(localtime(float(sys.argv[3])))
	installed	 	= sys.argv[4]
	needsbuild		= sys.argv[5]
	building		= sys.argv[6]
	uploaded		= sys.argv[7]
	failed			= sys.argv[8]
	depwait 		= sys.argv[9]
	reuploadwait	= sys.argv[10]
	installwait 	= sys.argv[11]
	failedremoved	= sys.argv[12]
	depwaitremoved	= sys.argv[13]
	notforus		= sys.argv[14]
	total			= int(sys.argv[15])
	
	try:
		
	sqlcmd = "insert into graphhistory (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total) values ('%s', '%s','%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (arch, uxtime, installed, needsbuild, building, uploaded, failed, depwait, reuploadwait, installwait, failedremoved, depwaitremoved, notforus, total)
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





