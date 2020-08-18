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
pfad=/home/builddnet/$flavour
#ALL="alpha arm hppa i386 ia64 m68k mips mipsel powerpc s390 sparc"
#ALL="hppa ia64 m68k powerpc"
ALL=`cat /home/builddnet/bin/archs_${flavour}`

TITLES=("" "Time" "Installed" "Needs-Build" "Building" "Uploaded" "Failed" "Dep-Wait" "Reupload-Wait" "Install-Wait" "Failed-Removed" "Dep-Wait-Removed" "Not-For-Us" "total")

cd $pfad/listdir

for arch in $ALL; do
  echo "{${flavour} : $arch }"
#  grep Needs-Build ~/listdir/${arch}_stats | cut -f2 -d: | xargs echo >> ~/listdir/${arch}_stats-history `date`
  grep "^[A-Zt].*: " ${arch}_stats \
  | cut -f2 -d: | cut -f1 -d"(" \
  | xargs echo >> ${arch}_stats-full-history `date +%s`
  echo `tail -n 1 ${arch}_stats-full-history` | xargs /home/builddnet/bin/builddgraph.py add $flavour $arch 
  tail -n 240 ${arch}_stats-full-history > ${arch}_stats-history.new
# 335 ----^^^
  mv ${arch}_stats-history.new ${arch}_stats-history
  (
    echo set terminal png enhanced size 900,600
    echo set nologscale y
    echo set xdata time
    echo set key top outside
#    echo set key box 
    echo set timefmt '"%s"'
    echo set format x '"%Y\n%b %d"'
	echo set linestyle 1 lt 2 lw 3 pt 3 ps 4
    SEP="plot"
    for i in 3 4 5 6 7 8 9 10 11 12; do
      echo -n "$SEP "; SEP=","
      echo -n '"'${arch}_stats-history'"' using 1:$i title '"' ${TITLES[$i]}'"' with lines
    done
    echo
  ) | gnuplot >${arch}_stats.png
done

for i in 2 3 4 5 6 7 8 9 10 11 12 13; do
  (
    echo set terminal png enhanced size 900,600
    echo set logscale y 10
    echo set xdata time
    echo set key top outside
    echo set timefmt '"%s"'
    echo set format x '"%Y\n%b %d"'
    echo set linestyle 1 lt 2 lw 3 pt 3 ps 10
    echo set ylabel '"'${TITLES[$i]}'"'
    SEP="plot"
    for arch in $ALL; do
      echo -n "$SEP "; SEP=","
      echo -n '"'${arch}_stats-history'"' using 1:$i title '"' $arch'"' with lines
    done
    echo
  ) | gnuplot >${TITLES[$i]}_stats.png
done
