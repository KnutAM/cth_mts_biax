Introduction
************
This package provides some convenient routines for working with raw data produced by the
MTS Tension-Torsion machine located in the Materials Lab in the Engineering Materials division
at Chalmers. Compensation parameters are hard-coded for this machine, and were reported in
Meyer et al. (2018) [https://doi.org/10.1016/j.ijsolstr.2017.10.007]

..
    Machine
    =====================
    |machine|

    .. |machine| image:: /img/example.svg
             :align: middle
             :alt: Could not include example.svg
..

Installation
============

Prerequisites
-------------
* ``python`` installed with ``conda`` (``anaconda``) and be able to run ``conda`` and ``python`` from your shell.
* ``conda activate`` should work from your shell


Installation
------------
1. Download repository using ``git``: ``git clone git@github.com:KnutAM/cth_mts_biax.git``
2. In your shell, change directory to the ``cth_mts_biax`` folder and run
   * ``conda activate base`` (Advanced: Use your own custom environment instead of ``base``)
   * ``conda install sphinx_rtd_theme``
   * ``pip install .``

Tutorial
========
In this tutorial, we will use the example python scripts in the ``examples`` folder. 
It is advisable to copy the content of this folder to another location on your computer.


Using a shell
-------------

In shell (``bash``, ``cmd``, ``powershell``, etc.), run the following commands 

* ``conda activate base`` (or another environment if you have installed to that)
* ``python <example_file>``

where ``<example_file>`` can be ``raw_data_ex.py``, ``read_variables_ex.py``, or ``xml_to_hdf5_ex.py``.

Using PyCharm
-------------
Open the copied ``examples`` folder in PyCharm. 
See `PyCharm's manual <https://www.jetbrains.com/help/pycharm/conda-support-creating-conda-virtual-environment.html>`_ 
for information how to activate the conda environment for your file/project. 
After activating the project, you can run the example files, 
``raw_data_ex.py``, ``read_variables_ex.py``, or ``xml_to_hdf5_ex.py``, 
inside PyCharm


