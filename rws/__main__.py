"""
Main callable script.
"""
from pathlib import Path

import click
from pyhdtoolkit.utils.defaults import config_logger


@click.command()
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
    "--waist_shift",
    type=click.FloatRange(min=0),
    required=True,
    help="Unit setting of the rigid waist shift."
    "A value of 1 corresponds to a 0.5% change in the triplets powering.",
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
    "--loglevel",
    type=click.Choice(["trace", "debug", "info", "warning", "error", "critical"]),
    default="info",
    show_default=True,
    help="Sets the logging level.",
)
def main(sequence: Path, opticsfile: Path, ip: int, waist_shift: float, qx: float, qy: float, loglevel: str):
    config_logger(level=loglevel)


if __name__ == "__main__":
    main()
