#!/bin/bash

ALL="experimental unstable-non-free etch-volatile etch-secure etch-bpo"

#for i in experimental unstable-non-free etch-volatile etch-secure etch-bpo; do 
for i in $ALL ; do 
  echo -n "Processing $i..."
  cd /home/builddnet/$i 
  /home/builddnet/bin/get_all-txt $i all 
  /home/builddnet/bin/generate-html.sh $i
  cd ..
  echo "done."
done

