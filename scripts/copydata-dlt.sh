#!/bin/bash
#
# Copy DLT data to /var/www
# Run as sudo

#tapeNos=(1 2 4 6 7 12 14)
tapeNos=(2 4 6 7 12 14)

#sudo rsync -avhl /media/johan/xxLINK/xxLINK-DLT/tapes-DLT/1/file000001/www/ /var/www/xxLINK-DLT-1
#sudo find /var/www/xxLINK-DLT-1 -type d -exec chmod 755 {} \;
#sudo find /var/www/xxLINK-DLT-1 -type f -exec chmod 644 {} \;

for i in "${tapeNos[@]}"
do
    echo "Processing tape ""$i"
    rsync -avhl /media/johan/xxLINK/xxLINK-DLT/tapes-DLT/"$i"/file000001/www/ /var/www/xxLINK-DLT-"$i"
    find /var/www/xxLINK-DLT-"$i" -type d -exec chmod 755 {} \;
    find /var/www/xxLINK-DLT-"$i" -type f -exec chmod 644 {} \;
done
