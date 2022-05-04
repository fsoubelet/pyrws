# PyRWS

[![GitHub last commit](https://img.shields.io/github/last-commit/fsoubelet/pyrws.svg?style=popout)](https://github.com/fsoubelet/pyrws/)
[![PyPI Version](https://img.shields.io/pypi/v/pyrws?label=PyPI&logo=pypi)](https://pypi.org/project/pyrws/)
[![GitHub release](https://img.shields.io/github/v/release/fsoubelet/pyrws?logo=github)](https://github.com/fsoubelet/pyrws/)
<!-- [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.5070986.svg)](https://doi.org/10.5281/zenodo.5070986) -->

This is a `Python 3.8+` package that provides functionality to create Rigid Waist Shift Knobs to be used for for IR local coupling correction in the LHC commissioning 2022.
A bit more information can be found on the OMC website's page for [the procedure](https://pylhc.github.io/measurements/procedures/rigid_waist_shift/).

See the [API documentation](https://fsoubelet.github.io/pyrws/) for details.

## Installing

Installation is easily done via `pip`:
```bash
python -m pip install pyrws
```

## Example Usage

 The package is meant to be used at the command line.
```bash
python -m pyrws \
  --sequence acc-models-lhc/lhc.seq \
  --opticsfile acc-models-lhc/operation/optics/R2022a_A30cmC30cmA10mL200cm.madx \
  --ip 1 \
  --waist_shift_setting 1 \
  --outputdir 30cm \
  --energy 6800 \
  --show_plots no \
```

Individual parts of the package can be imported to be used in a Python program, or as utilities to load and inspect the outputs of some knob generation.
For details, see the API documentation website.

## License

This project is licensed under the `MIT License` - see the [LICENSE](LICENSE) file for details.