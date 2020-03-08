#!/bin/bash
set -eux

tiles="082 083 084 092 093 094 102 103 104 114"

HOST="ftp.maps.canada.ca"
REMOTE="/pub/nrcan_rncan/elevation/cdem_mnec"
LOCAL="/home/jeff/running_gis/cdem_canada/ftp_tiles"
UNZIPPED="/home/jeff/running_gis/cdem_canada/unzipped"

for t in $tiles; do
	wd="$LOCAL"/"$t"
	lftp -f "
	open $HOST
	lcd $wd
	mirror --continue --delete --verbose $REMOTE/$t $wd
	bye
	"

	for zipfile in "$wd/*.zip"; do
		unzip -u "$zipfile" -d "$UNZIPPED/$t/" "*.tif"
	done
done

echo 'Done!'
