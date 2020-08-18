#!/usr/bin/python
# -*- coding: UTF-8 

import psycopg
from os import linesep, path
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
#dsn = "dbname=buildd"
db = psycopg.connect(dsn)
csr = db.cursor()

wdsn = "dbname=%s host=%s user=%s password=%s" % ( database, host, username, password )
#wdsn = "dbname=buildd"
wdb = psycopg.connect(wdsn)
wcsr = wdb.cursor()

flavour = sys.argv[1]
arch = sys.argv[2]

if flavour=="etch-bpo": flavour="etchbpo"
if flavour=="unstable-non-free": flavour="nonfree"
if flavour=="woody-volatile": flavour="woodyvolatile"
if flavour=="etch-volatile": flavour="etchvolatile"
if flavour=="etch-skolelinux": flavour="etchskolelinux"
if flavour=="etch-secure": flavour="etchsecure"

#sqlcmd = "start transaction isolation level serializable"
#csr.execute(sqlcmd)
sqlcmd = "select id, arch, name, host, model, cpu, ram, disk, admin, email, status, lastseen, interval, reason, building, buildingflavour, builddstatus, speed from status where arch='%s' and %s=true and status<'999999' order by cpu desc, ram desc, name" % (arch, flavour)
#  and (buildingflavour='%s' or buildingflavour is Null or buildingflavour='unspecified')
csr.execute(sqlcmd)
sqlresult = csr.fetchall()
#print sqlresult

buildd=[]
bgcolor="#c0c0c0"


def ptracker(name, package):
	"""reads out data from ptracker DB"""
	
	packagename, version = split(package, "_", 1)
	
	sqlcmd = "select now()-begin from ptracker where state='nowbuilding' and buildd='%s' and packagename='%s' and version='%s'" % (name, packagename, version)
	csr.execute(sqlcmd)
	#print sqlcmd
	try:
		#print "in try 0"
		sqlresult = csr.fetchone()
		#print sqlresult
		buildtime = split(str(sqlresult[0]), ".")[0]
		#print buildtime
		#print type(buildtime)
	except:
		#print "in except 0"
		buildtime = ""
	return buildtime

#print """
#The %s autobuilders:

def tableheader():
	print """<p><table border=0 cellspacing=2 cellpadding=2>""" # % arch
	print  """
	<tr bgcolor="%s">
		<td><b>H B</b></td>
		<td><b>Name:</b></td>
		<!--td><b>Host:</b></td-->
		<td><b>Model:</b></td>
		<td><b>CPU:</b></td>
		<td><b>RAM:</b></td>
		<td><b>Disk:</b></td>
		<td><b>p/d:</b></td>
		<td><b>Admin:</b></td>
		<td><b>Building | <font color="#FF0000">Reason:</font></b></td>
		<td><b>hh:mm:ss:</b></td>
	</tr>"""	% bgcolor

def table():
	j = 0
	k = 0
	for i in sqlresult:
		#print "i: ", i
		machine			= 	list(i)
		bid 			=	machine[0]
		arch			=	machine[1]
		name			=	machine[2]
		host			=	machine[3]
		model			=	machine[4]
		cpu 			= 	machine[5]
		ram 			=	machine[6]
		disk			=	machine[7]
		admin			=	machine[8]
		email			=	machine[9]
		status			=	machine[10]
		lastseen		=	machine[11]
		interval		=	machine[12]
		reason			=	machine[13]
		building		=	machine[14]
		buildingflavour =	machine[15]
		builddstatus 	=	machine[16]
		speed	 		=	machine[17]
		try:
			foo=len(building)
			building=replace(building, " ", "+")
			#print "in try, %s <br>" % name
		except:
			building="" 
		try:
			bar=int(builddstatus)
		except:
			builddstatus=0 
	
		if status<=99999:
			if status<30:
				#sqlcmd = "update status set reason='8 weeks w/o response' where (lastseen+interval'8 weeks')<now() and status<>'99999'"
				#wcsr.execute(sqlcmd)
				#sqlcmd = "update status set reason='delisted in 1 week' where (lastseen+interval'11 weeks')<now() and status<>'99999'"
				#wcsr.execute(sqlcmd)
				#sqlcmd = "update status set reason=Null, status='99999' where (lastseen+interval'12 weeks')<now()"
				#wcsr.execute(sqlcmd)

				sqlcmd = "select now(), lastseen + 1.25*(select interval from status where name='%s'), lastseen + 4*(select interval from status where name='%s') from status where name='%s'" % (name, name, name)
				csr.execute(sqlcmd)
				res = csr.fetchone()
				#print sqlcmd
				#print res
				now = res[0]
				warn = res[1]
				timeout = res[2]
				if (now>warn and now<timeout):
					status=1
					sqlcmd = "update status set status=1 where name='%s'" % name
					try: 
						wcsr.execute(sqlcmd)
					except:
						pass
				if (now>timeout and timeout<>''):
					status=0
					sqlcmd = "update status set status=0 where name='%s'" % name
					try:
						wcsr.execute(sqlcmd)
					except:
						print "Exception! %s", name
						pass
				if (now<timeout and now<warn):
					sqlcmd = "update status set status=2 where name='%s'" % name
					try:
						wcsr.execute(sqlcmd)
					except:
						pass
				#print "before wdb.commit()"
				wdb.commit()
				#print name,now, warn, timeout

			j = j +1
			k = j % 2 
			if k == 1:
				bgcolor="#f8f8ff"
			else:
				bgcolor="#e0e0f0"
			print '    <tr bgcolor=%s>' % bgcolor	
			print '       <td align="left">'
			#print "before LEDs: %s %s<br>" % (name, status)
		
			# host-centric LEDs:		
			if (status<=0 or status==10 or status==20):
				hstatus = "down"
				print '         <img src="http://www.buildd.net/pix/red.png" alt="down">'
			elif (status==1 or status==11 or status==21):
				hstatus = "noresp"
				print '         <img src="http://www.buildd.net/pix/yellow.png" alt="no response">'
			elif (status==2 or status==12 or status==22):
				hstatus = "up"
				print '         <img src="http://www.buildd.net/pix/green.png" alt="up">'
			elif status==99999:
				hstatus = "notpart"
				print '         <img src="http://www.buildd.net/pix/grey.png" alt="not participating">'
		
			# buildd-centric LEDs:
			if (hstatus == "up" or hstatus == "noresp"):
				if builddstatus==-1:
					print '         <img src="http://www.buildd.net/pix/red.png" alt="down">',
				elif (builddstatus==0 and len(building)==0):
					print '         <img src="http://www.buildd.net/pix/grey.png" alt="idle">',
				elif (builddstatus==0 and len(building)<>0):
					print '         <img src="http://www.buildd.net/pix/green.png" alt="building">',
				elif builddstatus==1:
					print '         <img src="http://www.buildd.net/pix/green.png" alt="building">',
				elif builddstatus==2:
					print '         <img src="http://www.buildd.net/pix/yellow.png" alt="NO-DAEMON-PLEASE">',
				elif (builddstatus>=10 and builddstatus<20):
					print '         <img src="http://www.buildd.net/pix/purple.png" alt="need key">',
				elif (builddstatus>=20 and builddstatus<99999):
					print '         <img src="http://www.buildd.net/pix/blue.png" alt="need setup">',
			else:
					print '         &nbsp;', #<img src="http://www.buildd.net/pix/blue.png" alt="need setup">',
			
		
			print '       </td>'
			if (hstatus=="notpart" or str(buildingflavour)=="None"):
				print '       <td>%s</td>' % ( name )
			else:
				print '       <td><a href="http://buildd.net/cgi/hostpackages.cgi?%s_arch=%s&searchtype=%s">%s</a></td>' % ( flavour, arch, name, name )
			#print '       <td>%s</td>' % host
			print '       <td>%s</td>' % model
			print '       <td>%s</td>' % cpu
			print '       <td align="right">%sM</td>' % ram
			print '       <td align="right">%sG</td>' % disk
			print '       <td align="right">%.2f</td>' % speed
			print '       <td><a href="mailto:%s">%s</a></td>' % (email, admin)
			print '       <td>'
			try:
				if len(building)<>0:
					if buildingflavour==flavour:
						print '      <a href="http://buildd.net/cgi/ptracker.cgi?%s_pkg=%s&searchtype=%s">%s</a>' % ( buildingflavour, building, arch, building )
						#print '       %s' % building
					elif (buildingflavour=="unspecified" or buildingflavour==''):
						print ''
					else:
						print '     <a href="http://%s.buildd.net/index-%s.html">%s</a>' % (buildingflavour, arch, buildingflavour)
			except:
				print ''
			try:
				if (len(reason) and len(building)):
					print "&nbsp;|&nbsp;"
				else:
					pass
			except:
				pass
			try:
				if len(reason)<>0:
					print '       <font color="#FF0000">%s</font>' % reason
			except:
				print ''
			print '       </td>'
			try:
				if (len(building)<>0 and buildingflavour==flavour):
					#print "in if"
					buildtime = str(ptracker(name, building))
					if count(buildtime, ":")==3:
						buildtime=replace(buildtime, ":", "d", 1)
					print '       <td>%s</td>' % buildtime 
					#print '       <td><a href="http://buildd.net/cgi/ptracker.cgi?%s_pkg=%s&searchtype=%s">%s</a></td>' % ( buildingflavour, building, arch, buildtime )
				else:
					#print "in else"
					buildtime=""
					print '       <td></td>' 
				print '    </tr>'	
			except:
				buildtime = ""
				print '       <td>%s</td>' % buildtime
				print '       <td></td>'
				print '    </tr>'
				                                                                        
	#print "end of for"
	return

def tablefooter():
	#db.commit()
	print '</table>'
	#print '<center><img src="pix/green.png"> up | <img src="pix/yellow.png"> no response | <img src="pix/red.png"> down | <img src="pix/purple.png"> wait for key | <img src="pix/blue.png"> need setup | <img src="pix/grey.png"> not participating | <a href="http://www.buildd.net/faq">FAQ</a></center>'
	print '<center>the colors of the LEDs are explained in the <a href="http://www.buildd.net/faq/">FAQ</a></center>'
	#sqlcmd = "commit"
	#csr.execute(sqlcmd)

tableheader()
try: 
	table()
except Exception, e:
	print "Exception caught: ", e
	pass
tablefooter()

wdb.commit()
wdb.close
db.close()
