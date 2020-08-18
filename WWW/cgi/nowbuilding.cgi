#!/bin/bash

# apache doesn't like this: (where's header; where's blank line?)

HOME="/home/builddnet"
source $HOME/conf.d/database.conf

cat << .
Content-type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2//EN">
<html>
<head>
<title>buildd.net - now building</title>
</head>
<body bgcolor="#ffffff" text="#000000">
<table bgcolor="#f0f0f0" width=100%>
<th>
<h1>
now building:<br>
</h1>
</th>
</table>

<p>
.

echo "<pre>"
psql -U ${username} -h ${host} ${database} -c "select packagename, version, dist, arch, buildd, now()-begin as buildtime from ptracker where dist not like '%secur%' and state='nowbuilding' order by arch, buildd, packagename, version"
echo "</pre><p><br>"
echo '</body></html>'
