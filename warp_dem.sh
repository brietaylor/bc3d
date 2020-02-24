#!/bin/bash
if [ -z "$1" ]; then
	echo "usage: $0 srcfile id"
	exit 1
fi
set -eux

id=$1
srcfile=../cdem_canada/merged/cdem_bc_merged_virt.vrt
tmpdir=$(mktemp -d)
dstfile=$id/cdem_utm.tif

rm -f "$dstfile"

xmin=$(sqlite3 grid.sqlite "select left from grid where id = $id")
xmax=$(sqlite3 grid.sqlite "select right from grid where id = $id")
ymin=$(sqlite3 grid.sqlite "select bottom from grid where id = $id")
ymax=$(sqlite3 grid.sqlite "select top from grid where id = $id")

warped="$tmpdir"/warped.tif
mkdir -p $id
gdalwarp \
	-t_srs EPSG:32610 \
	-te "$xmin" "$ymin" "$xmax" "$ymax" \
	-tr 25 25 \
	"$srcfile" "$warped"

raised="$tmpdir"/raised.tif
# Raise everything up by 34
gdal_calc.py --calc="A+34" --outfile="$raised" -A "$warped"

# Drop the ocean back down to 0
gdal_rasterize -burn 0 ../water-polygons-split-4326/water_polygons.sqlite "$raised"

# Copy over destination
cp "$raised" "$dstfile"
