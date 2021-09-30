SFGTools : Processing and Analysing SFG Spectroscopy Data
===============================================================================

Overview
----------

**SFGTools** is a Python module designed to facilitate easy processing and analysis of Sum Frequency Generation (SFG) spectroscopy datasets. 

In its current form, it consists of a module containing functions and methods for working with SFG data in a Python script/interpreter, ``sfgtools.py``. Using SFGTools in this way (importing into Python and using in a script) is the most flexible way to use it, and provides the most extended functionality for complex use cases. However, packaged with this module is a graphical frontend made using Qt Designer, ``SFGTools_ui.ui``, which is converted to a Python file, ``SFGTools_ui.py``. This frontend is interfaced with ``sfgtools.py`` via the ``SFGToolsGUI.py`` file, and provides a user-friendly GUI where SFG data can be quickly and easily processed and plotted (as would be useful in a working lab), but without all of the extended functionality of the bare module. 

Scope
______
Currently, ``sfgtools`` can be used to process SFG spectra recorded in the *.spe* filetype, which is common in high-sensitivity CCD cameras for spectroscopy. Support is provided for *.spe* version 2.x and 3.0 (commonly produced by Andor and Princeton Instruments cameras respectively). The graphical frontend and plotting capability is currently designed around plotting one-dimensional SFG spectra (where the data on the CCD is binned into one row), but the underlying software supports a wider range of data shapes and formats - they just may not plot correctly when using the GUI. Use of the module in a Python script is advised for this purpose. 

As far as possible, the module has been written to be easily extended, and is well documented. Thus, other data types, data formats, and processing functions can be easily integrated. See REF LATER. 
