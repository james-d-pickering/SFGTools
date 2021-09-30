Using SFGTools in a Python Script
------------------------------------

For ultimate flexibility for future development, the *sfgtools.py* module defines a class ``SFGProcessTools()`` which contains all relevant classes, methods, and attributes for processing SFG data. To load the module in a script, do something like::

        import sfgtools as sfgtools
        SFGTools = sfgtools.SFGProcessTools()

Here we have imported the module and created ``SFGTools`` as an instance of the ``SFGProcessTools()`` class. 

Now we will load and process some example data to illustrate the module. The example data files and complete script can be found in REF.

First, we define our files to be processed. A publishable SFG spectrum normally consists of a **signal** spectrum that is background subtracted using a **background** spectrum. This subtracted signal spectrum is then normalised by dividing it by a **reference** spectrum, which is itself backgorund subtracted from a **reference background** spectrum. These four names are used extensively in various full and shortened forms throughout the module to denote these different kinds of data. We can load the spectra as follows::

        directory = './examples/'
        signal = ['signal_example.spe']
        background = ['background_example.spe']
        reference = ['reference_example.spe']
        reference_bg = ['reference_background_example.spe']

Note that we have defined a data directory, ``directory``, and then four appropriately named Python **lists** containing the four raw *.spe* files to be processed. The files could be used as bare strings, but loading them as a list makes it easier to batch process files later on. 

Before we can process these four files, we have to provide some more information to the program about how we want to process our data. In addition to background subtraction and normalisation, SFG spectra are almost always **downconverted**, which means that the spectrum energy axis is lowered in energy such that reflects the vibrational (or electronic, or whatever) response of the molecule. The energy is lowered by the energy of the upconversion beam used in the experiment. Furthermore, the spectra are often **calibrated** by applying a linear offset to the energy axis, to account for any poor calibration of the spectrometer. We have to to tell the program the wavelength of the upconverter, and any calibration shift, and we do this as follows::

        SFGTools.upconversion_line_num = 808
        SFGTools.calibration_offset = 15

Here we have defined the class attributes ``upconversion_line_num`` and ``calibration_offset``, in nanometres and wavenumbers respectively. See specific documentation for more information. Finally, we have to tell the program that we do want to downconvert, calibrate, background subtract, and normalise our spectrum. We also want to correct the spectra for exposure time differences (so subtracting them from each other makes sense), and we might want to remove contributions from cosmic rays (but not needed in this example)::

        SFGTools.downconvert_check = True
        SFGTools.calibrate_check = True
        SFGTools.subtract_check = True
        SFGTools.normalise_check = True
        SFGTools.exposure_check = True
        SFGTools.cosmic_kill_check = False

Setting these boolean flags will tell the program what to do (there are many other flags, see further documentation). Now we are ready to read our data files, but need to create a place to put the data. To do this we create an ``SFGDataStore`` instance::

        datastore = SFGTools.SFGDataStore()

The instance ``datastore`` of the ``SFGDataStore()`` class will hold our data, together with a large amount of associated metadata if we desire it. Understanding how this class works is central to effectively using (and developing for) this module. The data and metadata are all stored in class attributes, and core processing functions that are applied to the data (such as all of the processes mentioned above) are implemented as methods of this class. You can also create a list of datastore instances for an arbitary number of files by using the function::

        datastores = SFGTools.create_data_stores(len(signal))

Where the length of your *signal* list defines the number of datastores. Now we can load our data into the datastores as follows::

        SFGTools.read_files( directory+signal[0], datastore, 'sig')
        SFGTools.read_files( directory+background[0], datastore, 'bg')
        SFGTools.read_files( directory+reference[0], datastore, 'ref')
        SFGTools.read_files( directory+reference_bg[0], datastore, 'refbg')

The function ``read_files()`` takes the path to the datafile as the first argument, then the ``SFGDataStore`` instance to store the data in, and finally a string that determines whether the loaded file is marked as a signal (*'sig'*), background (*'bg'*), reference (*'ref'*), or reference background (*'refbg'*) file. This ensures that the data is put in the right place for further processing. If you have a list of datastores, or simply want to avoid writing this out, you can also call the function::

        SFGTools.populate_data_stores(datastores, directory, signal, background, reference, reference_bg)

See further documentation for more information. Note that some parameters such as the exposure time and spectrum dimensions are automatically extracted from the *.spe* file, but others can either be added manually, or by using other functions provided in the module. If we wanted to look at our imported data, we can simply look at some of the attributes of datastore - perhaps we want to look at the raw signal data, then type into the Python shell::

        datastore.signal_raw

And you should see a **numpy array** object outputted. All the data are stored as numpy arrays, with a shape of *(frameheight, framewidth)*, where frameheight and framewidth refer to the height and width of the data read from the *.spe* file. In general, this array will then have a shape of *(1, n)* where *n* is the width of the spectrum. The additional dimension is preserved such that reading without binning the CCD chip is possible. Similarly, we can look at the energy axis::

        datastore.xaxis

This is also a numpy array, but is now one dimensional, as the energy axis will never have two dimensions. All attributes of the datastore can be printed to the shell using the ``print_attributes()`` method. Anyway, let us now proceed with processing our data, which we can do as follows::

        SFGTools.process_data(datastore, SFGTools.downconvert_check, SFGTools.subtract_check, 
                              SFGTools.normalise_check, SFGTools.exposure_check, 
                              SFGTools.calibrate_check, SFGTools.cosmic_kill_check )
        
The ``process_data`` method takes the populated datastore and all our flags as arguments. Under the bonnet, this is calling the appropriate methods of the ``SFGDataStore`` class (see further documentation). If you have multiple datastores in a list, you can batch process as follows::

        SFGTools.batch_process(datastores)  

This doesn't take all the flag arguments and inherits them from the class. The reason for this is that sometimes it is desirable to process the same data with or without certain kinds of processing, and the ``process_data()`` method makes this easier. The ``batch_process()`` method is mainly intended for use with the GUI frontend for this module.

Now we have the data processed, we can use our preferred plotting program to look at it, I like matplotlib, so something like::

        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(datastore.xaxis, datastore.signal_normalised[0])

Will show us the data. You can also apply whatever processing you want to do to the data (fitting etc..) to the processed data. Alternatively, if we have already imported matplotlib, we can use plot our data using functions in the module. These are again mostly intended for use with the GUI, so have some additional arguments which need not worry us here::

        SFGTools.custom_region_start = 2800
        SFGTools.custom_region_end = 3100
        SFGTools.plot_data(datastore, iteration=1, num_files=1, figure=plt.figure() ) 

Here we have defined two new class attributes which plot the interesting range of our data. The *iteration* and *num_files* variables are used to control plotting in the GUI. 

There you go! You have processed and plotted some SFG data using the ``sfgtools`` module! Please explore the rest of the documentation to see what other methods are available (there are many), and do not be shy about hacking apart the code and bending it to your will. 

