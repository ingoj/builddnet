#!/bin/bash

HOME="/home/builddnet"
source $HOME/conf.d/database.conf

flavour=$(echo "$QUERY_STRING" |cut -f1 -d"_")
arch=$(echo $QUERY_STRING | sed -e 's/.*searchtype=\([^&]*\).*/\1/')
PKG=$(echo $QUERY_STRING |sed -e 's/.*pkg=\([^&]*\).*/\1/'|sed -e 's/%2B/+/g')
PKGVERSION=`echo $PKG | cut -f2 -d"_"`
PKG=${PKG%%_*}
all=`cat /home/builddnet/bin/archs_${flavour}`
refererarch=$(echo $QUERY_STRING |sed -e 's/.*arch=\([^&]*\).*/\1/')

TMPFILE=`mktemp` || exit 1
trap "rm $TMPFILE" EXIT


#if [ "$flavour"="unspecified" ]; then
#	flavour="unstable"
#fi

# apache doesn't like this: (where's header; where's blank line?)

cat << .
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>buildd.net build times for $PKG</title>
</head>
<body bgcolor="#ffffff" text="#000000">
[<a href="http://$flavour.buildd.net/index-$arch.html">arch page</a>]
<table bgcolor="#f0f0f0" width=100%>
<th>
<font size=+3>
$PKG/$flavour:<br>
</font>
</th>
</table>
<p>
<center>
<form action="http://www.buildd.net/cgi/ptracker.cgi" method=get>
  Package_version:
  <input type="text" name="${flavour}_pkg" size=30>
  <!--input type="submit" name="searchtype" value="${refererarch}"-->
  <input type="submit" name="searchtype" value="OK">
  <input type="hidden" name="arch" value="$refererarch">
</form>
</center>
.
#http://buildd.net/cgi/ptracker.cgi?${flavour}_pkg=${PKG}&searchtype=$arch
psql -U ${username} -h ${host} ${database} -o $TMPFILE --no-align -c "select distinct s.architecture, s.buildconflicts, s.builddepends, s.binaries, s.maintainer, s.priority, s.section, s.branch, s.version, p.description from sources s, packages p where s.package='${PKG}' and s.id=p.source and s.flavour=p.flavour and p.flavour='${flavour}' limit 1"
#echo "select distinct s.architecture, s.buildconflicts, s.builddepends, s.binaries, s.maintainer, s.priority, s.section, s.branch, s.version, p.description from sources s, packages p where s.package='${PKG}' and s.id=p.source<br>"
#head -n 1 $TMPFILE ; echo "<br>"
#echo "<pre>" ; cat $TMPFILE ; echo "</pre>"
result=`tail -n 2 $TMPFILE | head -n 1`
#echo $result, "<br>"
architecture=`echo $result | awk -F"|" '{ print $1 }'`
buildconflicts=`echo $result | awk -F"|" '{ print $2 }'`
builddepends=`echo $result | awk -F"|" '{ print $3 }' | sed 's/\ /__/g' | sed -e 's/,/\ /g' `
binary=`echo $result | awk -F"|" '{ print $4 }' | sed -e 's/Files://g'`
maintainer=`echo $result | awk -F"|" '{ print $5 }' | sed -e 's/</\&lt;/g' -e 's/>/\&gt;/g'`
priority=`echo $result | awk -F"|" '{ print $6 }'`
section=`echo $result | awk -F"|" '{ print $7 }'`
branch=`echo $result | awk -F"|" '{ print $8 }'`
version=`echo $result | awk -F"|" '{ print $9 }'`
description=`echo $result | awk -F"|" '{ print $10 }'`

echo "<table>"
echo "  <tr><td><b>Package</b></td><td>&nbsp;:&nbsp;</td><td><a href=\"http://people.debian.org/~igloo/status.php?packages=${PKG}\">$PKG</a> $version (building: ${PKGVERSION})&nbsp; - &nbsp;$description</td></tr>"
#echo "  <tr><td><b>Description</b></td><td>&nbsp;:&nbsp;</td><td>$description</td></tr>"
echo "  <tr><td><b>Architecture</b></td><td>&nbsp;:&nbsp;</td><td>$architecture</td></tr>"
echo "  <tr><td><b>Maintainer</b></td><td>&nbsp;:&nbsp;</td><td><a href=\"http://qa.debian.org/developer.php?package=${PKG}\">$maintainer</a></td></tr>"
echo "  <tr><td><b>Section</b></td><td>&nbsp;:&nbsp;</td><td>$section</td></tr>"
echo "  <tr><td><b>Priority</b></td><td>&nbsp;:&nbsp;</td><td>$priority</td></tr>"
echo "  <tr><td valign=\"top\"><b>Binary</b></td><td valign=\"top\">&nbsp;:&nbsp;</td><td>$binary</td></tr>"
echo "  <tr><td valign=\"top\"><b>Build-Depends</b></td><td valign=\"top\">&nbsp;:&nbsp;</td><td>"

for bd in `echo $builddepends | sed -e 's/(>=,//g' -e 's/!/|/g'`; do 
	bdpackage=`echo $bd | sed -e 's/__/\ /g' | awk '{ print $1 }'`
	echo "<a href=\"http://packages.debian.org/${bdpackage}\">"
	echo "`echo ${bd}|sed -e 's/__/\ /g'`</a>&nbsp;" | sed -e 's/.[__]//'
done 
echo "</td></tr>"
echo "</table>"

dball=`echo $all | sed -e 's/\ /,\ /g' -e 's/-//g'`
#echo `psql -U builddnet buildd -c "select ${dball} from packages where package='${PKG}'"`
binpackage=`psql -t -U ${username} -h ${host} ${database} -c "select binaries from sources where package='$PKG'" |  sed -e 's/,/\n/g' | sort -u | head -n2 | tail -n 1 | tr -d "[:blank:] "`
archvers=`psql -U ${username} -h ${host} ${database} -c "select ${dball} from packageversion as p, sources as s where p.package='${binpackage}' limit 1" | head -3 | tail -n 1`
#echo "select ${dball} from packageversion as p, sources as s where p.package='$binpackage'"
#archvers=`psql -U builddnet buildd -c "select ${dball} from packageversion as p, sources as s where p.package=(select distinct p.package from packages as p, sources as s where s.package='${PKG}' limit 1) limit 1" | head -3 | tail -n 1`
#echo "select ${dball} from packageversion as p, sources as s where p.package=(select distinct p.package from packages as p, sources as s where s.id=p.source and s.package='${PKG}' limit 1)"
echo "<center><font size=-2><b>installed version check for ${flavour}:</b><table border=0 width=\"100%\" cellspacing=2><tr bgcolor=\"#c0c0c0\">"
for dbarch in $dball; do
	echo -n "<td><font size=-2>"; echo -n ${dbarch} | tr -d "[:blank:]" | sed -e 's/,//g' ; echo "</font></td>"
done
echo "</tr><tr bgcolor=\"#f8f8ff\">"
i=0
#verslist=`echo $archvers |  sed -e 's/|/\n/g' | grep [[:alnum:]] | tr -d "[:blank:]" | sort -r -u`
#first=`echo $verslist | head -1 | tr -d [:blank:]`
#second=`echo $verslist | head -2 | tail -n 1 | tr -d [:blank:]`
first=`echo $archvers |  sed -e 's/|/\n/g' | grep [[:alnum:]] | sort -r -u | head -1 | tr -d [:blank:]`
second=`echo $archvers |  sed -e 's/|/\n/g' | grep [[:alnum:]] | sort -r -u | head -2 | tail -n 1 | tr -d [:blank:]`
if `dpkg --compare-versions $first gt $second`  ; then
	newest=$first
else
	newest=$second
fi 
# enable the next if statement to compare against the building version as well
#if  `dpkg --compare-versions $PKGVERSION gt $newest` ; then
#	newest=$PKGVERSION
#fi
#echo "&gt;$newest:$first:$second&lt;"
for dbarch in $dball; do
	((i=i+1))
	dbvers=`echo $archvers | cut -d"|" -f${i}`
	#echo $dbvers
	if [ -z $dbvers ] ; then 
		echo "<td width="6.25%"><font size=-2>n/a</font></td>"
	elif [ "$dbvers" = "(0 rows)" ] ; then 
		echo "<td><font size=-2>n/a</font></td>"
	else
		tver=`dpkg --compare-versions "${dbvers}" eq "${newest}" ; echo $?`
		#echo $tver
		dbvers=`echo $dbvers | sed -e 's/+cvs/+cvs\n/g'`
		if [ "$tver" = "0" ] ; then 
			echo "<td width="6.25%"><font size=-2 color=\"green\">${dbvers}</font></td>"
			#echo "<td><img src=\"http://buildd.net/pix/green.png\"></td>"
		else
			echo "<td><font size=-2 color=\"red\">${dbvers}</font></td>"
		fi
	fi
done
echo "</tr></table></font></center>"
echo "<br><p>"

echo "<table>"
echo "<tr><td valign=\"top\">"
echo "<b>avgtime for archs:</b>"
echo "<pre>"
psql -U ${username} -h ${host} ${database} -c "select * from v_avgtimeperarch"
echo "</pre>"
#echo "</td><td>&nbsp; &nbsp; &nbsp;</td><td valign=\"top\">"
#echo "<b>database count:</b><br>"
#echo "<pre>"
#psql -U builddnet buildd  -c "select arch, count(*) as \"Packages per arch\" from ptracker group by arch order by arch"
#echo "</pre><p><br>"
#echo "</td><td>&nbsp; &nbsp; &nbsp;</td><td valign=\"top\">"
echo "<b>Totals:</b>"
echo "<pre>"
psql -U ${username} -h ${host} ${database} -c "select dist, count(*) as \"Packages\" from ptracker where dist not like '%secur%' group by dist order by dist"
echo "</pre><p><br>"
echo "</td><td>&nbsp; &nbsp; &nbsp;</td><td valign=\"top\">"
echo "<b>avgtime for package $PKG:</b>"
echo "<pre>"
psql -U ${username} -h ${host} ${database} -c "select version, arch, dist, date_trunc('second', begin) as begin, buildd, date_trunc('second', endtime-begin) as buildtime from ptracker where packagename='$PKG' and dist not like '%secur%' order by version desc, begin desc, dist, arch limit 25" 
echo "</pre><br><p>"
echo "</td></tr>"
echo "</table>"
echo '</body></html>'
