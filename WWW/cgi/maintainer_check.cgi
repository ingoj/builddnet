#!/bin/sh
#
# look up a package's status in the m68k-all.txt file

HOME="/home/builddnet"
source $HOME/conf.d/database.conf

#all="alpha arm hppa i386 ia64 m68k mips mipsel powerpc s390 sparc"
#all="hppa ia64 m68k"

#flavour=$(echo "$QUERY_STRING" |cut -f1 -d"_")
#arch=$(echo $QUERY_STRING |cut -f2 -d"_")
flavour=$(echo "$QUERY_STRING" |cut -f1 -d"_")
arch=$(echo $QUERY_STRING | sed -e 's/.*searchtype=\([^&]*\).*/\1/')
PKG=$(echo $QUERY_STRING |sed -e 's/.*pkg=\([^&]*\).*/\1/'|sed -e 's/%2B/+/g')
PKG=${PKG%%_*}
refererarch=$(echo $QUERY_STRING |sed -e 's/.*arch=\([^&]*\).*/\1/')
firstletter=`echo $PKG | cut -f1 -d"." | perl -ne 'foreach $m (m/\b(\w)/g) { print "$m\n"; }'`
all=`cat /home/builddnet/bin/archs_${flavour}`

if [ $arch = "all" ]; then 
	linkarch=""
else
	linkarch=$arch
fi


# apache doesn't like this: (where's header; where's blank line?)

cat << .
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<link rel="stylesheet" href="http://buildd.net/builddnet.css" type="text/css" />
<title>buildd.net search for $PKG</title>
</head>
<body bgcolor="#ffffff" text="#000000">
[<a href="http://${flavour}.buildd.net/index-${refererarch}.html">back</a>]<br>
<table bgcolor="#f0f0f0" width=100%>
<th>
<h1>
$flavour:<br>
</h1>
</th>
</table>
<p>
<center>
<form action="http://www.buildd.net/cgi/package_status" method=get>
  Package status
  <input type="text" name="unstable_pkg" size=30>
  <input type="submit" name="searchtype" value="${refererarch}">
  <input type="submit" name="searchtype" value="all">
  <input type="hidden" name="arch" value="$refererarch">
</form>
<p>
<table>
	<th bgcolor="#c0c0c0" colspan="6">$PKG</th>
	<tr>
		<td><a href="http://buildd.net/cgi/ptracker.cgi?${flavour}_pkg=${PKG}&searchtype=$arch">Package statistics</a></td>
		<td><a href="http://bugs.debian.org/${PKG}">Debian BTS</a></td>
		<td><a href="http://packages.qa.debian.org/${firstletter}/${PKG}.html">Debian PTS</a></td>
		<td><a href="http://buildd.debian.org/build.php?arch=${linkarch}&pkg=${PKG}&ver=">build logs (b.d.o)</a></td>
		<td><a href="http://experimental.ftbfs.de/build.php?arch=${linkarch}&pkg=${PKG}&ver=">build logs (e.f.d)</a></td>
		<td><a href="http://amd64.ftbfs.de/build.php?arch=${linkarch}&pkg=${PKG}&ver=">build logs (amd64)</a></td>
	</tr>
</table>
</center>
<p><hr>
.

packages=`grep-dctrl -r -F Maintainer '<aba@debian.org' -n -s Package /home/builddnet/unstable/packages/*_Sources` # | awk '{print $2}'`
echo "<table border=0 width="100%" cellspacing=2><tr bgcolor=\"#c0c0c0\"><th><font size=-2>Package</font></th>"

for i in $all; do
    echo "<th><font size=-2>${i}</font></th>"
done
echo "</tr><tr>"
for PKG in ${packages}; do
	echo "<td><font size=-1>${PKG}</font></td>"
	for i in $all; do
		HIT=$(sed -n "/\/${PKG}_/,/^[/a-z0-9A-Z]/p" /home/builddnet/$flavour/listdir/${i}-all.txt | head -1 | awk '{ print $2 }' | tr [:upper:] [:lower:])
   		if [ -z "$HIT" ]; then
   		    echo "<td></td>"
        else
   			case "$HIT" in 	
						"needs-build")
							qnum=`grep -i ^[a-z] /home/builddnet/${flavour}/listdir/${i}-all.txt | grep -i needs-build | cat -b | grep ${PKG} | awk '{print $1}'`
							echo "<td align=\"center\" bgcolor=\"#fffbce\"><font size=-2>needs-build<br>#${qnum}</font></td>"
							;;
						"installed")
							echo "<td align=\"center\" bgcolor=\"lightgreen\"><font size=-2>inst.</font></td>"
							;;
						"failed")
							echo "<td align=\"center\" bgcolor=\"red\"><font size=-2>failed</font></td>"
							;;
						"dep-wait")
							echo "<td align=\"center\" bgcolor=\"lightblue\"><font size=-2>dep-wait</font></td>"
							;;
						"uploaded")
							echo "<td align=\"center\" bgcolor=\"#be8e8e\"><font size=-2>uploaded</font></td>"
							;;
						"building")
							echo "<td align=\"center\" bgcolor=\"yellow\"><font size=-2>building</font></td>"
							;;
						*)
							echo "<td></td>"
							;;
					esac
							
		fi
	done
	echo "</tr>"
done
echo "</table><br><p>"
echo '<hr><p>
<center>
<form action="http://www.buildd.net/cgi/package_status" method=get>
  Package status
  <input type="text" name="unstable_pkg" size=30>'
echo "  <input type=\"submit\" name=\"searchtype\" value=\"${arch}\">"
echo '  <input type="submit" name="searchtype" value="all">
</form>
</center>'
echo "[<a href=\"http://${flavour}.buildd.net/index-${refererarch}.html\">back</a>]<br><p>"


echo '</body></html>'

exit 0

