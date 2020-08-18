#!/bin/bash


HOME="/home/builddnet"
source $HOME/conf.d/database.conf

flavour=$(echo "$QUERY_STRING" |cut -f1 -d"_")
buildd=$(echo $QUERY_STRING | sed -e 's/.*searchtype=\([^&]*\).*/\1/')
arch=$(echo $QUERY_STRING |sed -e 's/.*arch=\([^&]*\).*/\1/'|sed -e 's/%2B/+/g')
#arch=${PKG%%_*}
#PKG=$(echo $QUERY_STRING |sed -e 's/.*pkg=\([^&]*\).*/\1/'|sed -e 's/%2B/+/g')
#PKG=${PKG%%_*}
#all=`cat /home/builddnet/$flavour/bin/archs`
KERNEL="n/a"

TMPFILE=`mktemp` || exit 1
trap "rm $TMPFILE" EXIT

if [ $flavour = "unspecified" ]; then
	flavour="unstable"
fi

# apache doesn't like this: (where's header; where's blank line?)
cat << .
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>buildd.net build times for $buildd</title>
</head>
<body bgcolor="#ffffff" text="#000000">
<table border="0" width="100%">
<tr><td align="left" width="15%">[<a href="http://$flavour.buildd.net/index-$arch.html">back</a>]</td><td align="center" width="70%">
.

buildds=`psql -U ${username} -h ${host} ${database} -c "select distinct name from status,ptracker where status.name=ptracker.buildd and status.arch='${arch}' and ${flavour}='t' order by name" | tail +3 | grep ^[\ *]`
#echo $buildds
echo "<center>"
for box in $buildds; do 
	box=`echo $box | tr -d [:space:]`
	echo -n "<font size=+0>[<a href=\"http://buildd.net/cgi/hostpackages.cgi?${flavour}_arch=${arch}&searchtype=${box}\">${box}</a>]</font> "
done
echo '</center></td><td align="right" width="15%">&nbsp;</td></tr></table>'

cat << .
<table bgcolor="#f0f0f0" width=100%>
<th>
<font size=+3>
${buildd}:<br>
</font>
</th>
</table>
.

allstats=`psql -t -U ${username} -h ${host} ${database} -c "select uptime, users, lavg, memtotal, memfree, swaptotal, swapfree, kernel from status where name='${buildd}'"`
UPTIME=`echo $allstats | cut -f1 -d"|"`
USERS=`echo $allstats | cut -f2 -d"|"`
LAVG=`echo $allstats | cut -f3 -d"|"`
MEMTOTAL=`echo $allstats | cut -f4 -d"|" | sed 's/ //g'`
MEMFREE=`echo $allstats | cut -f5 -d"|" | sed 's/ //g'`
SWAPTOTAL=`echo $allstats | cut -f6 -d"|" | sed 's/ //g'`
SWAPFREE=`echo $allstats | cut -f7 -d"|" | sed 's/ //g'`
KERNEL=`echo $allstats | cut -f8 -d"|" | sed 's/ //g'`

if [ -n "$UPTIME" ]; then
	if [ -z "${KERNEL}" ]; then 
		KERNEL="n/a"
	fi
	/home/builddnet/bin/hoststats-graph.sh $flavour $buildd
	(( MEMUSED=${MEMTOTAL}-${MEMFREE} ))
	(( SWAPUSED=${SWAPTOTAL}-${SWAPFREE} ))
	echo "<p><center><table><tr><td>"
	echo "<table><tr><td align=left colspan=4>Kernel version:</td><td align=right colspan=2>${KERNEL}</td></tr>"
	echo "<tr><td colspan=2>up: ${UPTIME}</td><td colspan=2 align=center>${USERS} users</td><td colspan=2>load avg: ${LAVG}</td></tr>
	<tr><td>Mem: </td><td align=right>${MEMTOTAL}k</td><td align=right>used: </td><td align=right>${MEMUSED}k</td><td align=right>free: </td><td align=right>${MEMFREE}k</td></tr>
	<tr><td>Swap: </td><td align=right>${SWAPTOTAL}k</td><td align=right>used: </td><td align=right>${SWAPUSED}k</td><td align=right>free: </td><td align=right>${SWAPFREE}k</td></tr></table>"
	echo "</td><td><img src=\"http://www.buildd.net/hoststats/${buildd}_hoststats_mem.png\" alt=\"memory\"></td><td valign=center><font size=-2 color=red>used</font><br><font size=-2 color=green>free</font></td><td><img src=\"http://www.buildd.net/hoststats/${buildd}_hoststats_swap.png\" alt=\"swap\"></td></tr></table></center></p>"	
fi
echo "<table>"
echo "<tr><td valign=\"top\">"
echo "<b>Last 75 packages by $buildd:</b><br>"
echo "<pre>"
#'<a href=\"http://www.buildd.net/cgi/package_status?unstable_pkg=' || packagename || '&searchtype=all&arch=m68k\">' || packagename || '</a>'
#psql -U ${username} -h ${host} ${database} -c "select '<a href=\"http://www.buildd.net/cgi/package_status?unstable_pkg=' || packagename || '&searchtype=all&arch=m68k\">' || packagename || '</a>' as \"package (latest first)\", version, date_trunc('second', begin) as date, date_trunc('second',endtime-begin) as buildtime, dist from ptracker where buildd='$buildd' and state<>'nowbuilding' and dist not like '%secur%' order by id desc limit 75" #| sed 's/\(^.[[:alpha:]]*\b\)/http\:\/\/www\.buildd\.net/cgi/package_status\?unstable_pkg=\1\&searchtype=m68k\&arch=m68k/g'
psql -U ${username} -h ${host} ${database} -c "select packagename as \"package (latest first)\", version, date_trunc('second', begin) as date, date_trunc('second',endtime-begin) as buildtime, dist from ptracker where buildd='$buildd' and state<>'nowbuilding' and dist not like '%secur%' order by id desc limit 75" #\
#| sed 's/\(^\ .[[:alnum:]\-\.]*\)/\<a href=\"http\:\/\/www\.buildd\.net\/cgi\/package_status\?unstable_pkg=\1\&searchtype=m68k\&arch=m68k\"\>\1\<\/a\>/g'
echo "</pre><br><p>"
echo "</td><td>&nbsp; &nbsp; &nbsp;</td><td valign=\"top\">"
echo "<b>Average build time of $buildd:</b><br>"
echo "<pre>"
psql -U ${username} -h ${host} ${database} -c "select dist, count(*) as packages, avg(endtime-begin) as buildtime from ptracker where buildd='$buildd' and dist not like '%secur%' group by dist" | cut -f1 -d"."
echo "</pre><br><p>"
echo "<b>Packages built per day (max. 60 days):</b><br>"
#days=`psql -U ${username} -h ${host} ${database} -t -c "select distinct date_trunc('day', endtime) as endtime from ptracker where buildd='$buildd' order by endtime desc limit 60" | awk '{ print $1}' | sort -r | xargs echo`
#i=0
#packages=0
#touch $TMPFILE
#for day in $days ; do 
#	((i=i+1))
#	packagesbuilt=`psql -U ${username} -h ${host} ${database} -c "select count(*), avg(endtime-begin) from ptracker where endtime between '$day 00:00:00' and '$day 23:59:59' and buildd='${buildd}'" | grep  [[:digit:]*] | cut -f1 -d"." | head -1`
#	echo "$day |    $packagesbuilt" >> $TMPFILE
#	packagesbuilt=`echo $packagesbuilt | awk '{print $1}'`
#	((packages=packages+packagesbuilt))
#done
#((avgpackages=packages/${i}.0))
#avgpackages=$(echo -e "scale=2\n$packages/$i\nquit" | bc)
avgpackages=`psql -t -U ${username} -h ${host} ${database} -c "select round(count(*)/60.00, 2) from ptracker where buildd='${buildd}' and endtime>(now()-interval '60 days')"`
#echo "i: ${i} num:${packages} avg:${avgpackages}"
echo "<b>$avgpackages packages/day</b><br>"
echo "<pre>"
echo "Date:       | Count | avg buildtime: "
echo "------------+-------+----------------"

psql -U ${username} -t -h ${host} ${database} -c "select distinct  date_trunc('day', endtime) as date,  count(*), avg(endtime-begin) from ptracker where buildd='${buildd}'  group by date order by date desc limit 60;" > $TMPFILE
cat $TMPFILE | sed -e "s/\ 00:00:00//g" | tail -n 60
echo "</pre>"
echo "</td></tr>"
echo "</table>"

echo '</body></html>'
