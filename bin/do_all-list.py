#!/usr/bin/python

from string import *
import sys
import os

args=sys.argv
global flavour
path 			= os.path.dirname(args[0])
flavour 		= args[1]
arch 			= args[2]
urlbuildlogs	= args[3]

print path, flavour, arch, urlbuildlogs


#sys.exit()

f = open('listdir/m68k-all.txt', 'r+')

def main():
	global flavour
	i = 0
	while 1:
		line = replace(f.readline(), '\r\n', '')
		if not line: 
			break
		#print line
		i=i+1
		if line.count("wanna-build"): line= " "
		first = list(line)[0]
		#print first, 
		if first == " ":
			pass
			#print "nothing new..."
		elif first == "T":
			pass
		else: 
			sectionpackage, rest = split(line, ":", 1)
			#print sectionpackage, rest
			section, packageversion = rsplit(str(sectionpackage), "/", 1)
			print "Section: ", section, 
			packagename, packageversion = split(lstrip(packageversion), "_")
			print "Package: ", packagename, 
			print "Version: ", packageversion
			

main()
 