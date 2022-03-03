.. _quickstart-top:

Quickstart
==========

.. _quickstart-install:

Installation
------------

This package requires `Python 3.8+`.
You can install it simply from ``PyPI`` in a virtual environment with:

.. prompt:: bash

    pip install pyrws

.. tip::
    Don't know what a virtual environment is or how to set it up?
    Here is a good primer on `virtual environments <https://realpython.com/python-virtual-environments-a-primer/>`_ by `RealPython`.


.. quickstart-five-minutes:

Using the CommandLine Tool
--------------------------

One can use the tool by simply calling it with the ``-m`` flag at the commandline. For instance, to display the help message and usage options:

.. prompt:: bash $

    python -m pyrws --help

To see these options, refer to the :ref:`following page <pyrws-cli>`.

.. admonition:: Example
    
    Below is an example call to the tool. It calls the program for given **sequence** and **opticsfile** inputs,
    and asks for the creation of an improved rigid waist shift knob at IP1, with a unit setting of 1.

    The outputs will be written to a newly created **waist_shift** folder, will use a **figsize** of (20, 9) for
    the created plots, and will display them in interactive `matplotlib` windows before exiting.

    The logging level is set to show all log messages with a level of ``debug`` or above.

    .. prompt:: bash $

        python -m pyrws \
          --sequence /path/to/lhc_as-built.seq \
          --opticsfile /path/to/proton/opticsfiles/opticsfile.22 \
          --ip 1 \
          --waist_shift_setting 1 \
          --outputdir waist_shift \
          --show_plots true \
          --figsize 20 9 \
          --loglevel debug

    .. dropdown:: Show the Output Folder Structure
        :animate: fade-in-slide-down
        :title: text-center

        Here is the complete structure of the output folder. For each ``LHC`` beam, a folder is created in which
        one can find:

        - a subfolder with ``MAD-X`` knobs (absolute values and change to nominal configuration),
        - a subfolder with all exported plots,
        - a subfolder with all **TFS** files,
        - the generated ``MAD-X`` scripts and their outputs.

        .. code-block:: bash
            
            waist_shift
            ├── BEAM1
            │   ├── KNOBS
            │   │   ├── quadrupoles.madx
            │   │   ├── quadrupoles_change.madx
            │   │   ├── triplets.madx
            │   │   └── triplets_change.madx
            │   ├── PLOTS
            │   │   ├── bare_vs_matched_betabeatings.pdf
            │   │   ├── betas.pdf
            │   │   ├── betas_deviations.pdf
            │   │   ├── matched_waist_shift_betabeatings.pdf
            │   │   ├── phase_advances.pdf
            │   │   ├── phase_differences.pdf
            │   │   └── waist_shift_betabeatings.pdf
            │   ├── TFS
            │   │   ├── bare_waist_b1.tfs
            │   │   ├── bare_waist_b1_monitors.tfs
            │   │   ├── matched_waist_b1.tfs
            │   │   ├── matched_waist_b1_monitors.tfs
            │   │   ├── nominal_b1.tfs
            │   │   └── nominal_b1_monitors.tfs
            │   ├── nominal_b1.madx
            │   ├── nominal_b1.out
            │   ├── waist_b1.madx
            │   └── waist_b1.out
            └── BEAM2
                ├── KNOBS
                │   ├── quadrupoles.madx
                │   ├── quadrupoles_change.madx
                │   ├── triplets.madx
                │   └── triplets_change.madx
                ├── PLOTS
                │   ├── bare_vs_matched_betabeatings.pdf
                │   ├── betas.pdf
                │   ├── betas_deviations.pdf
                │   ├── matched_waist_shift_betabeatings.pdf
                │   ├── phase_advances.pdf
                │   ├── phase_differences.pdf
                │   └── waist_shift_betabeatings.pdf
                ├── TFS
                │   ├── bare_waist_b2.tfs
                │   ├── bare_waist_b2_monitors.tfs
                │   ├── matched_waist_b2.tfs
                │   ├── matched_waist_b2_monitors.tfs
                │   ├── nominal_b2.tfs
                │   └── nominal_b2_monitors.tfs
                ├── nominal_b2.madx
                ├── nominal_b2.out
                ├── waist_b2.madx
                └── waist_b2.out

Program Worfklow
----------------

The program's workflow is reflected in the logs, and goes as follows:

1. Run the nominal scenario for beam 1, corresponding to the provided *opticsfile* and working point.
2. Apply a rigid waist shift for beam 1, for the given *ip* and with the provided *waist_shift_setting*.
3. Perform matchings on beam 1 to reduce the impact of the waist shift on the optics, and retrieve all the relevant knobs.
4. Export beam 1 data to disk.
5. Run the nominal scenario for beam 2, corresponding to the provided *opticsfile* and working point.
6. Apply the rigid waist shift for beam 2, using the triplet powering knob determined when creating the waist shift for beam 1.
7. Perform matchings on beam 2 to reduce the impact of the waist shift on the optics, and retrieve all the relevant knobs.
8. Export beam 2 data to disk.
9. Write all knobs to disk, for their absolute values as well as change to nominal scenario.
10. Create various plots from the beam 1 and beam 2 data, and write them to disk.
11. Eventually display the plots in interactive `matplotlib` windows.
12. Exit.