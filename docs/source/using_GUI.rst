Using SFGTools with a GUI
=================================

Also provided with the **SFGTools** module is a graphical user interface to make doing the most common data processing simple and efficient. The GUI can be run (if you have Python and the right packages installed) from the a UNIX shell or Windows Powershell, after navigating to the directory containing *SFGToolsGUI.py* simply by running the file with your Python interpreter::

        python SFGToolsGUI.py

You should now see a GUI window open on your screen. If you don't, it is probably due to you not having Python or the relevant dependencies installed - a standalone *.exe* version of the GUI is coming very soon. The SFGTools GUI works simply by implementing the functions defined in the *sfgtools.py* module but takes user input of the files and processing flags from the GUI window. Lets take a tour of the GUI panel.

Examining panels clockwise from the top left, we have: 
* **Data Input** - this panel contains two tabs that give two options for data input. A 'smart' reader (efficient if your filenaming is consistent and as the program expects - see later), and a 'manual' reader (a bit more labour intensive).
* **Data Processing** - this panel is where options related to the data processing can be selected, currently it holds checkboxes that relate to all the bool flags that determine how the data is processed. 
* **File Manager** - this panel contains two tables that will show the loaded data files (top table is for signal data, bottom is for reference data).
* **Program Options** - this panel contains options that relate to the running of the GUI. 
* **Output** - this panel contains settings that determine how and where the program outputs processed data.
* **Experimental Parameters** - this panel contains parameters that are specific to the experiment but affect the data processing.

Use of the GUI once you have loaded the data files is pretty straightforward, just click the checkboxes you want and hit "Go!" to process and plot/write the data. The slightly complex part comes in understanding the file input methods. Using the example files in */examples/GUI/* we can illustrate this. 

There are two ways that data files can be loaded into the SFGToolsGUI - **smart**, and **manual**. The **smart** method works best if your data conform to a (somewhat flexible) naming format, and is helpful if you need to process large amounts of data at once. The **manual** method is slightly more labour intensive. Recall that the processing in *SFGTools* is centered around defining **signal**, **background**, **reference**, and **reference background** data files, which are then loaded into a datastore and processed. 

Using the Smart File Reader
----------------------------

The first thing to do when using either file reader is to select the **data directory** that you want to read the files from. As of the current version, all the files to be read must be in the same folder (otherwise use the module in a Python script to get more flexibility). This is done either using the *select directory* button on the Data Input panel, or the *Browse...* button on the File Manager panel. Both point to the same slot in the underlying program, and will open a file dialog that allows you navigate and select a folder. Select the */examples/GUI/* folder now. 

If it was not already so, the *Data Directory* field in File Manager should now be filled in with the correct directory. Now, we have to provide three strings to the smart data reader so that it can get our data:
* **Sample String** - this string must be at the start of your filename, and is what identifies it as the correct type of data file to plot (for example - you may have recorded several different samples on one day, but only want to plot one at a time). 
* **Reference String** - this string must be at the start of the filename of any reference files, and identifies them as a reference. 
* **Bg String** - this string is what identifies a file as a background file, and can be present anywhere in the filename. 

Some of these fields may already be filled in depending on the settings when the GUI was last run on your system. Set the sample string to 'sample', the reference to 'reference', and the background to '_bg'. When the fields are filled in and the *Get Data* button is pressed, then the program will look in the specified directory and find the relevant files. Try this now. You should see files that have been loaded in the File Manager panel - four in total. 

It is perhaps useful to illustrate how this method would work with a more complex filename. Imagine that we have the following six files::

        LkA_SSP_3000nm_1.spe
        LkA_SSP_3000nm_2.spe
        LkA_SSP_3000nm_3.spe
        LkA_SSP_3000nm_bg.spe
        Au_PPP_1.spe
        Au_PPP_bg.spe

In our fictional experiment, our sample is 'LkA', and our reference is 'Au' (classic SFG). The smart file reader would identify the top three files as signal files, the fourth file as a background to the signal files, the fifth file as a reference file, and the sixth file as a background to the reference file. The reader is quite capable, but please try and break it so it can be improved! 

Now our files are loaded, but we need to **sort** the files before they can be processed. For the example case, this is not strictly necessary, but if we have multiple signal files that share a background or reference, or multiple references, then this is important. Clicking the *Auto Sort* button in File Manager will attempt to match each signal file with it's correct background and reference files (see module documentation for more explanation). Of course, if it doesn't do this correctly (or you have some inconsistent naming), you can manually edit the generated data tables and it will update the data to be processed. 

Having got and sorted the data, you can now ensure that the *Plot Data* checkbox is ticked and plot the data. 

Using the Manual File Reader
-----------------------------
The manual file reader is simpler to understand but more clunky to use. Changing the tab from *smart* to *manual* you will see that there are now four buttons labelled with the four filetypes we need for our data processing. Again, the first thing to do is to ensure the correct directory is selected. 

Once that is done, clicking each of the four buttons will bring up a file dialog where data files can be selected. The files you select in the dialog that arises from the *Signal Files* button will be stored as signal files, and so on. Once you have done this for all four buttons you will see that the tables are populated - then you can either sort out the backgrounds/references manually, or you can use the Auto Sort function again. 

Try to use the Manual file reader now with the files in the */examples/GUI/* folder. You should find it gives the same result as the smart reader.

A note on references
.....................
You will note that the reference and signal tables are separate, and that references are created with a number (the **refID**) next to them. Most of the time in SFG, there are many more signal files than reference files, so you may only have two or three reference files loaded that provide the references for tens of different signal files. You can see which reference files are associated with each reference after sorting by comparing the numbers in the final column of each table - it is fairly self explanatory. 

Don't trust my sorting function?
...................................
Sensible skepticism. Before processing, but after the files are loaded and sorted, you can press the *Check Files* button, and this will print a table of files to the shell. The four columns of this table are::

        [signal_files, background_files, reference_files, reference_bg_files]

Each row represents a different signal file, and the files in the same row are all stored in the same ``SFGDataStore`` instance, and thus are processed together - i.e. the background file in the same row as the signal file is the background for that signal, and so on. In this way you can check what processing is actually going to happen before you hit *Go* and potentially generate hundreds of meaningless spectra. Again, note that if the sorting function does not work for you, you can manually edit the table. But let me know if you find bugs. 

Processing Options
-------------------
Once the files are loaded, I think it is quite self explanatory how the processing checkboxes work. Simply select or deselect the ones you want. Note that if you have a spectrum you want to plot without a background/reference, then just deselect these and the program will not get angry about there not being a loaded background/reference. If it expects there to be a file and one is not provided, you only have yourself to blame for the crash to desktop. 

You also need to input the upconversion wavelength in the appropriate box - in **nanometres**. The calibration offset must be provided in **wavenumbers**.

The cosmic ray remover is a function implemented by Steven and I, but has not been thoroughly tested and is not the most robust thing. Try it if needed and see - but future versions will have more functionality in this area. In the same vein, a polynomial calibration will be coming soon. 

Data Output
--------------
In terms of data output, the options are to plot the data using matplotlib, write it to a *.txt* file, or both. If the data are plotted, there are some limited options:
* **Stack Plots** - will overlay the data from all loaded signal files on a single figure. 
* **Close Plots** - will close any open plots the next time *Go!* is pressed.
* **Region of Interest** - these two textboxes define the start and end of the region to be plotted, in **wavenumbers**. Often you want to ignore all the noise at the edges due to normalisation, and this does that. 

If the data are written to a *.txt* file, they are written to the directory specified in the *Write Directory* box, which can be selected using the *Browse* button next to it. The data are written to a file with the same name as the signal file, but with an appended string showing they have been processed. The files written are relatively chunky, as there is a header that records a large amount of the processing options that were used (for future reference), and also many parts of the raw data are written out, not just the final processed output - this is for possible future reference. The first two columns of this file contain the final processed spectral data (xaxis, yaxis). 

Miscellaneous Notes
-------------------
* The current version of this GUI is only going to give reliable results when processing **one dimensional** spectral data. Use the module in a Python script for more complex cases.
* There are some program options to do with verbosity that can be selected - this just changes what is printed to terminal during processing. 
* After each run, the program will store the last used parameters internally and save them on closing, so that when the program is reinitialised on your machine, your previous settings will be reloaded. The *Restore Defaults* button clears this memory, so an empty GUI will be loaded on the next startup. 



