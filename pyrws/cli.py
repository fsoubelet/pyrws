"""
.. _cli:

Main command line script.
"""
from pathlib import Path
from typing import Optional, Tuple

import click
import matplotlib
import tfs

from cpymad.madx import Madx
from loguru import logger
from matplotlib import pyplot as plt

from pyhdtoolkit.utils._misc import fullpath
from pyhdtoolkit.utils.defaults import config_logger
from pyrws.core import (
    get_bare_waist_shift_beam1_config,
    get_bare_waist_shift_beam2_config,
    get_matched_waist_shift_config,
    get_nominal_beam_config,
)
from pyrws.plotting import (
    plot_betas_comparison,
    plot_betas_deviation,
    plot_phase_advances_comparison,
    plot_phase_differences,
    plot_waist_shift_betabeatings,
    plot_waist_shift_betabeatings_comparison,
)
from pyrws.utils import (
    add_betabeating_columns,
    only_export_columns,
    only_monitors,
    prepare_output_directories,
    write_knob_delta,
    write_knob_powering,
)


@click.command(context_settings=dict(max_content_width=105))
# ----- Required Arguments ----- #
@click.option(
    "--sequence",
    type=click.Path(exists=True, file_okay=True, resolve_path=True, path_type=Path),
    required=True,
    help="Path to the LHC sequence file to use.",
)
@click.option(
    "--opticsfile",
    type=click.Path(exists=True, file_okay=True, resolve_path=True, path_type=Path),
    required=True,
    help="Path to the LHC optics file to use.",
)
@click.option(
    "--ip",
    type=click.IntRange(min=0, max=8),
    default=1,
    show_default=True,
    required=True,
    help="Which IP to prepare the waist shift knob for. Should be 1 or 5.",
)
@click.option(
    "--waist_shift_setting",
    type=click.FloatRange(min=0),
    required=True,
    help="Unit setting of the rigid waist shift." "A value of 1 corresponds to a 0.5% change in the triplets powering.",
)
@click.option(
    "--outputdir",
    type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=Path),
    default=Path.cwd() / "outputs",
    show_default=True,
    help="Directory in which to write output files. Defaults to 'outputs/' in the current working directory.",
)
# ----- Optional Arguments ----- #
@click.option(
    "--qx",
    type=click.FloatRange(min=0),
    default=62.31,
    show_default=True,
    help="The horizontal tune to match to.",
)
@click.option(
    "--qy",
    type=click.FloatRange(min=0),
    default=60.32,
    show_default=True,
    help="The vertical tune to match to.",
)
@click.option(
    "--show_plots",
    type=click.BOOL,
    default=False,
    show_default=True,
    help="Whether to ask matplotlib to show plots.",
)
@click.option(
    "--mplstyle",
    type=click.STRING,
    help="Name of a matplotlib style to use for plots.",
)
@click.option(
    "--figsize",
    nargs=2,
    type=click.Tuple([int, int]),
    help="Figure size for the created plots. "
    "Will affect the visibility of the plots. "
    "Defaults to the standard matplotlib rcParams value.",
)
@click.option(
    "--loglevel",
    type=click.Choice(["trace", "debug", "info", "warning", "error", "critical"]),
    default="info",
    show_default=True,
    help="Sets the logging level.",
)
def create_knobs(
    sequence: Path,
    opticsfile: Path,
    ip: int,
    waist_shift_setting: float,
    outputdir: Path,
    qx: Optional[float],
    qy: Optional[float],
    show_plots: Optional[bool],
    mplstyle: Optional[str],
    figsize: Optional[Tuple[int, int]],
    loglevel: Optional[str],
):
    # ----- Configuration ----- #
    config_logger(level=loglevel)
    (
        b1_dir,
        b1_tfs_dir,
        b1_knobs_dir,
        b1_plots_dir,
        b2_dir,
        b2_tfs_dir,
        b2_knobs_dir,
        b2_plots_dir,
    ) = prepare_output_directories(outputdir)
    if mplstyle:
        plt.style.use(mplstyle)

    # ----- Beam 1 Nominal ----- #
    logger.info("Preparing beam 1 nominal configuration")
    nominal_b1_in = b1_dir / "nominal_b1.madx"
    nominal_b1_out = b1_dir / "nominal_b1.out"
    with nominal_b1_in.open("w") as commands, nominal_b1_out.open("w") as outputs:
        with Madx(command_log=commands, stdout=outputs) as madxb1:
            madxb1.option(echo=False, warn=False)
            madxb1.call(fullpath(sequence))
            madxb1.call(fullpath(opticsfile))

            nominal_twiss_b1, nominal_triplets_b1, nominal_quads_b1, nominal_wp_b1 = get_nominal_beam_config(
                madxb1, beam=1, ip=ip, qx=qx, qy=qy
            )

    # ----- Beam 1 Waist Shift ----- #
    logger.info("Preparing beam 1 waist shift configuration")
    waist_b1_in = b1_dir / "waist_b1.madx"
    waist_b1_out = b1_dir / "waist_b1.out"
    with waist_b1_in.open("w") as commands, waist_b1_out.open("w") as outputs:
        with Madx(command_log=commands, stdout=outputs) as madxb1:
            madxb1.option(echo=False, warn=False)
            madxb1.call(fullpath(sequence))
            madxb1.call(fullpath(opticsfile))

            bare_twiss_b1, bare_triplets_b1, bare_quads_b1, bare_wp_b1 = get_bare_waist_shift_beam1_config(
                madxb1, ip=ip, rigidty_waist_shift_value=waist_shift_setting, qx=qx, qy=qy
            )
            bare_twiss_b1 = add_betabeating_columns(bare_twiss_b1, nominal_twiss_b1)

            logger.info("Refining beam 1 waist shift - this may take a while...")
            matched_twiss_b1, matched_triplets_b1, matched_quads_b1, matched_wp_b1 = get_matched_waist_shift_config(
                madxb1, beam=1, ip=ip, nominal_twiss=nominal_twiss_b1, bare_twiss=bare_twiss_b1, qx=qx, qy=qy
            )
            matched_twiss_b1 = add_betabeating_columns(matched_twiss_b1, nominal_twiss_b1)

    # ----- Beam 1 Output Files ----- #
    logger.info("Writing out TFS files for beam 1")
    tfs.write(b1_tfs_dir / "nominal_b1.tfs", only_export_columns(nominal_twiss_b1))
    tfs.write(b1_tfs_dir / "nominal_b1_monitors.tfs", only_monitors(only_export_columns(nominal_twiss_b1)))
    tfs.write(b1_tfs_dir / "bare_waist_b1.tfs", only_export_columns(bare_twiss_b1))
    tfs.write(b1_tfs_dir / "bare_waist_b1_monitors.tfs", only_monitors(only_export_columns(bare_twiss_b1)))
    tfs.write(b1_tfs_dir / "matched_waist_b1.tfs", only_export_columns(matched_twiss_b1))
    tfs.write(b1_tfs_dir / "matched_waist_b1_monitors.tfs", only_monitors(only_export_columns(matched_twiss_b1)))

    # ----- Write B1 Knobs ----- #
    logger.info("Writing B1 knob powerings and deltas to disk")
    write_knob_powering(b1_knobs_dir / "triplets.madx", matched_triplets_b1)
    write_knob_powering(b1_knobs_dir / "quadrupoles.madx", matched_quads_b1)
    write_knob_powering(b1_knobs_dir / "working_point.madx", matched_wp_b1)
    write_knob_delta(b1_knobs_dir / "triplets_change.madx", nominal_triplets_b1, matched_triplets_b1)
    write_knob_delta(b1_knobs_dir / "quadrupoles_change.madx", nominal_quads_b1, matched_quads_b1)
    write_knob_delta(b1_knobs_dir / "working_point_change.madx", nominal_wp_b1, matched_wp_b1)

    # ----- Beam 2 Nominal ----- #
    logger.info("Preparing beam 2 nominal configuration")
    nominal_b2_in = b2_dir / "nominal_b2.madx"
    nominal_b2_out = b2_dir / "nominal_b2.out"
    with nominal_b2_in.open("w") as commands, nominal_b2_out.open("w") as outputs:
        with Madx(command_log=commands, stdout=outputs) as madxb2:
            madxb2.option(echo=False, warn=False)
            madxb2.call(fullpath(sequence))
            madxb2.call(fullpath(opticsfile))

            nominal_twiss_b2, nominal_triplets_b2, nominal_quads_b2, nominal_wp_b2 = get_nominal_beam_config(
                madxb2, beam=2, ip=ip, qx=qx, qy=qy
            )

    # ----- Beam 2 Waist Shift ----- #
    logger.info("Preparing beam 1 waist shift configuration")
    waist_b2_in = b2_dir / "waist_b2.madx"
    waist_b2_out = b2_dir / "waist_b2.out"
    with waist_b2_in.open("w") as commands, waist_b2_out.open("w") as outputs:
        with Madx(command_log=commands, stdout=outputs) as madxb2:
            madxb2.option(echo=False, warn=False)
            madxb2.call(fullpath(sequence))
            madxb2.call(fullpath(opticsfile))

            bare_twiss_b2, bare_triplets_b2, bare_quads_b2, bare_wp_b2 = get_bare_waist_shift_beam2_config(
                madxb2, ip=ip, triplet_knobs=matched_triplets_b1, qx=qx, qy=qy
            )
            bare_twiss_b2 = add_betabeating_columns(bare_twiss_b2, nominal_twiss_b2)

            logger.info("Refining beam 2 waist shift - this may take a while...")
            matched_twiss_b2, matched_triplets_b2, matched_quads_b2, matched_wp_b2 = get_matched_waist_shift_config(
                madxb2, beam=2, ip=ip, nominal_twiss=nominal_twiss_b2, bare_twiss=bare_twiss_b2, qx=qx, qy=qy
            )
            matched_twiss_b2 = add_betabeating_columns(matched_twiss_b2, nominal_twiss_b2)

    # ----- Quick Sanity check ----- #
    assert matched_triplets_b1 == matched_triplets_b2, "Triplet knobs are different for B1 and B2!"

    # ----- Beam 2 Output Files ----- #
    logger.info("Writing out TFS files for beam 2")
    tfs.write(b2_tfs_dir / "nominal_b2.tfs", only_export_columns(nominal_twiss_b2))
    tfs.write(b2_tfs_dir / "nominal_b2_monitors.tfs", only_monitors(only_export_columns(nominal_twiss_b2)))
    tfs.write(b2_tfs_dir / "bare_waist_b2.tfs", only_export_columns(bare_twiss_b2))
    tfs.write(b2_tfs_dir / "bare_waist_b2_monitors.tfs", only_monitors(only_export_columns(bare_twiss_b2)))
    tfs.write(b2_tfs_dir / "matched_waist_b2.tfs", only_export_columns(matched_twiss_b2))
    tfs.write(b2_tfs_dir / "matched_waist_b2_monitors.tfs", only_monitors(only_export_columns(matched_twiss_b2)))

    # ----- Write B2 Knobs ----- #
    logger.info("Writing B2 knob powerings and deltas to disk")
    write_knob_powering(b2_knobs_dir / "triplets.madx", matched_triplets_b2)
    write_knob_powering(b2_knobs_dir / "quadrupoles.madx", matched_quads_b2)
    write_knob_powering(b2_knobs_dir / "working_point.madx", matched_wp_b2)
    write_knob_delta(b2_knobs_dir / "triplets_change.madx", nominal_triplets_b2, matched_triplets_b2)
    write_knob_delta(b2_knobs_dir / "quadrupoles_change.madx", nominal_quads_b2, matched_quads_b2)
    write_knob_delta(b2_knobs_dir / "working_point_change.madx", nominal_wp_b2, matched_wp_b2)

    # ----- Generate Plots ----- #
    b1_figures = _generate_beam1_figures(
        plots_dir=b1_plots_dir,
        nominal_b1=nominal_twiss_b1,
        bare_b1=bare_twiss_b1,
        matched_b1=matched_twiss_b1,
        # kwargs
        figsize=figsize,
    )
    b2_figures = _generate_beam2_figures(
        plots_dir=b2_plots_dir,
        nominal_b2=nominal_twiss_b2,
        bare_b2=bare_twiss_b2,
        matched_b2=matched_twiss_b2,
        # kwargs
        figsize=figsize,
    )

    # ----- Eventually Display Plots ----- #
    if show_plots:
        logger.info("Asking matplotlib to show plots")
        plt.show()


# ----- Helper Functions ----- #


def _generate_beam1_figures(
    plots_dir: Path, nominal_b1: tfs.TfsDataFrame, bare_b1: tfs.TfsDataFrame, matched_b1: tfs.TfsDataFrame, **kwargs
) -> Tuple[matplotlib.figure.Figure, ...]:
    """
    Helper to generate figures for beam 1 from the different result `~tfs.TfsDataFrame`
    and take boilerplate away from the main function.

    Args:
        plots_dir (Path): `~pathlib.Path` to the directory to save the B1 figures in.
        nominal_b1 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the nominal B1 results.
        bare_b1 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the bare waist B1 results.
        matched_b1 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the matched waist B1 results.
        **kwargs: any keyword argument is passed to `~matplotlib.pyplot.subplots`.

    Returns:
        A tuple of all the generated figures.
    """
    logger.info("Generating plots for beam 1")
    fig_b1_bbing_before, axis = plt.subplots(**kwargs)
    plot_waist_shift_betabeatings(axis, bare_b1, show_ips=True)
    axis.set_title("B1 - Waist Shift Induced Beta-Beating")
    fig_b1_bbing_before.savefig(plots_dir / "waist_shift_betabeatings.pdf")

    fig_b1_bbing_after, axis = plt.subplots(**kwargs)
    plot_waist_shift_betabeatings(axis, matched_b1, show_ips=True)
    axis.set_title("B1 - Waist Shift Induced Beta-Beating, After Matching")
    fig_b1_bbing_after.savefig(plots_dir / "matched_waist_shift_betabeatings.pdf")

    fig_b1_before_vs_after_bbing, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_waist_shift_betabeatings_comparison(axx, bare_b1, matched_b1, column="BBX", show_ips=True)
    plot_waist_shift_betabeatings_comparison(axy, bare_b1, matched_b1, column="BBY", show_ips=True)
    axx.set_title("B1 - Horizontal Waist Shift Induced Beta-Beating - Before vs After Matching")
    axy.set_xlabel("S [m]")
    fig_b1_before_vs_after_bbing.savefig(plots_dir / "bare_vs_matched_betabeatings.pdf")

    fig_b1_betas, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_betas_comparison(axx, nominal_b1, bare_b1, matched_b1, column="BETX", show_ips=True)
    plot_betas_comparison(axy, nominal_b1, bare_b1, matched_b1, column="BETY", show_ips=True)
    axx.set_title("B1 - Beta Functions for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b1_betas.savefig(plots_dir / "betas.pdf")

    fig_b1_betas_deviations, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_betas_deviation(axx, nominal_b1, bare_b1, matched_b1, column="BETX", show_ips=True)
    plot_betas_deviation(axy, nominal_b1, bare_b1, matched_b1, column="BETY", show_ips=True)
    axx.set_title("B1 - Variation to Nominal Beta-Functions - Before vs After Matching")
    axy.set_xlabel("S [m]")
    fig_b1_betas_deviations.savefig(plots_dir / "betas_deviations.pdf")

    fig_b1_phase_advances, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_phase_advances_comparison(axx, nominal_b1, bare_b1, matched_b1, column="MUX", show_ips=True)
    plot_phase_advances_comparison(axy, nominal_b1, bare_b1, matched_b1, column="MUY", show_ips=True)
    axx.set_title("B1 - Phase Advances for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b1_phase_advances.savefig(plots_dir / "phase_advances.pdf")

    fig_b1_phase_differences, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_phase_differences(axx, nominal_b1, bare_b1, matched_b1, show_ips=True)
    plot_phase_differences(axy, nominal_b1, bare_b1, matched_b1, show_ips=True)
    axx.set_title("B1 - Phase Differences for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b1_phase_differences.savefig(plots_dir / "phase_differences.pdf")

    return (
        fig_b1_bbing_before,
        fig_b1_bbing_after,
        fig_b1_before_vs_after_bbing,
        fig_b1_betas,
        fig_b1_betas_deviations,
        fig_b1_phase_advances,
        fig_b1_phase_differences,
    )


def _generate_beam2_figures(
    plots_dir: Path, nominal_b2: tfs.TfsDataFrame, bare_b2: tfs.TfsDataFrame, matched_b2: tfs.TfsDataFrame, **kwargs
) -> Tuple[matplotlib.figure.Figure, ...]:
    """
    Helper to generate figures for beam 2 from the different result `~tfs.TfsDataFrame`
    and take boilerplate away from the main function. The figures are saved to disk before
    being returned to the caller.

    Args:
        plots_dir (Path): `~pathlib.Path` to the directory to save the B2 figures in.
        nominal_b2 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the nominal B2 results.
        bare_b2 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the bare waist B2 results.
        matched_b2 (tfs.TfsDataFrame): `~tfs.TfsDataFrame` of the matched waist B2 results.
        **kwargs: any keyword argument is passed to `~matplotlib.pyplot.subplots`.

    Returns:
        A tuple of all the generated figures.
    """
    logger.info("Generating plots for beam 2")
    fig_b2_bbing_before, axis = plt.subplots(**kwargs)
    plot_waist_shift_betabeatings(axis, bare_b2, show_ips=True)
    axis.set_title("B2 - Waist Shift Induced Beta-Beating")
    fig_b2_bbing_before.savefig(plots_dir / "waist_shift_betabeatings.pdf")

    fig_b2_bbing_after, axis = plt.subplots(**kwargs)
    plot_waist_shift_betabeatings(axis, matched_b2, show_ips=True)
    axis.set_title("B2 - Waist Shift Induced Beta-Beating, After Matching")
    fig_b2_bbing_after.savefig(plots_dir / "matched_waist_shift_betabeatings.pdf")

    fig_b2_before_vs_after_bbing, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_waist_shift_betabeatings_comparison(axx, bare_b2, matched_b2, column="BBX", show_ips=True)
    plot_waist_shift_betabeatings_comparison(axy, bare_b2, matched_b2, column="BBY", show_ips=True)
    axx.set_title("B2 - Horizontal Waist Shift Induced Beta-Beating - Before vs After Matching")
    axy.set_xlabel("S [m]")
    fig_b2_before_vs_after_bbing.savefig(plots_dir / "bare_vs_matched_betabeatings.pdf")

    fig_b2_betas, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_betas_comparison(axx, nominal_b2, bare_b2, matched_b2, column="BETX", show_ips=True)
    plot_betas_comparison(axy, nominal_b2, bare_b2, matched_b2, column="BETY", show_ips=True)
    axx.set_title("B2 - Beta Functions for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b2_betas.savefig(plots_dir / "betas.pdf")

    fig_b2_betas_deviations, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_betas_deviation(axx, nominal_b2, bare_b2, matched_b2, column="BETX", show_ips=True)
    plot_betas_deviation(axy, nominal_b2, bare_b2, matched_b2, column="BETY", show_ips=True)
    axx.set_title("B2 - Variation to Nominal Beta-Functions - Before vs After Matching")
    axy.set_xlabel("S [m]")
    fig_b2_betas_deviations.savefig(plots_dir / "betas_deviations.pdf")

    fig_b2_phase_advances, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_phase_advances_comparison(axx, nominal_b2, bare_b2, matched_b2, column="MUX", show_ips=True)
    plot_phase_advances_comparison(axy, nominal_b2, bare_b2, matched_b2, column="MUY", show_ips=True)
    axx.set_title("B2 - Phase Advances for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b2_phase_advances.savefig(plots_dir / "phase_advances.pdf")

    fig_b2_phase_differences, (axx, axy) = plt.subplots(2, 1, sharex=True, **kwargs)
    plot_phase_differences(axx, nominal_b2, bare_b2, matched_b2, show_ips=True)
    plot_phase_differences(axy, nominal_b2, bare_b2, matched_b2, show_ips=True)
    axx.set_title("B2 - Phase Differences for Each Configuration")
    axy.set_xlabel("S [m]")
    fig_b2_phase_differences.savefig(plots_dir / "phase_differences.pdf")

    return (
        fig_b2_bbing_before,
        fig_b2_bbing_after,
        fig_b2_before_vs_after_bbing,
        fig_b2_betas,
        fig_b2_betas_deviations,
        fig_b2_phase_advances,
        fig_b2_phase_differences,
    )
