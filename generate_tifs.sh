#!/usr/bin/bash
tiles=$(sqlite3 ~/running_gis/bc3d_grid.sqlite "select ogc_fid from grid")
for t in $tiles; do
	~/coding/bc3d/warp_dem.sh $t
done
