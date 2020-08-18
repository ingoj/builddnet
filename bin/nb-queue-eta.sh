#!/bin/bash

flavour=$1
arch=$2

trap "exit 0" EXIT 

cd /home/builddnet/${flavour}/listdir

nbp=`grep ": Needs-Build \[" ${arch}-all.txt | awk '{print $1}' | xargs -n 1 basename | cut -f1 -d"_" | xargs echo | sed -e "s/\ /\',\ \'\ /g" | tr -d [:blank:]`
#echo $nbp
#ETA=`psql -t -U builddnet buildd -c "select date_trunc('seconds', sum(erg)) from (select avg(endtime-begin) as erg from ptracker where arch='${arch}' and packagename in ('${nbp}') group by packagename) as erg" | tail -n 3 | head -n 1`
ETA=`psql -t -h db.windfluechter.net -U builddnet buildd -c "select date_trunc('seconds', justify_hours(sum(erg))) from (select avg(endtime-begin) as erg from ptracker where arch='${arch}' and packagename in ('${nbp}') group by packagename) as erg"`
#ETA=`psql -U builddnet buildd -c "select date_trunc('seconds', sum(erg/nb)) from (select avg(endtime-begin) as erg from ptracker where arch='${arch}' and packagename in ('${nbp}') group by packagename) as erg, (select count(*) as nb from status where status='2' and arch='$arch') as nb" | tail -n 3 | head -n 1`


nbp2=`echo $nbp | sed -e "s/'/ /g" -e "s/,//g" | tr -s " "| sed -e "s/ /\n/g"`

rm ${arch}_queue_order.txt
for p in $nbp2; do
	echo $p >> ${arch}_queue_order.txt
done

echo $ETA > ${arch}_nbq_ETA.txt
echo $ETA

exit 0
