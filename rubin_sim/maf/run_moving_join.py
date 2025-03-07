#!/usr/bin/env python

import os
import glob
import argparse
import numpy as np
import matplotlib

matplotlib.use("Agg")

from . import batches as batches


def run_moving_join():
    """Join split metric outputs into a single metric output file."""
    parser = argparse.ArgumentParser(
        description="Join moving object metrics (from splits) for a particular "
        "opsim run.  Assumes split metric files are in "
        "<orbitRoot_split> subdirectories of baseDir. "
    )
    parser.add_argument(
        "--orbitFile", type=str, help="File containing the moving object orbits."
    )
    parser.add_argument(
        "--baseDir",
        type=str,
        default=".",
        help="Root directory containing split (or single) metric outputs.",
    )
    parser.add_argument(
        "--outDir",
        type=str,
        default=None,
        help="Output directory for moving object metrics. Default [orbitRoot]",
    )
    args = parser.parse_args()

    if args.orbitFile is None:
        print("Must specify an orbitFile")
        exit()

    # Outputs from the metrics are generally like so:
    #  <baseDir>/<splitDir>/<metricFileName>
    # - baseDir tends to be <opsimName_orbitRoot> (but is set by user when starting to generate obs.)
    # - splitDir tends to be <orbitRoot_split#> (and is set by observation generation script)
    # - metricFile is <opsimName_metricName_metadata(NEO/L7/etc + metadata from metric script)_MOOB.npz
    #  (the metricFileName is set by the metric generation script - run_moving_calc.py).
    #  (note that split# does not show up in the metricFileName, and is not used in run_moving_calc.py).
    #  ... this lets run_moving_calc.py easily run in parallel on multiple splits.

    # Assume splits = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    splits = np.arange(0, 10, 1)
    orbitRoot = (
        args.orbitFile.replace(".txt", "").replace(".des", "").replace(".s3m", "")
    )

    if args.outDir is not None:
        outDir = args.outDir
    else:
        outDir = f"{orbitRoot}"

    # Scan first splitDir for all metric files.
    tempdir = os.path.join(args.baseDir, f"{orbitRoot}_{splits[0]}")
    print(
        f"# Joining files from {orbitRoot}_[0-9]; will use {tempdir} to find metric names."
    )

    metricfiles = glob.glob(os.path.join(tempdir, "*MOOB.npz"))
    # Identify metric names that we want to join.
    metricNames = []
    for m in metricfiles:
        mname = os.path.split(m)[-1]
        # Hack out raw Discovery outputs. We don't want to join the raw discovery files.
        # This is a hack because currently we're just pulling out _Time and _N_Chances to join.
        if "Discovery" in mname:
            if "Discovery_Time" in mname:
                metricNames.append(mname)
            elif "Discovery_N_Chances" in mname:
                metricNames.append(mname)
            elif "Magic" in mname:
                metricNames.append(mname)
            else:
                pass
        else:
            metricNames.append(mname)

    if len(metricNames) == 0:
        print(f"Could not read any metric files from {tempdir}")
        exit()

    # Create the output directory.
    if not (os.path.isdir(outDir)):
        os.makedirs(outDir)

    # Read and combine the metric files.
    for m in metricNames:
        b = batches.readAndCombine(orbitRoot, args.baseDir, splits, m)
        b.write(outDir=outDir)
