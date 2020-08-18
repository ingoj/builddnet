#!/usr/bin/python

import psycopg
from os import linesep
from string import *
from time import *
import cgi, sys, os
import popen2

homedir=os.environ['HOME']
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

mode = sys.argv[1]
#arch = sys.argv[2]

#if flavour=="woody-backports.org": flavour="woodybackports"
#if flavour=="unstable-non-free": flavour="nonfree"
#if flavour=="woody-volatile": flavour="woodyvolatile"
#if flavour=="sarge-volatile": flavour="sargevolatile"
#if flavour=="etch-secure": flavour="etchsecure"

buildd="aahz"
#totalcount=0
errorcount=0

def main(mode):
	sqlcmd = "select distinct status.id as id, ptracker.buildd as buildd from status, ptracker where ptracker.buildd=status.name and state<>'nowbuilding' order by buildd"
	csr.execute(sqlcmd)
	sqlresult = csr.fetchall()
	#print sqlresult 
	for i in range(0, len(sqlresult)):
		oid = sqlresult[i][0]
		buildd = sqlresult[i][1]
		print "!!! ", buildd
		if (mode=="daily" or mode=="init"):
			getstats(oid, buildd, mode)
		else:
			print "no argument given. exiting."
			sys.exit(1)
		db.commit()

def getstats(oid, buildd, mode):
	""" foo """
	global errorcount
	totalcount=0
	sqlcmd = "select distinct date_trunc('day', endtime) from ptracker where buildd='%s' and endtime is not null" % buildd
	csr.execute(sqlcmd)
	dates = csr.fetchall()
	#print dates
	dates.sort()
	firstdate=dates[0][0]
	#print firstdate
	#sys.exit(0)
	for i in range(0, len(dates)):
		day = split(str(dates[i][0]), " ")[0]
		#print day
		sqlcmd = "select count(*), avg(endtime-begin) from ptracker where endtime between '%s' and '%s 23:59:59' and buildd='%s'" % ( firstdate, day, buildd )
		csr.execute(sqlcmd)
		sqlresult = csr.fetchall()
		#print sqlresult
		avgcount = int(sqlresult[0][0])
		avgtime  = str(sqlresult[0][1])
		if avgtime.count(":")==3:
			avgtime=replace(avgtime, ":", " ", 1)
		ii=i+1
		if avgtime<>"None":
			print " =>", avgcount, avgtime
			speed = avgcount/float(ii)
			if mode=="init":
				sqlcmd = "insert into builddspeed (buildd, datum, speed, avgtime) values ('%s', '%s', '%s', '%s')" % ( oid, day, speed, avgtime)
				csr.execute(sqlcmd)
		totalcount = totalcount + avgcount
	if mode=="daily":
		while 1:
			try:
				sqlcmd = "insert into builddspeed (buildd, datum, speed, avgtime) values ('%s', '%s', '%s', '%s')" % ( oid, day, speed, avgtime )
				csr.execute(sqlcmd)
				sqlcmd = "update status set speed='%s' where id='%s'" % ( speed, oid )
				csr.execute(sqlcmd)
				break
			except Exception, e:
				print "!!! Exception: ", e
				errorcount=errorcount+1
				if errorcount >= 10: sys.exit()
				sleep(5)
				
	#print sqlcmd
	i=i+1
	#print totalcount, i
	#print "Total: %0.3f" %( int(totalcount)/float(i) )



main(mode)
db.commit()
db.close()

