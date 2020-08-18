#!/bin/sh

cd ~/listdir/
for ARCH in alpha arm armeb armel hppa i386 ia64 m68k mips mipsel powerpc s390 sparc; do

#rm -f -- "${ARCH}_stats-history"
#wget "http://www.buildd.net/buildd/${ARCH}_stats-history"
cat "${ARCH}_stats-history" \
| while read a b c d e f num; do
    DATE="$a $b $c $d $e $f"
    HOUR=`date -d "$a $b $c $d $e $f" +%H`
    if [ "$ARCH" = "m68k" -o "$HOUR" = "00" -o "$HOUR" = "06" -o "$HOUR" = "12" -o "$HOUR" = "18" ]; then
      echo `date -d "$DATE" +%s` $num;
    fi
  done >"${ARCH}.data"
(
  echo set terminal png
  echo set xdata time
  echo set timefmt '"%s"'
  echo set format x '"%Y\n%b %d"'
  echo set ylabel '"Needs-Build"'
  echo plot '"'"${ARCH}.data"'"' using '1:2' title '"'"${ARCH}"'"' with lines
) \
| gnuplot >"${ARCH}_stats.png"
done

(
  echo set terminal png
  echo set xdata time
  echo set timefmt '"%s"'
  echo set format x '"%Y\n%b %d"'
  echo set ylabel '"Needs-Build"'
  echo -n plot '"'alpha.data'"' using 1:2 title '"'alpha'"' with lines
  for ARCH in arm armeb armel hppa i386 ia64 m68k mips mipsel powerpc s390 sparc; do
    echo -n , '"'"${ARCH}.data"'"' using 1:2 title '"'"$ARCH"'"' with lines
  done
  echo
) \
| gnuplot >"all_stats.png"
