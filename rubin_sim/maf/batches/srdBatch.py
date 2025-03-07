"""Metrics to investigate quantities related to SRD.
Potentially could diverge from versions in scienceRadar.
"""
import warnings
import numpy as np
import healpy as hp
import rubin_sim.maf.metrics as metrics
import rubin_sim.maf.slicers as slicers
import rubin_sim.maf.stackers as stackers
import rubin_sim.maf.plots as plots
import rubin_sim.maf.metricBundles as mb
from .colMapDict import ColMapDict
from .common import standardSummary, radecCols, combineInfoLabels

__all__ = ["fOBatch", "astrometryBatch", "rapidRevisitBatch"]


def fOBatch(
    colmap=None,
    runName="opsim",
    extraSql=None,
    extraInfoLabel=None,
    slicer=None,
    benchmarkArea=18000,
    benchmarkNvisits=825,
    minNvisits=750,
):
    """Metrics for calculating fO.

    Parameters
    ----------
    colmap : `dict` or None, optional
        A dictionary with a mapping of column names. Default will use OpsimV4 column names.
    runName : `str`, optional
        The name of the simulated survey. Default is "opsim".
    extraSql : `str` or None, optional
        Additional sql constraint to apply to all metrics.
    extraInfoLabel : `str` or None, optional
        Additional info_label to apply to all results.
    slicer : `rubin_sim.maf.slicer.HealpixSlicer` or None, optional
         This must be a HealpixSlicer or some kind, although could be a HealpixSubsetSlicer.
         Default is a HealpixSlicer with nside=64.

    Returns
    -------
    metricBundleDict
    """
    if colmap is None:
        colmap = ColMapDict("fbs")

    bundleList = []

    sql = ""
    info_label = "All visits"
    # Add additional sql constraint (such as wfdWhere) and info_label, if provided.
    if (extraSql is not None) and (len(extraSql) > 0):
        sql = extraSql
        if extraInfoLabel is None:
            info_label = extraSql.replace("filter =", "").replace("filter=", "")
            info_label = info_label.replace('"', "").replace("'", "")
    if extraInfoLabel is not None:
        info_label = extraInfoLabel

    subgroup = info_label

    raCol, decCol, degrees, ditherStacker, ditherMeta = radecCols(None, colmap, None)
    # Don't want dither info in subgroup (too long), but do want it in bundle name.
    info_label = combineInfoLabels(info_label, ditherMeta)

    # Set up fO metric.
    if slicer is None:
        nside = 64
        slicer = slicers.HealpixSlicer(
            nside=nside, latCol=decCol, lonCol=raCol, latLonDeg=degrees
        )
    else:
        try:
            nside = slicer.nside
        except AttributeError:
            warnings.warn("Must use a healpix slicer. Swapping to the default.")
            nside = 64
            slicer = slicers.HealpixSlicer(
                nside=nside, latCol=decCol, lonCol=raCol, latLonDeg=degrees
            )

    displayDict = {"group": "SRD FO metrics", "subgroup": subgroup, "order": 0}

    # Configure the count metric which is what is used for f0 slicer.
    metric = metrics.CountExplimMetric(
        col=colmap["mjd"], metricName="fO", expCol=colmap["exptime"]
    )
    plotDict = {
        "xlabel": "Number of Visits",
        "Asky": benchmarkArea,
        "Nvisit": benchmarkNvisits,
        "xMin": 0,
        "xMax": 1500,
    }
    summaryMetrics = [
        metrics.fOArea(
            nside=nside,
            norm=False,
            metricName="fOArea",
            Asky=benchmarkArea,
            Nvisit=benchmarkNvisits,
        ),
        metrics.fOArea(
            nside=nside,
            norm=True,
            metricName="fOArea/benchmark",
            Asky=benchmarkArea,
            Nvisit=benchmarkNvisits,
        ),
        metrics.fONv(
            nside=nside,
            norm=False,
            metricName="fONv",
            Asky=benchmarkArea,
            Nvisit=benchmarkNvisits,
        ),
        metrics.fONv(
            nside=nside,
            norm=True,
            metricName="fONv/benchmark",
            Asky=benchmarkArea,
            Nvisit=benchmarkNvisits,
        ),
        metrics.fOArea(
            nside=nside,
            norm=False,
            metricName=f"fOArea_{minNvisits}",
            Asky=benchmarkArea,
            Nvisit=minNvisits,
        ),
    ]
    caption = "The FO metric evaluates the overall efficiency of observing. "
    caption += (
        "foNv: out of %.2f sq degrees, the area receives at least X and a median of Y visits "
        "(out of %d, if compared to benchmark). " % (benchmarkArea, benchmarkNvisits)
    )
    caption += (
        "fOArea: this many sq deg (out of %.2f sq deg if compared "
        "to benchmark) receives at least %d visits. "
        % (benchmarkArea, benchmarkNvisits)
    )
    displayDict["caption"] = caption
    bundle = mb.MetricBundle(
        metric,
        slicer,
        sql,
        plotDict=plotDict,
        stackerList=[ditherStacker],
        displayDict=displayDict,
        summaryMetrics=summaryMetrics,
        plotFuncs=[plots.FOPlot()],
        info_label=info_label,
    )
    bundleList.append(bundle)
    # Set the runName for all bundles and return the bundleDict.
    for b in bundleList:
        b.setRunName(runName)
    return mb.makeBundlesDictFromList(bundleList)


def astrometryBatch(
    colmap=None,
    runName="opsim",
    extraSql=None,
    extraInfoLabel=None,
    slicer=None,
):
    """Metrics for evaluating proper motion and parallax.

    Parameters
    ----------
    colmap : `dict` or None, optional
        A dictionary with a mapping of column names. Default will use OpsimV4 column names.
    runName : `str`, optional
        The name of the simulated survey. Default is "opsim".
    extraSql : `str` or None, optional
        Additional sql constraint to apply to all metrics.
    extraInfoLabel : `str` or None, optional
        Additional info_label to apply to all results.
    slicer : `rubin_sim.maf.slicer` or None, optional
        Optionally, specify something other than an nside=64 healpix slicer.

    Returns
    -------
    metricBundleDict
    """
    if colmap is None:
        colmap = ColMapDict("fbs")
    bundleList = []

    sql = ""
    info_label = "All visits"
    # Add additional sql constraint (such as wfdWhere) and info_label, if provided.
    if (extraSql is not None) and (len(extraSql) > 0):
        sql = extraSql
        if extraInfoLabel is None:
            info_label = extraSql.replace("filter =", "").replace("filter=", "")
            info_label = info_label.replace('"', "").replace("'", "")
    if extraInfoLabel is not None:
        info_label = extraInfoLabel

    subgroup = info_label

    raCol = colmap["ra"]
    decCol = colmap["dec"]
    degrees = colmap["raDecDeg"]

    rmags_para = [22.4, 24.0]
    rmags_pm = [20.5, 24.0]

    # Set up parallax/dcr stackers.
    parallaxStacker = stackers.ParallaxFactorStacker(
        raCol=raCol, decCol=decCol, dateCol=colmap["mjd"], degrees=degrees
    )
    dcrStacker = stackers.DcrStacker(
        filterCol=colmap["filter"],
        altCol=colmap["alt"],
        degrees=degrees,
        raCol=raCol,
        decCol=decCol,
        lstCol=colmap["lst"],
        site="LSST",
        mjdCol=colmap["mjd"],
    )

    # Set up parallax metrics.
    if slicer is None:
        slicer = slicers.HealpixSlicer(
            nside=64, lonCol=raCol, latCol=decCol, latLonDeg=degrees
        )
    subsetPlots = [plots.HealpixSkyMap(), plots.HealpixHistogram()]

    displayDict = {
        "group": "SRD Parallax",
        "subgroup": subgroup,
        "order": 0,
        "caption": None,
    }
    # Expected error on parallax at 10 AU.
    plotmaxVals = (2.0, 15.0)
    good_parallax_limit = 11.5
    summary = [
        metrics.AreaSummaryMetric(
            area=18000,
            reduce_func=np.median,
            decreasing=False,
            metricName="Median Parallax Uncert (18k)",
        ),
        metrics.AreaThresholdMetric(
            upper_threshold=good_parallax_limit,
            metricName="Area better than %.1f mas uncertainty" % good_parallax_limit,
        ),
    ]
    summary.append(
        metrics.PercentileMetric(
            percentile=95, metricName="95th Percentile Parallax Uncert"
        )
    )
    summary.extend(standardSummary())
    for rmag, plotmax in zip(rmags_para, plotmaxVals):
        plotDict = {"xMin": 0, "xMax": plotmax, "colorMin": 0, "colorMax": plotmax}
        metric = metrics.ParallaxMetric(
            metricName="Parallax Uncert @ %.1f" % (rmag),
            rmag=rmag,
            seeingCol=colmap["seeingGeom"],
            filterCol=colmap["filter"],
            m5Col=colmap["fiveSigmaDepth"],
            normalize=False,
        )
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            stackerList=[parallaxStacker],
            displayDict=displayDict,
            plotDict=plotDict,
            summaryMetrics=summary,
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1

    # Parallax normalized to 'best possible' if all visits separated by 6 months.
    # This separates the effect of cadence from depth.
    for rmag in rmags_para:
        metric = metrics.ParallaxMetric(
            metricName="Normalized Parallax Uncert @ %.1f" % (rmag),
            rmag=rmag,
            seeingCol=colmap["seeingGeom"],
            filterCol=colmap["filter"],
            m5Col=colmap["fiveSigmaDepth"],
            normalize=True,
        )
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            stackerList=[parallaxStacker],
            displayDict=displayDict,
            summaryMetrics=standardSummary(),
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1
    # Parallax factor coverage.
    for rmag in rmags_para:
        metric = metrics.ParallaxCoverageMetric(
            metricName="Parallax Coverage @ %.1f" % (rmag),
            rmag=rmag,
            m5Col=colmap["fiveSigmaDepth"],
            mjdCol=colmap["mjd"],
            filterCol=colmap["filter"],
            seeingCol=colmap["seeingGeom"],
        )
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            stackerList=[parallaxStacker],
            displayDict=displayDict,
            summaryMetrics=standardSummary(),
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1
    # Parallax problems can be caused by HA and DCR degeneracies. Check their correlation.
    for rmag in rmags_para:
        metric = metrics.ParallaxDcrDegenMetric(
            metricName="Parallax-DCR degeneracy @ %.1f" % (rmag),
            rmag=rmag,
            seeingCol=colmap["seeingEff"],
            filterCol=colmap["filter"],
            m5Col=colmap["fiveSigmaDepth"],
        )
        caption = (
            "Correlation between parallax offset magnitude and hour angle for a r=%.1f star."
            % (rmag)
        )
        caption += " (0 is good, near -1 or 1 is bad)."
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            stackerList=[dcrStacker, parallaxStacker],
            displayDict=displayDict,
            summaryMetrics=standardSummary(),
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1

    # Proper Motion metrics.
    displayDict = {
        "group": "SRD Proper Motion",
        "subgroup": subgroup,
        "order": 0,
        "caption": None,
    }
    # Proper motion errors.
    plotmaxVals = (1.0, 5.0)
    summary = [
        metrics.AreaSummaryMetric(
            area=18000,
            reduce_func=np.median,
            decreasing=False,
            metricName="Median Proper Motion Uncert (18k)",
        )
    ]
    summary.append(
        metrics.PercentileMetric(metricName="95th Percentile Proper Motion Uncert")
    )
    summary.extend(standardSummary())
    for rmag, plotmax in zip(rmags_pm, plotmaxVals):
        plotDict = {"xMin": 0, "xMax": plotmax, "colorMin": 0, "colorMax": plotmax}
        metric = metrics.ProperMotionMetric(
            metricName="Proper Motion Uncert @ %.1f" % rmag,
            rmag=rmag,
            m5Col=colmap["fiveSigmaDepth"],
            mjdCol=colmap["mjd"],
            filterCol=colmap["filter"],
            seeingCol=colmap["seeingGeom"],
            normalize=False,
        )
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            displayDict=displayDict,
            plotDict=plotDict,
            summaryMetrics=summary,
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1
    # Normalized proper motion.
    for rmag in rmags_pm:
        metric = metrics.ProperMotionMetric(
            metricName="Normalized Proper Motion Uncert @ %.1f" % rmag,
            rmag=rmag,
            m5Col=colmap["fiveSigmaDepth"],
            mjdCol=colmap["mjd"],
            filterCol=colmap["filter"],
            seeingCol=colmap["seeingGeom"],
            normalize=True,
        )
        bundle = mb.MetricBundle(
            metric,
            slicer,
            sql,
            info_label=info_label,
            displayDict=displayDict,
            summaryMetrics=standardSummary(),
            plotFuncs=subsetPlots,
        )
        bundleList.append(bundle)
        displayDict["order"] += 1

    # Set the runName for all bundles and return the bundleDict.
    for b in bundleList:
        b.setRunName(runName)
    return mb.makeBundlesDictFromList(bundleList)


def rapidRevisitBatch(
    colmap=None,
    runName="opsim",
    extraSql=None,
    extraInfoLabel=None,
    slicer=None,
):
    """Metrics for evaluating proper motion and parallax.

    Parameters
    ----------
    colmap : `dict` or None, optional
        A dictionary with a mapping of column names. Default will use OpsimV4 column names.
    runName : `str`, optional
        The name of the simulated survey. Default is "opsim".
    extraSql : `str` or None, optional
        Additional sql constraint to apply to all metrics.
    extraInfoLabel : `str` or None, optional
        Additional info_label to apply to all results.
    slicer : `rubin_sim_maf.slicers.HealpixSlicer` or None, optional
        Optionally, specify something other than an nside=64 healpix slicer. (must be a healpix slicer)

    Returns
    -------
    metricBundleDict
    """
    if colmap is None:
        colmap = ColMapDict("fbs")
    bundleList = []

    sql = ""
    info_label = "All visits"
    # Add additional sql constraint (such as wfdWhere) and info_label, if provided.
    if (extraSql is not None) and (len(extraSql) > 0):
        sql = extraSql
        if extraInfoLabel is None:
            info_label = extraSql.replace("filter =", "").replace("filter=", "")
            info_label = info_label.replace('"', "").replace("'", "")
    if extraInfoLabel is not None:
        info_label = extraInfoLabel

    subgroup = info_label

    raCol = colmap["ra"]
    decCol = colmap["dec"]
    degrees = colmap["raDecDeg"]

    if slicer is None:
        nside = 64
        slicer = slicers.HealpixSlicer(
            nside=nside, lonCol=raCol, latCol=decCol, latLonDeg=degrees
        )
    else:
        try:
            nside = slicer.nside
        except AttributeError:
            warnings.warn("Must use a healpix slicer. Swapping to the default.")
            nside = 64
            slicer = slicers.HealpixSlicer(
                nside=nside, latCol=decCol, lonCol=raCol, latLonDeg=degrees
            )

    subsetPlots = [plots.HealpixSkyMap(), plots.HealpixHistogram()]

    displayDict = {
        "group": "SRD Rapid Revisits",
        "subgroup": subgroup,
        "order": 0,
        "caption": None,
    }

    # Calculate the actual number of revisits within 30 minutes.
    dTmax = 30  # time in minutes
    m2 = metrics.NRevisitsMetric(
        dT=dTmax, mjdCol=colmap["mjd"], normed=False, metricName="NumberOfQuickRevisits"
    )
    plotDict = {"colorMin": 400, "colorMax": 2000, "xMin": 400, "xMax": 2000}
    caption = (
        "Number of consecutive visits with return times faster than %.1f minutes, "
        % (dTmax)
    )
    caption += "in any filter, all proposals. "
    displayDict["caption"] = caption
    bundle = mb.MetricBundle(
        m2,
        slicer,
        sql,
        plotDict=plotDict,
        plotFuncs=subsetPlots,
        info_label=info_label,
        displayDict=displayDict,
        summaryMetrics=standardSummary(withCount=False),
    )
    bundleList.append(bundle)
    displayDict["order"] += 1

    # Better version of the rapid revisit requirements: require a minimum number of visits between
    # dtMin and dtMax, but also a minimum number of visits between dtMin and dtPair (the typical pair time).
    # 1 means the healpix met the requirements (0 means did not).
    dTmin = 40.0 / 60.0  # (minutes) 40s minumum for rapid revisit range
    dTpairs = 20.0  # minutes (time when pairs should start kicking in)
    dTmax = 30.0  # 30 minute maximum for rapid revisit range
    nOne = 82  # Number of revisits between 40s-30m required
    nTwo = 28  # Number of revisits between 40s - tPairs required.
    pixArea = float(hp.nside2pixarea(nside, degrees=True))
    scale = pixArea * hp.nside2npix(nside)
    m1 = metrics.RapidRevisitMetric(
        metricName="RapidRevisits",
        mjdCol=colmap["mjd"],
        dTmin=dTmin / 60.0 / 60.0 / 24.0,
        dTpairs=dTpairs / 60.0 / 24.0,
        dTmax=dTmax / 60.0 / 24.0,
        minN1=nOne,
        minN2=nTwo,
    )
    plotDict = {"xMin": 0, "xMax": 1, "colorMin": 0, "colorMax": 1, "logScale": False}
    cutoff1 = 0.9
    summaryStats = [
        metrics.FracAboveMetric(cutoff=cutoff1, scale=scale, metricName="Area (sq deg)")
    ]
    caption = (
        "Rapid Revisit: area that receives at least %d visits between %.3f and %.1f minutes, "
        % (nOne, dTmin, dTmax)
    )
    caption += (
        "with at least %d of those visits falling between %.3f and %.1f minutes. "
        % (nTwo, dTmin, dTpairs)
    )
    caption += (
        'Summary statistic "Area" indicates the area on the sky which meets this requirement.'
        " (SRD design specification is 2000 sq deg)."
    )
    displayDict["caption"] = caption
    bundle = mb.MetricBundle(
        m1,
        slicer,
        sql,
        plotDict=plotDict,
        plotFuncs=subsetPlots,
        info_label=info_label,
        displayDict=displayDict,
        summaryMetrics=summaryStats,
    )
    bundleList.append(bundle)
    displayDict["order"] += 1

    # Set the runName for all bundles and return the bundleDict.
    for b in bundleList:
        b.setRunName(runName)
    return mb.makeBundlesDictFromList(bundleList)
