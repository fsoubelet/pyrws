"""
.. _constants:

Useful Constants
----------------

Specific constants to be used in the package, to help with consistency.
"""
from typing import List

from pyhdtoolkit.cpymadtools.constants import MONITOR_TWISS_COLUMNS

VARIED_IR_QUADRUPOLES: List[int] = list(range(4, 11))

EXPORT_TWISS_COLUMNS: List[str] = [colname.upper() for colname in MONITOR_TWISS_COLUMNS]
EXPORT_TWISS_COLUMNS.remove("DBX")
EXPORT_TWISS_COLUMNS.remove("DBY")
EXPORT_TWISS_COLUMNS += ["BBX", "BBY"]  # beta-beat columns
