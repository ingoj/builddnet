#!/bin/sh
#
# look up a package's status in the m68k-all.txt file

HOME="/home/builddnet"
source $HOME/conf.d/database.conf

#all="alpha arm hppa i386 ia64 m68k mips mipsel powerpc s390 sparc"
#arch=$(echo $QUERY_STRING |cut -f1 -d"_")
#PKG=$(echo $QUERY_STRING |sed -e 's/.*pkg=\([^&]*\).*/\1/')
#PKG=${PKG%%_*}

# apache doesn't like this: (where's header; where's blank line?)

cat << .
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>Needs-Build ETA</title>
</head>
<body bgcolor="#ffffff" text="#000000">
<font size=+3>ETA times for needs-build queue for unstable:</font><br>
<pre>
<table border=0>
.
for arch in `cat /home/builddnet/bin/archs_unstable`; do
	ETA=`cat /home/builddnet/unstable/listdir/${arch}_nbq_ETA.txt`
	echo "<tr><td>$arch</td><td>:</td><td> $ETA</td></tr>"
done
echo '</table></pre></body>'

exit 0

