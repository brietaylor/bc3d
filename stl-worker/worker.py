#!/usr/bin/env python3
"""Process a list of data in parallel, using Blender"""
import multiprocessing as mp
import subprocess
import os
import shutil
import argparse
from tempfile import mkdtemp

import boto3
s3 = boto3.client('s3')

mutex = mp.Lock()

S3_BUCKET = 'jefftaylor-maps'

TIF_FORMAT = 'bc3d_tifs/tile{tile:03}_cdem.utm.tif.xz'
DEST_PREFIX = 'bc3d_tiles/tile'
STL_FORMAT = DEST_PREFIX + '{tile:03}_{strength}x_{subdivisions}.stl.xz'

def process(params):
    """Download files, extract, process, compress, and upload result"""
    s3_tif_xz, s3_stl_xz, extra_args = params

    work_dir = mkdtemp(dir='/opt')

    tif_xz = os.path.join(work_dir, 'tile.tif.xz')
    s3.download_file(S3_BUCKET, s3_tif_xz, tif_xz)

    tif = tif_xz[:-3]
    subprocess.call(('xz', '-d', tif_xz))

    # Run Blender in a critical section, since we provision a node based on
    # its peak memory usage.
    stl = os.path.join(work_dir, 'tile.stl')
    with mutex:
        blender_cmd = ('blender', '--background', '--python',
                       'dem23d_blender.py', '--')
        subprocess.call(blender_cmd + extra_args + (tif, stl))

    stl_xz = stl + '.xz'
    subprocess.call(('xz', stl))

    # Upload stl.xz to AWS
    s3.upload_file(stl_xz, S3_BUCKET, s3_stl_xz)
    shutil.rmtree(work_dir)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subdivisions', type=int, default=500,
                        help="Number of grid points in each axis")
    parser.add_argument('--strength', type=float, default=3,
                        help="Terrain exaggeration")
    parser.add_argument('tiles', type=int, nargs='+',
                        help="List of tiles to process")

    args, extra_args = parser.parse_known_args()
    extra_args += ('--strength', str(args.strength))
    extra_args += ('--subdivisions', str(args.subdivisions))

    return args, tuple(extra_args)

class S3ObjectList():
    """Maintain a list of S3 objects so we don't have to query every loop."""
    def __init__(self, prefix):
        self.prefix = prefix
        self.keys = set()

        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=self.prefix):
            for result in page['Contents']:
                self.keys.add(result['Key'])

    def exists(self, key):
        """Return: true if object key exists"""
        assert key.startswith(self.prefix)
        return key in self.keys

def main():
    args, extra_args = parse_args()
    pool = mp.Pool()
    obj_list = S3ObjectList(DEST_PREFIX)

    def get_jobs():
        for tile in args.tiles:
            args_dict = {
                'tile': tile,
                'strength': args.strength,
                'subdivisions': args.subdivisions,
            }
            s3_tif_xz = TIF_FORMAT.format(**args_dict)
            s3_stl_xz = STL_FORMAT.format(**args_dict)

            # Check S3 target directory
            if obj_list.exists(s3_stl_xz):
                continue

            yield s3_tif_xz, s3_stl_xz, extra_args

    list(pool.imap_unordered(process, get_jobs()))

    print('Done!')

main()
