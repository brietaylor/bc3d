#!/bin/bash
# Create warped DEM tiles from a single merged source.

if [ -z "$1" ]; then
	echo "usage: $0 id"
	exit 1
fi
set -eux

gis_dir=/home/jeff/running_gis/

id=$1
srcfile="$gis_dir"/cdem_canada/merged/cdem_bc_merged_virt.vrt
sql="$gis_dir"/bc3d_grid.sqlite
tmpdir=$(mktemp -d)
function cleanup {
	rm -rf "$tmpdir"
}
trap cleanup EXIT

id_pad=$(printf "%03d" "$id")

dstfile="$gis_dir"/bc3d_models/all/tile"$id_pad"_cdem.utm.tif

rm -f "$dstfile"

xmin=$(sqlite3 "$sql" "select left from grid where ogc_fid = $id")
xmax=$(sqlite3 "$sql" "select right from grid where ogc_fid = $id")
ymin=$(sqlite3 "$sql" "select bottom from grid where ogc_fid = $id")
ymax=$(sqlite3 "$sql" "select top from grid where ogc_fid = $id")

warped="$tmpdir"/warped.tif
gdalwarp \
	-t_srs EPSG:32610 \
	-te "$xmin" "$ymin" "$xmax" "$ymax" \
	-tr 25 25 \
	"$srcfile" "$warped"

raised="$tmpdir"/raised.tif
# Raise everything up by one layer.  35m * 3 / 1e6 ~= 0.1mm
gdal_calc.py \
	--NoDataValue=0 \
	--quiet \
	--calc="A+35" \
	-A "$warped" \
	--outfile="$raised"

# Drop the ocean back down to 0
gdal_rasterize \
	-burn 0 \
	"$gis_dir"/water-polygons-split-4326/water_polygons.sqlite "$raised"

# Copy over destination
cp "$raised" "$dstfile"

#xz -k "$dstfile"

