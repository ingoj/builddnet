#!/bin/bash
#
# Copyright (c) 2003-2006,  Goswin Brederlow <brederlo@informatik.uni-tuebingen.de>
#							Ingo Juergensmann <ij@buildd.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# nb-stats.sh comes with ABSOLUTELY NO WARRANTY
#

flavour=$1
buildd=$2
pfad=/home/builddnet/WWW/hoststats
#$flavour
#ALL="alpha arm hppa i386 ia64 m68k mips mipsel powerpc s390 sparc"
#ALL="hppa ia64 m68k powerpc"
#ALL=`cat $pfad/bin/archs`


TITLES=("" "Time" "uptime" "users" "lavg" "memtotal" "memfree" "swaptotal" "swapfree")

cd $pfad

modes="mem swap"

#XENVIRONMENT=/home/builddnet/.Xdefaults

for mode in $modes; do
  #psql -t -U builddnet buildd -c "select date_trunc('seconds', dtstamp), ${mode}total-${mode}free, ${mode}free from hoststats where buildd='${buildd}' order by dtstamp desc limit 20" | sed -e 's/|/ /g' | tr -s " " > ${buildd}-hoststats-${mode}.txt
  psql -t -h db.windfluechter.net -U builddnet buildd -c "select date_trunc('seconds', dtstamp), ${mode}total, ${mode}total-${mode}free from hoststats where buildd='${buildd}' order by dtstamp desc limit 20" | sed -e 's/|/ /g' | tr -s " " > ${buildd}-hoststats-${mode}.txt
  logger 'psql -t -U builddnet buildd -c "select date_trunc('seconds', dtstamp), ${mode}total-${mode}free, ${mode}free from hoststats where buildd='${buildd}' order by dtstamp limit 20"'
  (
	echo "set terminal png enhanced size 160,80 xffffff x000000 x404040 x00ff00 xff0000"
    #echo set logscale y 10
    echo set xdata time
    #echo set key top outside
	
	echo set noxtics
	echo set noytics
	echo set yrange [0:]
	echo set timefmt '"%Y-%m-%d %H:%M:%S"'
    #echo set format x '"%Y\n%m %d"'
    #echo set linestyle 1 lt 2 lw 3 pt 3 ps 10
    #echo set ylabel '"'${TITLES}'"'
    #echo set xrange [0:20]
	#echo set line 2 #00ff00 
	#echo "set line 1 #ff0000"
	SEP="plot" 
	echo "plot \"${buildd}-hoststats-${mode}.txt\" using 1:3 notitle with filledcurve x1, \"${buildd}-hoststats-${mode}.txt\" using 1:4 notitle with filledcurve x1"
    echo
  ) | gnuplot > ${buildd}_hoststats_${mode}.png
  chmod a+rw ${buildd}[_-]hoststats[_-]${mode}.*
done

