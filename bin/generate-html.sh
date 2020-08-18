#!/bin/bash

CHECKFILE=/home/builddnet/bin/.checkfile

if [ -e $CHECKFILE ]; then
	exit 0
fi

trap "rm $CHECKFILE" EXIT
touch $CHECKFILE

all_flav="etch-bpo etch-secure experimental unstable-non-free etch-volatile etch-skolelinux unstable"
notall_flav="etch-bpo etch-secure experimental unstable-non-free etch-volatile etch-skolelinux"

if [ -z "$1" ]; then 
	echo ""
	echo "*** No flavour specified (woody-backports.org, experimental, non-free)."
	echo ""
	exit 1
else
	if [ $1 == "all" ]; then
		for i in $all_flav; do
			echo "*** Generating HTML pages for $i:"
			/home/builddnet/bin/generate-html.sh $i
		done
		exit 0
	elif [ $1 == "notall" ]; then
		for i in $notall_flav; do
			echo "*** Generating HTML pages for $i:"
			/home/builddnet/bin/generate-html.sh $i
		done
		exit 0
	else
		flavour=$1
		pfad=/home/builddnet/$flavour
	fi
fi

#ALL="alpha arm hppa i386 ia64 m68k mips mipsel powerpc s390 sparc"
#ALL="alpha hppa mips sparc"
ALL=`cat /home/builddnet/bin/archs_${flavour}`
echo $ALL

if [ -e /home/builddnet/bin/.maintenance ] ; then
	#MAINTENANCE="<font color=\"#ff0000\">Maintenance!</font>"
	MAINTENANCE="DB-maintenance!"
	echo "maintenance mode"
else
	MAINTENANCE=""
fi
echo "maintenance: $MAINTENANCE"
for arch in $ALL; do
	echo "Processing $arch"
	fmtime=`ls --full-time $pfad/listdir/${arch}-all.txt  | awk '{ print $6,$7 $8}' | cut -f1 -d"." | awk '{ print $2,$3,$1}'`
	mtime=`date -u -d"$fmtime"` 
	#ETA=`~/bin/nb-queue-eta.sh $flavour $arch`
	ETA=`cat $pfad/listdir/${arch}_eta`
	#echo $mtime
	cat /home/builddnet/template/top1.html | sed -e s/%FLAVOUR%/$flavour/g -e s/%ARCH%/$arch/g -e s/%MAINTENANCE%/$MAINTENANCE/g > $pfad/template/index-${arch}.html 

	for flav in $all_flav; do
		if [ -e /home/builddnet/$flav/WWW/index-${arch}.html ]; then
			case "$flav" in
				etch-bpo)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://backports.buildd.net/index-${arch}.html\">backports</a>]"
					;;
				etch-secure)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://etch-secure.buildd.net/index-${arch}.html\">etch-secure</a>]"
					;;
				etch-skolelinux)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://skolelinux.buildd.net/index-${arch}.html\">skolelinux</a>]"
					;;
				experimental)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://experimental.buildd.net/index-${arch}.html\">experimental</a>]"
					;;
				unstable-non-free)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://non-free.buildd.net/index-${arch}.html\">non-free</a>]"
					;;
				etch-volatile)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://volatile.buildd.net/index-${arch}.html\">etch-volatile</a>]"
					;;
				unstable)
					echo >>  $pfad/template/index-${arch}.html "	  [<a href=\"http://unstable.buildd.net/index-${arch}.html\">unstable</a>]"
					;;
			esac
		else
			case "$flav" in
				etch-bpo)
					echo >>  $pfad/template/index-${arch}.html "	  [backports]"
					;;
				etch-secure)
					echo >>  $pfad/template/index-${arch}.html "	  [etch-secure]"
					;;
				etch-skolelinux)
					echo >>  $pfad/template/index-${arch}.html "	  [skolelinux]"
					;;
				experimental)
					echo >>  $pfad/template/index-${arch}.html "	  [experimental]"
					;;
				unstable-non-free)
					echo >>  $pfad/template/index-${arch}.html "	  [non-free]"
					;;
				etch-volatile)
					echo >>  $pfad/template/index-${arch}.html "	  [etch-volatile]"
					;;
				unstable)
					echo >>  $pfad/template/index-${arch}.html "	  [unstable]"
					;;
			esac
		fi
	done
	cat /home/builddnet/template/top2.html | sed -e s/%FLAVOUR%/$flavour/g -e s/%ARCH%/$arch/g >> $pfad/template/index-${arch}.html
	
	#cat /home/builddnet/template/top.html | sed -e s/%FLAVOUR%/$flavour/g -e s/%ARCH%/$arch/g >> $pfad/template/index-${arch}.html 
	for toparch in $ALL; do
		if [ $flavour = "etch-volatile" ]; then
			dnsflavour="volatile"
		elif [ $flavour = "etch-skolelinux" ]; then
			dnsflavour="skolelinux"
		elif [ $flavour = "unstable-non-free" ]; then
			dnsflavour="non-free"
		elif [ $flavour = "etch-volatile" ]; then
			dnsflavour="volatile"
		elif [ $flavour = "etch-bpo" ]; then
			dnsflavour="backports"
		else
			dnsflavour=$flavour
		fi
		echo "[<a href="http://$dnsflavour.buildd.net/index-$toparch.html">$toparch</a>]" >> $pfad/template/index-${arch}.html
	done
	cat $pfad/template/header.html | sed -e s/%FLAVOUR%/$flavour/g -e s/%ARCH%/$arch/g -e s/%ETA%/"${ETA}"/g -e s/%MTIME%/"$mtime"/g >> $pfad/template/index-${arch}.html
	if [ ! -r /home/builddnet/bin/.maintenance ]; then
		/home/builddnet/bin/update-buildds.py $flavour ${arch} > $pfad/template/index-${arch}.html.buildd 
	fi 
	cat $pfad/template/index-${arch}.html.buildd >> $pfad/template/index-${arch}.html
	cat $pfad/template/${arch}.html >> $pfad/template/index-${arch}.html 
	cat $pfad/template/footer.html >> $pfad/template/index-${arch}.html
	echo "<p>Last modified: "`date`"</BODY></HTML>" >> $pfad/template/index-${arch}.html
done

#if [ ! -r /home/builddnet/bin/.maintenance ]; then
	mv $pfad/template/index-*.html $pfad/WWW/
#fi

rm $CHECKFILE


