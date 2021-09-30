"""Tools for processing SFG Data.

Classes:
    SFGProcess Tools
"""

import numpy as np
from lxml import etree
from PyQt5 import QtWidgets
import matplotlib.pyplot as plt
import pathlib
import glob
import inspect
import warnings
warnings.filterwarnings('ignore')


class SFGProcessTools:
    """A class that contains SFG processing tools.

    This is implemented as a class so it can be easily invoked as a model for a PyQT GUI, under the MVC
    framework.

    Attributes
    ----------
    verbose : bool
        If true tells program to print verbose output,
    stupid_verbose : bool
        If true tells program to print REALLY verbose output.
    sum_accumulations : bool
        If true tells program to sum multiple frames stored in the same .spe file
    series_accumulations : bool
        If true tells program to store multiple frames from the same .spe file as different arrays (series).
    downconvert_check : bool
        If true then spectra are downconverted.
    subtract_check : bool
        If true then spectra are background subtracted.
    normalise_check : bool
        If true then spectra are normalised by a reference.
    calibrate_check : bool
        If true then spectrum energy is shifted by +calibration_offset.
    exposure_check : bool
        If true then all spectra are divided by their relevant exposure time.
    cosmic_kill_check : bool
        If true then cosmic ray spikes are attempted to be removed automatically.
    stack_plots_check : bool
        If true then plots from multiple loaded files are stacked onto one figure.
    global_force : bool
        If true then attempts to (e.g.) downconvert spectra twice are allowed.
    write_file_check : bool
        If true then a .txt file with the processed data is written.
    plot_data_check : bool
        If true then processed data is plotted using matplotlib.
    close_plots_check : bool
        If true then plots are closed between successive runs.
    data_directory : str
        Direcotry where all the files to processed are.
    write_directory : str
        Directory where output files will be written to.
    samplestring : str
        What the smart file getter looks for at the start of a filename to identify a file as relevant.
    refstring : str
        What the smart file getter looks for at the start of a filename to identify a file as a reference.
    bg_string : str
        What the smart file getter looks for to identify a file as a background file.
    upconversion_line_num : float
        Wavelength of the upconverter in nanometres.
    calibration_offset : float
        Amount to shift a spectrum energy axis in wavenumbers.
    custom_region_start : float
        Defines leftmost edge of plotted data in wavenumbers.
    custom_region_end : float
        Defines rightmost edge of plotted data in wavenumbers.
    cosmic_threshold : float
        Used by the cosmic_ray_killer method. See description for detail.
    cosmic_max_width : float
        Used by the cosmic_ray_killer method. See description for detail.
    spe_version_loc : int
        Location in bytes that the .spe file version is stored in the .spe file.
    footer_offset_loc_loc : int
        Location in bytes that the location in bytes that the offset to the XML footer is found in an
        SPE3.0 file.
    data_offset_loc_loc : int
        Location in bytes of the location in bytes to the first data in an SPE2.x file.
    framewidth_loc : int
        Location in bytes of the framewidth of an SPE2.x file.
    frameheight_loc : int
        Location in bytes of the frameheight of an SPE2.x file.
    numframes_loc : int
        Location in bytes of the number of frames stored in an SPE2.x file.
    pixeltype_loc : int
        Location in bytes of the pixel type stored in an SPE2.x file.
    acqtime_loc : int
        Location in bytes of the acquisition time in an SPE2.x file.
    signal_names : list
        Contains the filenames of the signal files to be processed.
    bg_names : list
        Contains the filenames of the background files to be processed.
    ref_names : list
        Contains the filenames of the reference files to be processed.
    ref_bg_names : list
        Contains the filenames of the reference background files to be processed.
    ref_num : list
        Contains the reFID number of each reference file.
    sig_ref_num : list
        Contains the refID number that each signal file needs to be normalised by.
    tabledata : list
        Contains data to be shown in the GUI main data table.
    reftabledata : list
        Contains data to be down in the GUI reference data table.
    current_figure : pyplot figure
        Figure data is currently being plotted on.
    """
    def __init__(self):

        # bool things
        self.verbose = True
        self.stupid_verbose = False
        self.sum_accumulations = False
        self.series_accumulations = False
        self.downconvert_check = False
        self.subtract_check = False
        self.normalise_check = False
        self.calibrate_check = False
        self.exposure_check = False
        self.cosmic_kill_check = False
        self.stack_plots_check = False
        self.global_force = False
        self.write_file_check = False
        self.plot_data_check = False
        self.close_plots_check = False
        self.auto_sort_check = False

        # strings
        self.data_directory = None
        self.write_directory = None
        self.samplestring = None
        self.refstring = None
        self.bg_string = '_bg'

        # numeric
        self.upconversion_line_num = None
        self.calibration_offset = None
        self.custom_region_start = None
        self.custom_region_end = None
        self.cosmic_threshold = 0.001
        self.cosmic_max_width = 10

        # locations for things in .spe files - check process method docstring for details
        self.spe_version_loc = 1992
        self.footer_offset_loc_loc = 678
        self.data_offset_loc_loc = 4100
        self.framewidth_loc = 42
        self.frameheight_loc = 656
        self.numframes_loc = 1446
        self.pixeltype_loc = 108
        self.acqtime_loc = 10

        # lists
        self.signal_names = []
        self.bg_names = []
        self.ref_names = []
        self.ref_bg_names = []
        self.ref_num = []
        self.sig_ref_num = []
        self.tabledata = [self.signal_names, self.bg_names, self.sig_ref_num]
        self.reftabledata = [self.ref_names, self.ref_bg_names, self.ref_num]

        # misc
        self.current_figure = None
        
    class SFGDataStore:
        """This class is where the SFG data is stored.

        An instance of the class is created for every distinct signal file - i.e. a file that is not a 
        background or reference file. The slots define different things that can be associated with the 
        signal file. Each slot has an associated attribute.

        """

        __slots__ = ['sample', 'group', 'index', 'xaxis', 'xaxis_raw', 'signal_raw', 'background',
                     'polarisation', 'wavelength', 'acqtime', 'acqtime_bg', 'ref_subtracted', 'ref_bg',
                     'ref_raw',
                     'acqtime_ref', 'acqtime_refbg',
                     'creationtime', 'timestamps', 'framewidth', 'frameheight', 'numframes',
                     'applied_calibration', 'upconverter_used', 'calibrated', 'downconverted',
                     'background_subtracted', 'refbackground_subtracted', 'normalised', 'signal_subtracted',
                     'signal_normalised', 'exp_divided_sig', 'exp_divided_bg',
                     'exp_divided_ref',
                     'exp_divided_refbg',  'cosmic_sig', 'cosmic_bg', 'cosmic_ref',
                     'cosmic_refbg', 'filename_sig', 'filename_bg', 'filename_ref', 'filename_refbg']

        def __init__(self):
            self.sample = None
            self.group = None
            self.index = None
            self.xaxis = None
            self.xaxis_raw = None
            self.signal_raw = None
            self.background = None
            self.polarisation = None
            self.wavelength = None
            self.acqtime = None
            self.acqtime_bg = None
            self.ref_subtracted = None
            self.ref_bg = None
            self.ref_raw = None
            self.acqtime_ref = None
            self.acqtime_refbg = None
            self.creationtime = None
            self.timestamps = None
            self.framewidth = None
            self.frameheight = None
            self.numframes = None
            self.applied_calibration = None
            self.upconverter_used = None
            self.calibrated = False
            self.downconverted = False
            self.background_subtracted = False
            self.refbackground_subtracted = False
            self.normalised = False
            self.signal_subtracted = None
            self.signal_normalised = None
            self.exp_divided_sig = False
            self.exp_divided_bg = False
            self.exp_divided_ref = False
            self.exp_divided_refbg = False
            self.cosmic_sig = False
            self.cosmic_bg = False
            self.cosmic_ref = False
            self.cosmic_bg = False
            self.filename_sig = 'NoSignal'
            self.filename_bg = 'NoBackground'
            self.filename_ref = 'NoReference'
            self.filename_refbg = 'NoReferenceBackground'

        def downconvert_spectrum(self, upconverter, force=False):
            """Downconvert the energy axis in the spectrum by upconverter in wavenumbers.

            Overwrites xaxis attribute with the downconverted version.
            The original xaxis attribute is stored as xaxis_raw if needed later.

            Parameters
            -----------
            upconverter : float
                The energy of the upconversion line to subtract in wavenumbers.
            force : bool, optional
                Allows downconversion more than once if true. Default False.
            """

            if not force:
                if self.downconverted:
                    print('Spectra already downconverted, exiting. Pass flag "force=True" if you '
                          'really want to downconvert twice.')
                    return

                self.xaxis_raw = self.xaxis
                self.xaxis = self.xaxis - upconverter
                self.upconverter_used = upconverter
                self.downconverted = True
                print('Energy axis downconverted by ' + f'{upconverter:f}' + 'cm-1.')

            if force:
                if self.downconverted:
                    print('Note: you are forcing multiple downconversions.')
                self.xaxis_raw = self.xaxis
                self.xaxis = self.xaxis - upconverter
                self.upconverter_used = upconverter
                self.downconverted = True
                print('Energy axis downconverted by ' + f'{upconverter:f}' + 'cm-1.')

            return

        def background_subtract(self, force=False):
            """Subtract the background spectrum from the signal spectrum.

            Subtracts background attribute from the signal attribute (if it already exists),
            or raw attribute (if it doesn't). Either way the signal attribute is created.

             Parameters
            -----------
            force : bool, optional
                Allows subtraction more than once if true. Default False.
            """
            if self.background is None:
                print("Error - no background file found.")
                return
            if self.signal_raw is None:
                print("Error - no signal file found.")
                return

            if not force:
                if self.background_subtracted:
                    print(
                        'Spectrum already background subtracted, exiting. Pass flag "force=True" if you '
                        'really want to subtract twice.')
                    return

                self.signal_subtracted = self.signal_raw - self.background
                self.background_subtracted = True
                print('Background subtracted from the signal data.')

            if force:
                if self.signal_subtracted is not None:
                    print("Note, you are subtracting the background twice.")
                    self.signal_subtracted = self.signal_subtracted - self.background
                    self.background_subtracted = True
                    print('Background subtracted from the signal data.')
                else:
                    self.signal_subtracted = self.signal_raw - self.background
                    self.background_subtracted = True
                    print('Background subtracted from the signal data.')

            return

        def ref_background_subtract(self, force=False):
            """Subtracts background from the reference signal.

            Subtracts from ref_raw unless ref_subtracted exists.

            Parameters
            -----------
            force : bool, optional
                Allows subtraction more than once if true. Default False
            """
            if self.ref_bg is None:
                print("Error - no background for the reference file found, exiting.")
                return
            if self.ref_raw is None:
                print("Error - no reference file found, exiting.")
                return

            if not force:
                if self.refbackground_subtracted:
                    print(
                        'Reference already backround subtracted, exiting. Pass flag "force=True" if you '
                        'really want to subtract twice.')
                    return

                self.ref_subtracted = self.ref_raw - self.ref_bg
                self.refbackground_subtracted = True
                print('Background subtracted from the reference data.')

            if force:
                if self.ref_subtracted is not None:
                    print('Note, you are subtracting the reference background twice.')
                    self.ref_subtracted = self.ref_subtracted - self.ref_bg
                    self.refbackground_subtracted = True
                    print('Background subtracted from the reference data.')
                else:
                    self.ref_subtracted = self.ref_raw - self.ref_bg
                    self.refbackground_subtracted = True
                    print('Background subtracted from the reference data.')

            return

        def normalise_data(self, force=False):
            """Divide a signal spectrum by the reference spectrum.

            Will divide by the subtracted spectrum if it exists, otherwise from the raw spectrum.

            Parameters
            -----------
            force : bool, optional
                Allows normalisation more than once if true. Default False
            """
            if self.ref_subtracted is None and self.ref_raw is None:
                print("Error - no reference files found, exiting.")
                return

            if self.ref_subtracted is not None:
                reference = self.ref_subtracted
            else:
                reference = self.ref_raw

            if not force:
                if self.normalised:
                    print('Spectrum already normalised, exiting. Pass flag "force=True" if'
                          ' you really want to normalise twice.')
                    return

                if self.background_subtracted:
                    self.signal_normalised = self.signal_subtracted / reference
                    self.normalised = True
                    print('Signal data successfully normalised.')
                else:
                    self.signal_normalised = self.signal_raw / reference
                    self.normalised = True
                    print('Signal data successfully normalised.')

            if force:
                if self.normalised:
                    print('Note, you are normalising twice.')
                    self.signal_normalised = self.signal_normalised / reference
                    self.normalised = True
                    print('Signal data successfully normalised (more than once, r u srs).')
                else:
                    if self.background_subtracted:
                        self.signal_normalised = self.signal_subtracted / reference
                        self.normalised = True
                        print('Signal data successfully normalised.')
                    else:
                        self.signal_normalised = self.signal_raw / reference
                        self.normalised = True
                        print('Signal data successfully normalised.')

            return

        @staticmethod
        def exposure_subroutine(data, time, flag, string, force):
            """Divide the given spectrum by its exposure time.

            This subroutine is called multiple times by divide_exposure()

            Parameters
            -----------
            data : np.ndarray
                The data to be divided by exposure time.
            time : float
                The exposure time to divide by.
            flag : bool
                True if the spectrum has already been divided, used to prevent unwanted multiple calls.
            string : str
                Refers to the type of spectrum being subtracted. Possible values:
                "signal", "background", "reference", "reference background"
            force : bool, optional
                Allows exposure division more than once if true. Default False
            """

            if not force:
                if data is None:
                    print('No ' + string + ' file found.')
                    return data, flag
                else:
                    if time is None:
                        print('No exposure time for ' + string + ' found. Check SPE file.')
                        return data, flag
                    else:
                        if flag:
                            print(
                                'Exposure for ' + string + ' already divided, exiting. Pass flag "force=True"'
                                                           ' if you really want to divide it twice')
                            return data, flag
                        else:
                            data = data / time
                            flag = True
                            print(string + ' data divided by exposure time of ' + str(time) + ' s.')

            if force:
                print('Warning, you might be dividing the exposure out more than once.')
                if data is None:
                    print('No ' + string + ' file found.')
                    return data, flag
                else:
                    if time is None:
                        print('No exposure time for ' + string + ' found. Check SPE file.')
                        return data, flag
                    else:
                        data = data / time
                        flag = True
                        print(string + ' data divided by exposure time of ' + str(time) + ' s.')

            return data, flag

        def divide_exposure(self, force=False):
            """Divide all stored spectra by their relevant exposure times.

            Call this on the raw data before you do further processing.

            Parameters
            -----------
            force : bool, optional
                Allows exposure division more than once if true. Default False
            """

            if self.signal_raw is not None:
                self.signal_raw, self.exp_divided_sig = self.exposure_subroutine(self.signal_raw,
                                                                                 self.acqtime,
                                                                                 self.exp_divided_sig,
                                                                                 'signal', force)
            if self.background is not None:
                self.background, self.exp_divided_bg = self.exposure_subroutine(self.background,
                                                                                self.acqtime_bg,
                                                                                self.exp_divided_bg,
                                                                                'background', force)
            if self.ref_raw is not None:
                self.ref_raw, self.exp_divided_ref = self.exposure_subroutine(self.ref_raw,
                                                                              self.acqtime_ref,
                                                                              self.exp_divided_ref,
                                                                              'reference', force)
            if self.ref_bg is not None:
                self.ref_bg, self.exp_divided_refbg = self.exposure_subroutine(self.ref_bg,
                                                                               self.acqtime_refbg,
                                                                               self.exp_divided_refbg,
                                                                               'reference background',
                                                                               force)
            return

        def calibrate_spectrum(self, calibration_offset, force=False):
            """Shift the energy axis of a spectrum by +calibration_offset.

            Passing "force" and calibrating multiple times will update the applied_calibration attribute
            of datastore to keep track of what has been done.

            Parameters
            -----------
            calibration_offset : float
                The amount to shift the energy xaxis, in wavenumbers. Positive numbers shift to higher energy.
            force : bool, optional
                Allows calibration more than once if true. Default False
            """
            if not force:
                if self.calibrated:
                    print('Calibration offset already applied, exiting. Pass flag "force=True" if you'
                          ' really want to apply offset more than once.')
                    return

                self.xaxis = self.xaxis + calibration_offset
                self.applied_calibration = calibration_offset
                self.calibrated = True
                print('Calibration of ' + f'{calibration_offset:+f}' + 'cm-1 applied.')

            if force:
                if self.calibrated:
                    self.applied_calibration = self.applied_calibration + calibration_offset
                    print('Note, you are applying multiple calibrations.')
                    self.xaxis = self.xaxis + calibration_offset
                else:
                    self.applied_calibration = calibration_offset
                    self.xaxis = self.xaxis + calibration_offset

                self.calibrated = True
                print('Calibration of ' + f'{calibration_offset:+f}' + 'cm-1 applied.')
                print('Total calibration offset of ' + f'{self.applied_calibration:+d}' + 'cm-1 applied.')
            return

        @staticmethod
        def cosmic_ray_killer(data, threshold, max_width):
            """Remove cosmic ray contributions from data.

            Algorithm from Steven J Roeters. Not thoroughly tested but implemented for future use.

            Questionably robust method for doing it that might just require endless tweaking.

            Parameters
            -----------
                data : np array
                    Array containing the data to have cosmic ray contributions removed. Shape (1, width).
                threshold : float
                    Min height above the background signal that a spike has to have to be considered a
                    cosmic ray.
                max_width : int
                    Anything wider that max_width is considered real signal and not a cosmic ray.

            Returns
            ------------
                data : np array
                    Data with cosmic ray contributions removed.
                rays_removed : bool
                    Flag used to keep track of whether or not the data has had cosmic ray contributions
                    removed.
            """
            print("Killing cosmic rays. Threshold: ", threshold, ". Max width: ", max_width, ".")
            raycount = 0
            for i in range(len(data[0]) - int(max_width)):
                n = 0
                while data[0][i + n] >= data[0][i] + float(threshold):
                    n = n + 1
                    if data[0][i + n] < data[0][i] + float(threshold):
                        for k in range(n):
                            raycount = raycount + 1
                            data[0][i + k] = np.interp(i + k, [i, i + n + 1], [data[0][i], data[0][i + n +
                                                                                                   1]])
                    if n == int(max_width):
                        break
            rays_removed = True
            print("Rays removed:", raycount)
            return data, rays_removed

        def remove_cosmic_rays(self, threshold, max_width, flag):
            """Call cosmic_ray_killer on raw data.

            Uses flag to decide what kind of raw data to apply the removal to.

            Parameters
            -----------
                threshold : float
                    Min height above the background signal that a spike has to have to be considered a
                    cosmic ray.
                max_width : int
                    Anything wider that max_width is considered real signal and not a cosmic ray.
                flag : str
                    Determines what attribute of SFGDataStore to remove rays from. Possible values are
                    "sig", "bg", "ref", "refbg", or "all".
            """

            if flag == 'sig':
                self.signal_raw, self.cosmic_sig = self.cosmic_ray_killer(self.signal_raw, threshold,
                                                                          max_width)

            elif flag == 'bg':
                self.background, self.cosmic_bg = self.cosmic_ray_killer(self.background, threshold,
                                                                         max_width)
            elif flag == 'ref':
                self.ref_raw, self.cosmic_ref = self.cosmic_ray_killer(self.ref_raw, threshold, max_width)
            elif flag == 'refbg':
                self.ref_bg, self.cosmic_refbg = self.cosmic_ray_killer(self.ref_bg, threshold, max_width)
            elif flag == 'all':
                self.signal_raw, self.cosmic_sig = self.cosmic_ray_killer(self.signal_raw, threshold,
                                                                          max_width)
                self.background, self.cosmic_bg = self.cosmic_ray_killer(self.background, threshold,
                                                                         max_width)
                self.ref_raw, self.cosmic_ref = self.cosmic_ray_killer(self.ref_raw, threshold, max_width)
                self.ref_bg, self.cosmic_refbg = self.cosmic_ray_killer(self.ref_bg, threshold, max_width)
            else:
                print('Flag of', flag, 'invalid. Possible values are  "sig", "bg, "ref", "refbg", '
                                       '"all". Exiting.')
            return

    def process_data(self, datastore, downconvert_check, subtract_check, normalise_check,
                     exposure_check, calibrate_check, cosmic_kill_check,
                     force=False):
        """Process data stored in datastore according to provided check flags.

        Datastore contains SFG data to be processed, and methods of the datastore class are called to
        process the data. Bool flags are used to determine what processing to do. Note that the order in
        which the methods are called is important.

        Parameters
        -----------
        datastore : SFGDataStore object
            Contains the data to be processed.
        downconvert_check : bool
            If true then downconvert the data.
        subtract_check : bool
            If true then background subtract the data.
        normalise_check : bool
            If true then normalise the data to reference.
        exposure_check : bool
            If true then divide all spectra by exposure time.
        calibrate_check : bool
            If true then shift data energy axis by provided offset.
        cosmic_kill_check : bool
            If true then remove cosmic rays using cosmic_ray_killer().
        force : bool, optional.
            If true then allow data to be (e.g.) downconverted more than once (default False).
        """

        if cosmic_kill_check:
            datastore.remove_cosmic_rays(self.cosmic_threshold, self.cosmic_max_width, 'sig')
            if subtract_check:
                datastore.remove_cosmic_rays(self.cosmic_threshold, self.cosmic_max_width, 'bg')
            if normalise_check:
                datastore.remove_cosmic_rays(self.cosmic_threshold, self.cosmic_max_width, 'ref')
            if normalise_check and subtract_check:
                datastore.remove_cosmic_rays(self.cosmic_threshold, self.cosmic_max_width, 'refbg')

        if downconvert_check:
            upconverter = self.nm_to_cm(self.upconversion_line_num)
            datastore.downconvert_spectrum(upconverter, force)

        if calibrate_check:
            datastore.calibrate_spectrum(np.float32(self.calibration_offset), force)

        if exposure_check:
            datastore.divide_exposure(force)

        if subtract_check:
            datastore.background_subtract(force)

        if subtract_check and normalise_check:
            datastore.ref_background_subtract(force)

        if normalise_check:
            datastore.normalise_data(force)

        return

    def batch_process(self, datastores):
        """Process all data in the instances contained in datastores.

        Assumes you have a list of populated SFGDataStore objects to process (one per file).

        Here the bool checks are all called as class attributes via self rather than passed explicitly,
        which makes life slightly less cumbersome when invoking it in the GUI.

        Parameters
        -----------
        datastores : list
            Contains SFGDataStore objects, one per file to be processed.
        """

        num_files = len(datastores)
        print('Processing ' + f'{num_files:d}' + ' files.')
        for i, datastore in enumerate(datastores):

            print('Processing file ' + f'{i + 1:d}' + '/' + f'{num_files:d}')
            self.process_data(datastore, self.downconvert_check, self.subtract_check, self.normalise_check,
                              self.exposure_check, self.calibrate_check, self.cosmic_kill_check,
                              self.global_force)
            if self.write_file_check:
                self.write_data_to_file(datastore, self.write_directory)
            if self.plot_data_check:
                self.current_figure = self.plot_data(datastore, i, num_files, self.current_figure)

        return

    def plot_data(self, datastore, iteration, num_files, figure):
        """Plot processed SFG data from datastore to figure.

        Plots data contained in datastore, defaults to plotting normalised and subtracted data if present,
        otherwise subtracted, otherwise plots raw. If custom_region parameters are set in the GUI,
        then it will constrain the x axis to that region and rescale y, otherwise full range is plotted.

        Class attributes are used to determine other parameters that are mostly set by the GUI or plotting
        script.

        Parameters
        -----------
        datastore : SFGDataStore object
            Contains data to be plotted.
        iteration : int
            Current index of file being processed (for batch processing).
        num_files : int
            Total number of files to process.
        figure : matplotlib.pyplot.figure object
            Figure to plot data on (if stacking).

        Returns
        ----------
        figure : matplotlib.pyplot.figure object
            Figure that data was plotted on in the previous iteration.
        """
        if self.close_plots_check:
            plt.close('all')

        if datastore.normalised:
            signal = datastore.signal_normalised
            titleflag = '(normalised and subtracted)'
        elif datastore.background_subtracted:
            signal = datastore.signal_subtracted
            titleflag = '(subtracted, not normalised)'
        else:
            signal = datastore.signal_raw
            titleflag = '(not subtracted or normalised)'

        if self.custom_region_start is not None:
            leftwindow = float(self.custom_region_start)
        else:
            leftwindow = datastore.xaxis[-1]

        if self.custom_region_end is not None:
            rightwindow = float(self.custom_region_end)
        else:
            rightwindow = datastore.xaxis[0]

        mask = (datastore.xaxis >= leftwindow) & (datastore.xaxis <= rightwindow)

        if iteration == 0:
            figure = plt.figure()

        elif not self.stack_plots_check:
            figure = plt.figure()

        ax = figure.gca()

        for i in range(datastore.frameheight):
            ax.plot(datastore.xaxis[mask], signal[int(i), mask])

        ax.set_ylabel(r'SFG Intensity [a. u.]')
        ax.set_xlabel(r'Wavenumber [cm$^{-1}$]')

        title = pathlib.Path(datastore.filename_sig).name.replace('.spe', '')
        ax.set_title(str(title)+'\n'+titleflag)
        ax.set_xlim(leftwindow, rightwindow)
        plt.tight_layout()
        ax.autoscale(axis='y')

        if self.stack_plots_check:
            if iteration == num_files-1:
                plt.show()
        else:
            plt.show()

        return figure

    def write_data_to_file(self, datastore, directory):
        """Write data in datastore to a text file in directory.

        Data is written into a text file as columns with a 12 line header explaining what the data is and
        how it has been processed. Nine columns are written with different types of data, but column 0 and
        1 are the ones that contain the useful data in most cases.

        Parameters
        -----------
        datastore : SFGDataStore object
            Where the data to be written is stored.
        directory : str
            Where the resulting .txt file is to be saved.
        """
        headstring = " Signal Data File: " + datastore.filename_sig + \
                     "\n Background Data File: " + datastore.filename_bg + \
                     "\n Reference File: " + datastore.filename_ref + \
                     "\n Reference Background File: " + datastore.filename_bg

        if datastore.background_subtracted:
            headstring = headstring + "\n Background Subtracted? YES"
        else:
            headstring = headstring + "\n Background Subtracted? NO"

        if datastore.normalised:
            headstring = headstring + "\n Normalised to Reference? YES"
        else:
            headstring = headstring + "\n Normalised to Reference? NO"

        if datastore.downconverted:
            headstring = headstring + "\n Downconverted? YES. Line Used: " + str(
                self.upconversion_line_num) + " nm"
        else:
            headstring = headstring + "\n Downconverted? NO"

        if datastore.calibrated:
            headstring = headstring + "\n Calibrated? YES. Calibration Applied: " \
                         + f'{datastore.applied_calibration:+d}' + " cm-1"
        else:
            headstring = headstring + "\n Calibrated? NO"

        if datastore.exp_divided_sig:
            headstring = headstring + "\n Exposure corrected for Signal? YES, Exposure time: " + str(
                datastore.acqtime) + 's'
        else:
            headstring = headstring + "\n Exposure Corrected for Signal? NO"

        if datastore.exp_divided_bg:
            headstring = headstring + "\n Exposure corrected for Background? YES, Exposure time: " + str(
                datastore.acqtime_bg) + 's'
        else:
            headstring = headstring + "\n Exposure Corrected for Background? NO"

        if datastore.exp_divided_ref:
            headstring = headstring + "\n Exposure corrected for Reference? YES, Exposure time: " + str(
                datastore.acqtime_ref) + 's'
        else:
            headstring = headstring + "\n Exposure Corrected for Reference? NO"

        if datastore.exp_divided_sig:
            headstring = headstring + "\n Exposure corrected for Reference Background? YES, Exposure time: " \
                                      "" + str(datastore.acqtime_refbg) + 's'
        else:
            headstring = headstring + "\n Exposure Corrected for Reference Background? NO"

        headstring = headstring + "\n 0: Energy Axis, 1: Signal Normalised, 2: Reference, " \
                                  "3: Signal Pre-Normalise, " \
                                  "4: Signal Pre-Subtract, 5: Background, 6:Reference Pre-Subtract, " \
                                  "7: Energy Axis Raw"

        modelarray = np.empty((1, datastore.framewidth))
        modelarray_xaxis = np.empty((datastore.framewidth))

        # JDP  - this is to just print a column of NaNs if you havent done part of the processing. Theres
        # probably a less clunky way to do this but whatever.
        if datastore.xaxis is None:
            datastore.xaxis = np.full_like(modelarray_xaxis, fill_value=np.nan)
        if datastore.xaxis_raw is None:
            datastore.xaxis_raw = np.full_like(modelarray_xaxis, fill_value=np.nan)
        if datastore.signal_normalised is None:
            datastore.signal_normalised = np.full_like(modelarray, fill_value=np.nan)
        if datastore.ref_subtracted is None:
            datastore.ref_subtracted = np.full_like(modelarray, fill_value=np.nan)
        if datastore.signal_subtracted is None:
            datastore.signal_subtracted = np.full_like(modelarray, fill_value=np.nan)
        if datastore.signal_normalised is None:
            datastore.signal_normalised = np.full_like(modelarray, fill_value=np.nan)
        if datastore.signal_raw is None:
            datastore.signal_raw = np.full_like(modelarray, fill_value=np.nan)
        if datastore.background is None:
            datastore.background = np.full_like(modelarray, fill_value=np.nan)
        if datastore.ref_raw is None:
            datastore.ref_raw = np.full_like(modelarray, fill_value=np.nan)

        data_arrays = np.array([datastore.xaxis, datastore.signal_normalised[0], datastore.ref_subtracted[0],
                                datastore.signal_subtracted[0], datastore.signal_raw[0], datastore.background[0],
                                datastore.ref_raw[0], datastore.ref_subtracted[0], datastore.xaxis_raw])

        title = pathlib.Path(datastore.filename_sig).stem

        np.savetxt(directory + "/" + title + "_processed.txt", data_arrays.T, header=headstring,
                   fmt='%-10.5f')

        return

    def create_data_stores(self, num_files):
        """Create a list of SFGDataStore classes of length num_files.

        Parameters
        -----------
        num_files : int
            Number of files to process (and SFGDataStore instances to create).

        Returns
        ----------
        datastores : list
            Contains empty SFGDataStore instances to be populated.
        """

        datastores = [self.SFGDataStore() for _ in range(num_files)]

        return datastores

    def populate_data_stores(self, datastores, directory, signal_names, bg_names, ref_names, ref_bg_names):
        """Populate the SFGDataStore classes in datastores by reading files.

        Reads the data from the .spe file given in the supplied lists and populates the SFGDataStore
        classes accordingly. Uses bool flags from the class attributes to determine what to read.

        The lists are assumed to be ordered, so that the datastore in elemnent [n] of datastores is
        populated using signal data from signal_names[n], background from bg_names[n], and so on. This
        can be sorted manually in the command line, but the match_files method does it automatically for
        the GUI.

        Parameters
        -----------
        datastores : list
            Contains empty SFGDataStore class instances to be populated.
        directory : str
            Directory that the data files are stored in.
        signal_names : list
            Contains filenames of the signal data files to be processed.
        bg_names : list
            Contains filenames of the background data files of the signal data files to be processed.
        ref_names : list
            Contains filenames of the reference data files to be processed.
        ref_bg_names : list
            Contains filenames of the background data files of the reference data files to be processed.
        """
        for i, datastore in enumerate(datastores):
            self.read_files(directory + signal_names[i], datastore, 'sig')
            self.parse_filename(directory, signal_names[i], datastore)

            if self.normalise_check:
                self.read_files(directory + ref_names[i], datastore, 'ref')
                if self.subtract_check:
                    self.read_files(directory + ref_bg_names[i], datastore, 'refbg')

            if self.subtract_check:
                self.read_files(directory + bg_names[i], datastore, 'bg')

        return

    def parse_filename(self, directory, file, datastore):
        """Parse the name of file and populate datastore with relevant info.

        Populates various attributes of datastore with helpful info stored in the filename,
        such as polarisation, wavelength, creation time, and index/group. Not required in version 1.0 but
        could be useful later.

        Parameters
        -----------
        directory : str
            The directory that the files are stored in.
        file : str
            The name of the file to be parsed.
        datastore : SFGDataStore object
            The datastore to populate with the information gained from parsing.

        """

        if file.endswith(".spe"):
            names_nospe = file.replace(".spe", "").split('_')
        elif file.endswith(".txt"):
            names_nospe = file.replace(".txt", "").split('_')
        else:
            print("Invalid File Type, exiting.")
            return

        # JDP checks if a sample string has been defined by the user, if not then reads from filename.
        if self.samplestring is not None:
            datastore.sample = self.samplestring
        else:
            datastore.sample = names_nospe[0]

        # JDP checks if the penultimate element is numeric, if it is then define this as the group
        if names_nospe[-2].isnumeric():
            datastore.group = int(names_nospe[-2])

        # JDP checks if the final element is numeric, if it is then define this as the index
        if names_nospe[-1].isnumeric():
            datastore.index = int(names_nospe[-1])

        # JDP if there is something ending in "nm" then define this as the wavelength.
        for string in names_nospe:
            if string.endswith('nm') & string.replace('nm', '').isnumeric():
                datastore.wavelength = int(string.replace('nm', ''))

        # JDP set the polarisation according to what is in the name. If it is not, then defaults to None.
        if 'PPP' in names_nospe:
            datastore.polarisation = 'PPP'
        elif 'SPP' in names_nospe:
            datastore.polarisation = 'SPP'
        elif 'PSP' in names_nospe:
            datastore.polarisation = 'PSP'
        elif 'PPS' in names_nospe:
            datastore.polarisation = 'PPS'
        elif 'SSP' in names_nospe:
            datastore.polarisation = 'SSP'
        elif 'SPS' in names_nospe:
            datastore.polarisation = 'SPS'
        elif 'PSS' in names_nospe:
            datastore.polarisation = 'PSS'
        elif 'SSS' in names_nospe:
            datastore.polarisation = 'SSS'

        # JDP gets the time that the file was created
        datastore.creationtime = self.get_file_creationtime(directory + file)

        return

    def get_filenames_smart(self):
        """Globs all .spe files in the current data directory and sorts them into lists.

        Used mostly in the GUI so parameters are all class attributes modified by the GUI. This method
        looks in a directory for all the .spe files that are present, and then splits them up into signal,
        background, reference, and reference background, in line with the (user supplied) strings that
        determine if a file is a sample, reference, or background. For example, using attributes:

        self.samplestring = sampledata
        self.refstring = referencedata
        self.bg_string = _bg

        Would sort the following files as follows:

        sampledata.spe -> signal
        sampledata_bg.spe -> background
        referencedata.spe -> reference
        referencedata_bg.spe -> reference background

        It is important that the files START with the supplied sample and ref strings. The bg string can be
        anywhere in the filename.

        Returns
        ----------
        signal_names : list
            Contains names of signal files.
        bg_names : list
            Contains names of background files.
        ref_names : list
            Contains names of reference files.
        ref_bg_names : list
            Contains names of reference background files.
        ref_id : list
            Contains indexes for each unique reference file (later associated with a corresponding signal
            file).
        """
        names = glob.glob(self.data_directory+'*.spe')

        signal_names = [pathlib.PurePath(i).name for i in names if self.bg_string not in
                        pathlib.PurePath(i).name and pathlib.PurePath(i).name.startswith(self.samplestring)]

        bg_names = [pathlib.PurePath(i).name for i in names if self.bg_string in pathlib.PurePath(i).name and
                    pathlib.PurePath(i).name.startswith(self.samplestring)]

        ref_names = [pathlib.PurePath(i).name for i in names if self.bg_string not in i and
                     pathlib.PurePath(i).name.startswith(self.refstring)]

        ref_bg_names = [pathlib.PurePath(i).name for i in names if self.bg_string in i and
                        pathlib.PurePath(i).name.startswith(self.refstring)]

        ref_id = [ref_names.index(i)+1 for i in ref_names]

        return signal_names, bg_names, ref_names, ref_bg_names, ref_id

    def pull_trigger(self):
        """Start the processing sequence.

        Used mainly in the GUI. When all files are read in and sorted properly, this will create
        datastores, populate datastores, and process all the data using batch_process() according to the
        flags supplied. Parameters are all class attributes.

        The lists containing data files all need to be properly matched and sorted for this to make sense.
        """
        numfiles = len(self.signal_names)
        datastores = self.create_data_stores(numfiles)
        self.populate_data_stores(datastores, self.data_directory, self.signal_names, self.bg_names,
                                  self.ref_names, self.ref_bg_names)
        self.batch_process(datastores)
        return 

    def read_files(self, fname, datastore, flag):
        """Read fname and put the data in the right place in datastore using flag.

        Currently this implementation looks pointless, but it is made so that eventually filetypes other
        than .spe can be read in the same program.

        Parameters
        -----------
        fname : str
            File to be read in.
        datastore : SFGDataStore object
            Datastore to put the data from the file into.
        flag : str
            Tells the .spe reader where to put this data in datastore. Options are "sig", "bg", "ref",
            "refbg".
        """
        if fname.endswith(".spe"):
            self.open_spe(fname, datastore, flag)
        else:
            print('Bad file type - needs to be an SPE file, exiting.')
            return
        return

    @staticmethod
    def match_polarisations_bg(pol, bg_names):
        """UNUSED. Identify bg files with different polarisations to signal files.

        e.g. If signal file is in SSP polarisation, then a background file could either be SSP or SSS.

        NOT IMPLEMENTED IN VERSION 1.0
        """
        if pol == 'PPP' or pol == 'PPS':
            testpol = ['PPP', 'PPS']
        elif pol == 'PSP' or pol == 'PSS':
            testpol = ['PSP', 'PSS']
        elif pol == 'SPP' or pol == 'SPS':
            testpol = ['SPP', 'SPS']
        elif pol == 'SSS' or pol == 'SSP':
            testpol = ['SSS', 'SSP']
        else:
            print('No valid polarisations in filename, exiting.')
            return

        bg_names_match = [i for i in bg_names if testpol[0] in i or testpol[1] in i]
        return bg_names_match

    # def sum_spectra(self):
    #     # JDP tells you how many types of each attribute there are - we find instances that all have common 
    #     of these
    #     # JDP these attributes but then sum over multiple indices
    #
    #     # pol_attr = list(set([i.polarisation for i in self.data_instances]))
    #     # wavelength_attr = list(set([i.wavelength for i in self.data_instances]))
    #     # sample_attr = list(set([i.sample for i in self.data_instances]))
    #     # group_attr = list(set([i.group for i in self.data_instances]))
    #
    #     num_pol = len(pol_attr)
    #     num_wavelength = len(wavelength_attr)
    #     num_sample = len(sample_attr)
    #     num_group = len(group_attr)
    #     # JDP the number of output (summed) data classes to make is the product of the various attributes
    #     num_output = num_pol * num_wavelength * num_sample * num_group
    #     self.data_averaged_list = [None for i in range(num_output)]
    #     count = 0
    #
    #     for i in pol_attr:
    #         for j in wavelength_attr:
    #             for k in sample_attr:
    #                 for l in group_attr:
    #                     instances_select = [m for m in self.data_instances if m.polarisation == i and
    #                                         m.wavelength == j and m.sample == k and m.group == l]
    #                     self.data_averaged_list[count] = self.SFGDataStore()
    #                     self.data_averaged_list[count].sample = k
    #                     self.data_averaged_list[count].group = l
    #                     self.data_averaged_list[count].xaxis = instances_select[0].xaxis
    #                     self.data_averaged_list[count].signal = np.zeros_like(instances_select[0].signal)
    #                     self.data_averaged_list[count].polarisation = i
    #                     self.data_averaged_list[count].wavelength = j
    #                     self.data_averaged_list[count].ref = instances_select[0].ref
    #                     for n in instances_select:
    #                         self.data_averaged_list[count].signal = self.data_averaged_list[count].signal 
    #                         + n.signal
    #                     titlesum = str(k)+"_"+str(i)+"_"+str(j)+"_"+str(l)+"_summed"
    #                     if self.write_file_check:
    #                         self.save_data_sum_txt(self.data_averaged_list[count], titlesum)
    #                     count = count + 1
    #
    #
    #     return

    @staticmethod
    def get_file_creationtime(file):
        """Return the time of last modification of the file input."""
        fname = pathlib.Path(file)
        creation_time = fname.stat().st_mtime
        return creation_time

    def get_closest_file(self, files, target):
        """Compare the time of last modification of each element of files, and find the closest one to target.


        Parameters
        -----------
        files : list
            Contains files that are being tested for closeness-in-time to target.
        target : str
            File that is used as a target to find the closest file to.

        Returns
        -----------
        closest_file : str
            The element of files that was created at the closest time to target.
        """
        target_time = self.get_file_creationtime(target)
        times = [self.get_file_creationtime(i) for i in files]
        index = min(range(len(times)), key=lambda k: abs(times[k] - target_time))
        closest_file = files[index]
        return closest_file

    def open_spe(self, fname, datastore, flag):
        """Open an .spe file and send it to the correct reader method.

        Different spectroscopy cameras read off different versions of the .spe file that is currently used
        a lot (why people don't just save the spectrum they want as a .txt file, given that this is how 99%
        of spectrscopy is done, is a good question). Andor cameras generally read .spe version 2.5,
        and Princeton Instruments cameras (who maintain the .spe filetype) generally read version 3.0. The
        difference is largely in flexibility and metadata. See the SPE3.0 file format declaration for info
        (online in places).

        Parameters
        -----------
        fname : str
            Name of file to be opened.
        datastore : SFGDataStore object
            Datastore to put the data read from the file into.
        flag : str
            Determines whether the data is stored as signal, background, reference, or reference
            background. Possible values "sig", "bg", "ref", "refbg".

        """

        binaryfile = open(fname, 'rb')

        spe_version = self.read_at(binaryfile, self.spe_version_loc, -1, np.float32)[0]

        if self.verbose:
            print("SPE Version is", spe_version)

        self.assign_filename_to_storage(flag, datastore, fname)

        if spe_version < 3.0:
            self.process_spe2x(binaryfile, datastore, flag)

        if spe_version >= 3.0:
            self.process_spe3x(binaryfile, datastore, flag)

        return
    
    @staticmethod
    def read_at(file, pos, size, ntype):
        """Read a binary file at a specific position in bytes.

        Parameters
        -----------
        file : file object
            Opened binary file that you want to read from.
        pos : int
            Location (in bytes) to start reading from.
        size : int
            Number of items after pos to read. -1 reads all items.
        ntype : data type
            Data type the binary is encoded in.

        Returns
        -----------
         data : ntype
            The data read from the binary file.
        """
        file.seek(pos)
        data = np.fromfile(file, ntype, size)
        return data

    def get_pixel_type(self, pixeltype):
        """Convert the pixel type given by SPE 2.x and 3.0 files to numpy datatype.

        The pixeltype read from the SPE file is either a string (spe 3.0) or an integer (spe 2.x) that
        needs decoding. This method converts either to a numpy datatype.

        Parameters
        -----------
        pixeltype : int or str
            The pixeltype obtained from reading the SPE file. str for SPE 3.0, int for SPE 2.x.

        Returns
        -----------
        pixeltype_np : numpy datatype
            Numpy datatype corresponding to the pixel datatype.
        pixelsize : int
            Size of the pixel in bytes.
        """

        if pixeltype == 'MonochromeUnsigned16':
            pixeltype_np = np.uint16
            pixelsize = 2
            if self.verbose:
                print("Pixel type is unsigned 16 bit integer (2 bytes)")
        elif pixeltype == 'MonochromeUnsigned32':
            pixeltype_np = np.uint32
            pixelsize = 4
            if self.verbose:
                print("Pixel type is unsigned 32 bit integer (4 bytes)")
        elif pixeltype == 'MonochromeFloating32':
            pixeltype_np = np.float32
            pixelsize = 4
            if self.verbose:
                print("Pixel type is 32 bit float (4 bytes)")

        elif pixeltype == 0:
            pixeltype_np = np.float32
            pixelsize = 4
            if self.verbose:
                print("Pixel type is 32 bit float")
        elif pixeltype == 1:
            pixeltype_np = np.int32
            pixelsize = 4
            if self.verbose:
                print("Pixel type is signed 32 bit integer")
        elif pixeltype == 2:
            pixeltype_np = np.int16
            pixelsize = 2
            if self.verbose:
                print("Pixel type is signed 16 bit integer")
        elif pixeltype == 3:
            pixeltype_np = np.uint16
            pixelsize = 2
            if self.verbose:
                print("Pixel type is unsigned 16 bit integer")
        elif pixeltype == 5:
            pixeltype_np = np.float64
            pixelsize = 8
            if self.verbose:
                print("Pixel type is 64 bit float")
        elif pixeltype == 6:
            pixeltype_np = np.uint8
            pixelsize = 1
            if self.verbose:
                print("Pixel type is unsigned 8 bit integer")
        elif pixeltype == 8:
            pixeltype_np = np.uint32
            pixelsize = 4
            if self.verbose:
                print("Pixel type is unsigned 32 bit integer")
        else:
            err = QtWidgets.QMessageBox()
            err.setText("Your SPE file has an unrecognised pixel type, exiting.")
            err.setIcon(QtWidgets.QMessageBox.Warning)
            err.setStandardButtons(QtWidgets.QMessageBox.Ok)
            err.setDefaultButton(QtWidgets.QMessageBox.Ok)
            err.exec_()
            return
        return pixeltype_np, pixelsize

    @staticmethod
    def slice_data(datastore, data_in, data_out):
        """Slice a data array into a consistent shape.

         For most cases will slice to an array of dimensions (1, framewidth), but if the binning isnt to
         one pixel then this will become (frameheight, framewidth). Keeping that first dimension for future
         consistency.

        Parameters
        ----------
        datastore : SFGDataStore object
            Where the framewidth and frameheight are stored for the indexing.
        data_in :  np array
            1D array of data read from the data file.
        data_out : np array
            (frameheight, framewidth) shaped empty (or zero) array.

        Returns
        -----------
        data_out : np array
            (frameheight, framewidth) shaped array containing data.
        """

        for i in range(datastore.frameheight):
            start = int(i) * datastore.framewidth
            stop = start + datastore.framewidth
            dataslice = data_in[start:stop]
            data_out[int(i), :] = dataslice

        return data_out

    @staticmethod
    def assign_data_to_storage(flag, datastore, data):
        """Take the assigned flag and put the data read from the file in the right datastore attribute.

        Parameters
        -----------
        flag : str
            Defines the storage attribute of datastore to put the data into. Possible values "sig", "bg",
            "ref", "refbg".
        datastore : SFGDataStore object
            The datastore instance to put the data into.
        data : np array
            Numpy array of the data to store.
        """
        if flag == 'bg':
            datastore.background = data
        elif flag == 'ref':
            datastore.ref_raw = data
        elif flag == 'refbg':
            datastore.ref_bg = data
        elif flag == 'sig':
            datastore.signal_raw = data
        else:
            print('Could not identify data type, invalid flag.')
        return

    @staticmethod
    def assign_acqtime_to_storage(flag, datastore, acqtime):
        """Take the assigned flag and put the acquisition time from the file in the right datastore.

        Parameters
        -----------
        flag : str
            Defines the storage attribute of datastore to put the exposure time into. Possible values "sig",
            "bg", "ref", "refbg".
        datastore : SFGDataStore object
            The datastore instance to put the acquisition time into.
        acqtime : float
            Acqusition time in seconds.
        """
        if flag == 'bg':
            datastore.acqtime_bg = acqtime
        elif flag == 'ref':
            datastore.acqtime_ref = acqtime
        elif flag == 'refbg':
            datastore.acqtime_refbg = acqtime
        elif flag == 'sig':
            datastore.acqtime = acqtime
        else:
            print('Could not identify data type, invalid flag.')
        return
    
    @staticmethod
    def assign_filename_to_storage(flag, datastore, filename):
        """Take the assigned flag and put the filename into the right datastore attribute.

        Parameters
        -----------
        flag : str
            Defines the storage attribute of datastore to put the filename into. Possible values "sig", "bg",
            "ref", "refbg".
        datastore : SFGDataStore object
            The datastore instance to put the data into.
        filename : str
            Filename to store in datastore.
        """
        if flag == 'bg':
            datastore.filename_bg = filename
        elif flag == 'ref':
            datastore.filename_ref = filename
        elif flag == 'refbg':
            datastore.filename_refbg = filename
        elif flag == 'sig':
            datastore.filename_sig = filename
        else:
            print('Could not identify data type, invalid flag.')
        return

    def process_spe2x(self, binaryfile, datastore, flag):
        """Process data from an SPE 2.x file and put it in the relevant datastore.

        Reads the SPE file at the places defined in the binary header. The output data is in the shape (
        frameheight, framewidth), so is normally (1, n) for a standard spectrum. Extra dimensions are added
        if the full chip is read out, or if there is more than one frame in the SPE file.

        ftp://ftp.piacton.com/Public/Manuals/Princeton%20Instruments/SPE%203.0%20File%20Format%20Specification%20Issue%206%20(4411-0140).pdf
        Most of the options are class attributes and set externally by the GUI and not passed directly.

        Parameters
        -----------
        binaryfile : binary file object
            The opened .spe file to be processed.
        datastore : SFGDataStore object
            Where the data is stored to.
        flag : str
            Determines where in datastore the data is saved. Possible values "sig", "bg", "ref", "refbg".
        """

        # JDP make sure you cast things to 32bit integers to avoid overflows
        datastore.framewidth = self.read_at(binaryfile, self.framewidth_loc, 1, np.uint16)[0].astype(int)
        datastore.frameheight = self.read_at(binaryfile, self.frameheight_loc, 1, np.uint16)[0].astype(int)
        datastore.numframes = self.read_at(binaryfile, self.numframes_loc, 1, np.int32)[0].astype(int)
        pixeltype = self.read_at(binaryfile, self.pixeltype_loc, 1, np.int16)[0]
        pixeltype_np, pixelsize = self.get_pixel_type(pixeltype)
        npixels = datastore.framewidth * datastore.frameheight
        framestride = npixels * pixelsize
        acqtime = self.read_at(binaryfile, self.acqtime_loc, 1, np.float32)[0]
        self.assign_acqtime_to_storage(flag, datastore, acqtime)

        if self.verbose:
            print("Width of frame is", datastore.framewidth, "pixels.")
            print("Height of frame is", datastore.frameheight, "pixels.")
            print("Number of frames is", datastore.numframes)
            print("Pixel size is", pixelsize, "bytes.")
            print("Frame size is", framestride, "bytes")
            print("Acqusition time per frame is:", datastore.acqtime, "s.")
            print("Total acquisition time is:", datastore.acqtime * datastore.numframes, "s.")

        if datastore.frameheight > 1:
            print("Your data is not in n x 1 format.")

        # JDP read the data from location 4100 onwards - size is width x height as usual.
        if datastore.numframes == 1:
            # JDP read data into a temporary array
            data_temp = self.read_at(binaryfile, self.data_offset_loc_loc, npixels, pixeltype_np)
            # JDP create empty array for final data
            data = np.zeros((datastore.frameheight, datastore.framewidth))
            # JDP slice up data_temp into the array
            data = self.slice_data(datastore, data_temp, data)
            # JDP write to the datastore class
            self.assign_data_to_storage(flag, datastore, data)

        if datastore.numframes > 1 and self.sum_accumulations:
            # JDP create empty array for final summed data
            data = np.zeros((datastore.framewidth, datastore.frameheight))
            for i in range(datastore.numframes):
                # JDP read data into a temporary array
                data_temp = self.read_at(binaryfile, self.data_offset_loc_loc + (int(i) * framestride),
                                         npixels, pixeltype_np)

                # JDP make a temporary array to hold the data being summed in each iteration
                data_sum = np.zeros((datastore.frameheight, datastore.framewidth))
                # JDP slice up data into the sum array
                data_sum = self.slice_data(datastore, data_temp, data_sum)
                # JDP add data from each frame into the array
                data = data + data_sum

                if self.stupid_verbose:
                    print("Current frame", data_sum)
                    print("Running summation", data)

            self.assign_data_to_storage(flag, datastore, data)

        if datastore.numframes > 1 and self.series_accumulations:
            data_series = np.zeros((datastore.framewidth, datastore.frameheight, datastore.numframes))
            datastore.timestamps = np.zeros(datastore.numframes)
            for i in range(datastore.numframes):
                # JDP read data into a temporary array
                data_temp = self.read_at(binaryfile, self.data_offset_loc_loc + (int(i) * framestride),
                                         npixels, pixeltype_np)
                # JDP slice up data if needed
                data_sliced = np.zeros((datastore.frameheight, datastore.framewidth))
                data_sliced = self.slice_data(datastore, data_temp, data_sliced)

                # JDP add the sliced data to the series array with timestamps in another array
                data_series[:, :, int(i)] = data_sliced
                datastore.timestamps[int(i)] = int(i) * datastore.acqtime
                if self.stupid_verbose:
                    print("Current frame", data_sliced)
                    print("Running series", data_series)

            self.assign_data_to_storage(flag, datastore, data_series)

        if self.stupid_verbose:
            print("Shape of data array: ", np.shape(data))
            print("Data array:", data)

        # JDP in SPE 2.x they don't store the wavelengths as an array, but give you polynomial coefficients
        # JDP for a function that will produce them on a given x axis.
        calib_polyorder = int(self.read_at(binaryfile, 3101, -1, np.int8)[0])

        # JDP get the coefficients and flip them into the right order for np.polyval, which needs them like
        # JDP a,b,c where it's ax^2+bx+c or whatever, +1 on the end because by default numpy doesn't read
        # JDP the stopping point
        calib_polycoeffs = np.flipud(self.read_at(binaryfile, 3263, -1, np.float64)[0:calib_polyorder + 1])

        if self.stupid_verbose:
            print("Calibration coefficients (from highest degree down) are:", calib_polycoeffs)

        # JDP creating an x axis with the width of the frame to evaluate the polynomial over
        # JDP starts at 1 and not 0  (checked with real data)
        wavelength_x = np.arange(1, datastore.framewidth + 1)

        # JDP evaluate the polynomial with coefficients above on this axis to get the wavelength axis
        # JDP i think theres a new polynomial API in numpy now but whatever.
        wavelength_axis = np.polyval(calib_polycoeffs, wavelength_x)

        datastore.xaxis = self.nm_to_cm(wavelength_axis)

        if self.stupid_verbose:
            print("Wavelength axis :", wavelength_axis)

        # JDP this error is more of a warning.
        if np.size(wavelength_axis) != np.size(data[0]):
            print("ERROR, the wavelength axis length is", np.size(wavelength_axis), "elements",
                  "but the data is", np.size(data), "elements.")

        return

    @staticmethod
    def get_window(data, n_base=10, n_dev=2):
        """UNUSED. Get the indices of the reference array where spectral intensity is non-zero.

        It's a bit of a clunkfest and not very reliable.

        NOT IMPLEMENTED IN V1.0"""
        cat = np.concatenate((data[0:n_base], data[-n_base:-1]))
        base = np.mean(cat)
        dev = np.std(cat)
        threshold = base + (n_dev * dev)
        edgestart = int(np.argwhere(data > (base + threshold))[0])
        edgestop = int(np.argwhere(data > (base + threshold))[-1])
        return edgestart, edgestop

    def process_spe3x(self, binaryfile, datastore, flag):
        """Process data from an SPE 3.0 file and put it in the relevant datastore.

        Reads the SPE file at the places defined in the XML footer. The output data is in the shape (
        frameheight, framewidth), so is normally (1, n) for a standard spectrum. Extra dimensions are added
        if the full chip is read out, or if there is more than one frame in the SPE file.

        Most of the options are class attributes and set externally by the GUI and not passed directly.

        ftp://ftp.piacton.com/Public/Manuals/Princeton%20Instruments/SPE%203.0%20File%20Format%20Specification%20Issue%206%20(4411-0140).pdf

        Parameters
        -----------
        binaryfile : binary file object
            The opened .spe file to be processed.
        datastore : SFGDataStore object
            Where the data is stored to.
        flag : str
            Determines where in datastore the data is saved. Possible values "sig", "bg", "ref", "refbg".
        """
        # JDP function for processing SPE 3.0 or later
        # JDP moves to the position of the footer in the binary file, this is described in the manual
        footer_offset_loc = self.read_at(binaryfile, self.footer_offset_loc_loc, -1, np.uint64)[0]
        # JDP reading the position of the XML footer in bytes (varies depending on data size)
        binaryfile.seek(footer_offset_loc)
        xmlfooter = binaryfile.read()

        # JDP creating the two namespaces needed for the useful stuff
        xmlns = '{http://www.princetoninstruments.com/spe/2009}'
        xmlexpns = '{http://www.princetoninstruments.com/experiment/2009}'
        # JDP unpack the xmlfooter into an elementtree object
        xmltree = etree.fromstring(xmlfooter)

        # JDP find the dataformat child within the xmltree (all data is a child of this)
        dataformat = xmltree.find(xmlns+'DataFormat')

        #  DP find the datablock that corresponds to the frame data (all ROIs are children of this) - its
        # the first datablock. This will contain the data we want as we don't normally define multiple
        # regions of interest. Need to test with an accumulate mode file.

        # JDP note to self because this xml is a pain. The frame attributes include the count, pixel format,
        # size, and stride. The ROIs (children of frame) contain the actual widths and heights you need.
        # ROI sizes should add up to frame size. We normally just have one ROI.

        frame = dataformat.find(xmlns + 'DataBlock')

        if self.stupid_verbose:
            print("Attributes of Frame")
            print(frame.attrib)

        # JDP assume that there is only one ROI recorded. More than this would also need fancier processing
        # anyway because it wouldn't fit with the normal class. You could change this relatively easily as
        # the children of frame are just the ROIs.
        regions = frame.findall(xmlns+'DataBlock')
        if len(regions) > 1:
            print("Warning: More than one ROI detected in your data file. This is not yet supported, "
                  "and only the first ROI will be read for processing.")

        roi = regions[0]

        if self.stupid_verbose:
            print("Attributes of the ROI")
            print(roi.attrib)

        datastore.framewidth = int(roi.attrib['width'])
        datastore.frameheight = int(roi.attrib['height'])
        framestride = int(frame.attrib['stride'])
        datastore.numframes = int(frame.attrib['count'])
        pixeltype = frame.attrib['pixelFormat']
        pixeltype_np, pixelsize = self.get_pixel_type(pixeltype)
        npixels = datastore.framewidth * datastore.frameheight
        acqtime = np.float32(xmltree.findall('.//' + xmlexpns + 'ExposureTime')[0].text) / 1000
        self.assign_acqtime_to_storage(flag, datastore, acqtime)
        if self.verbose:
            print("Width of frame is", datastore.framewidth, "pixels.")
            print("Height of frame is", datastore.frameheight, "pixels.")
            print("Number of frames is", datastore.numframes)
            print("Pixel size is", pixelsize, "bytes.")
            print("Frame size is", framestride, "bytes")
            print("Acquisition time per frame is:", datastore.acqtime, "s.")
            print("Total acquisition time is:", datastore.acqtime * datastore.numframes, "s.")

        if datastore.frameheight > 1:
            print("Your data is not in n x 1 format, it will process correctly but the plotting/writing "
                  "may not work as intended.")

        if datastore.numframes > 1 and self.sum_accumulations:
            data = np.zeros((datastore.frameheight, datastore.framewidth))

            for i in range(datastore.numframes):
                data_temp = self.read_at(binaryfile, self.data_offset_loc_loc+(int(i)*framestride),
                                         npixels, pixeltype_np)

                data_sum = np.zeros((datastore.frameheight, datastore.framewidth))
                data_sum = self.slice_data(datastore, data_temp, data_sum)
                data = data + data_sum

                if self.stupid_verbose:
                    print("Current frame", data_temp)
                    print("Running summation", data_sum)

            self.assign_data_to_storage(flag, datastore, data)

        if datastore.numframes > 1 and self.series_accumulations:
            data_series = np.zeros((datastore.frameheight, datastore.framewidth, datastore.numframes))
            datastore.timestamps = np.zeros(datastore.numframes)
            for i in range(datastore.numframes):
                data_temp = self.read_at(binaryfile, self.data_offset_loc_loc+(int(i)*framestride),
                                         npixels, pixeltype_np)
                data_sliced = np.zeros((datastore.frameheight, datastore.framewidth))
                self.slice_data(datastore, data_temp, data_sliced)

                data_series[:, :, int(i)] = data_temp
                datastore.timestamps[int(i)] = int(i) * datastore.acqtime
                if self.stupid_verbose:
                    print("Current frame", data_temp)
                    print("Running series", data_series)

            data = data_series
            self.assign_data_to_storage(flag, datastore, data)

        if datastore.numframes == 1:
            data_temp = self.read_at(binaryfile, self.data_offset_loc_loc, npixels, pixeltype_np)
            data = np.zeros((datastore.frameheight, datastore.framewidth))
            data = self.slice_data(datastore, data_temp, data)
            self.assign_data_to_storage(flag, datastore, data)

        # JDP look through the tree to find the calibration
        calib = xmltree.find(xmlns+'Calibrations')

        # JDP find the part that is the wavelength axis
        wavelength = np.fromstring(calib[0].findall(xmlns+'Wavelength')[0].text, sep=',')

        # JDP this axis covers the whole sensor which isn't necessarily the bit you want for the ROI
        wavelength_leftedge = int(calib[2].attrib['x'])
        wavelength_rightedge = wavelength_leftedge + int(calib[2].attrib['width'])

        # JDP select the portion of the calibration that covers the region you're actually using
        wavelength_axis = wavelength[wavelength_leftedge:wavelength_rightedge]
        datastore.xaxis = self.nm_to_cm(wavelength_axis)
        if self.stupid_verbose:
            print("Size of wavelength axis:", np.shape(wavelength_axis))
            print("Wavelength axis :", wavelength_axis)
            print("Shape of data array: ", np.shape(data))
            print("Data array:", data)

        if np.size(wavelength_axis) != np.size(data[0]):
            print("ERROR, the wavelength axis length is", np.size(wavelength_axis), "elements",
                  "but the data is", np.size(data), "elements.")

        return

    @staticmethod
    def nm_to_cm(data):
        """Convert data from nanometre to wavenumber."""
        data_out = 1.0 / (data * 1.0E-9) * 0.01
        return data_out

    @staticmethod
    def nm_to_thz(data):
        """Convert data from nanometre to terahertz."""
        data_out = (2.997E8 / (data * 1.0E-9)) / 1.0E12
        return data_out

    @staticmethod
    def cm_to_nm(data):
        """Convert data from wavenumber to nanometre."""
        data_out = (1.0 / data) * 1.0E7
        return data_out

    @staticmethod
    def cm_to_thz(data):
        """Convert data from wavenumber to terahertz."""
        data_out = (2.997E8 * 100.0 * data) / 1.0E12
        return data_out

    @staticmethod
    def thz_to_nm(data):
        """Convert data from terahertz to nanometre."""
        data_out = (2.997E8 * 1.0E9 / (data * 1.0E12))
        return data_out

    @staticmethod
    def thz_to_cm(data):
        """Convert data from terahertz to wavenumber."""
        data_out = (data * 1.0E12) / (2.997E8 * 100)
        return data_out

    @staticmethod
    def print_attributes(datastore):
        """Print the attributes of datastore attractively."""

        for attribute in inspect.getmembers(datastore):
            if not attribute[0].startswith('_'):
                if not inspect.ismethod(attribute[1]):
                    print(attribute)

        return

    @staticmethod
    def remove_duplicate_refs(reftabledata):
        """Remove duplicate references from the reftabledata.

        Used to stop the GUI showing as many ref files as signal files after matching and sorting.
        """
        new_ref_table = [[], [], []]
        for i, refid in enumerate(reftabledata[2]):
            if refid not in new_ref_table[2]:
                new_ref_table[0].append(reftabledata[0][i])
                new_ref_table[1].append(reftabledata[1][i])
                new_ref_table[2].append(reftabledata[2][i])

        return new_ref_table

    def update_datatable(self):
        """Update data to be shown in the main datatable with current filenames."""
        self.tabledata = [self.signal_names, self.bg_names, self.sig_ref_num]
        return

    def update_reftable(self, remove_duplicates=False):
        """Update data to be shown in the reference datatable with current filenames."""
        self.reftabledata = [self.ref_names, self.ref_bg_names, self.ref_num]
        if remove_duplicates:
            self.reftabledata = self.remove_duplicate_refs(self.reftabledata)
            print(self.reftabledata)
        return

    def match_files_with_background(self, filenames, bg_filenames, directory):
        """Match each signal file with the appropriate background file.

        First checks if there are any files that have the same name when bg_string is removed. If there are
        then these are defined as the background. If not, then the nearest background file to the signal
        file (in terms of creation time) is chosen.

        Could be updated to include some way of strictly matching polarisations, rather than implicitly as
        here.

        Parameters
        -----------
        filenames : list
            Contains the signal filenames that need to be matched with a background.
        bg_filenames : list
            Contains the background filenames to match with.
        directory : str
            The directory containing the background and signal filenames.

        """
        length = len(filenames)
        bg_list_matched = [None] * length

        for sigindex, sigfile in enumerate(filenames):
            signame = pathlib.Path(sigfile).name
        for bgindex, bgfile in enumerate(bg_filenames):
            bgname = pathlib.Path(bgfile).name
            bgname_nobg = bgname.replace(self.bg_string, '')
            if bgname_nobg == signame:
                bg_list_matched[sigindex] = bgfile

        if None in bg_list_matched:
            for index, bgfile in enumerate(bg_list_matched):
                if bgfile is None:
                    signame = directory + filenames[index]
                    bgs = [directory + bg for bg in bg_filenames]
                    bg_match = self.get_closest_file(bgs, signame)
                    bg_list_matched[index] = str(pathlib.Path(bg_match).name)

        return bg_list_matched

    def match_files_with_reference(self, sig_filenames, ref_filenames, ref_id, directory):
        """Match each signal file with the appropriate reference file.

        As there are generally going to be many more signal files than references, each reference is given
        an ID which is then matched to the signal file. An array containing the refIDs for each signal file
        is returned.

        Finds the closest reference file to the signal file used in terms of creation time.

        Parameters
        -----------
        sig_filenames : list
            Contains the signal filenames that need to be matched with a reference.
        ref_filenames : list
            Contains the reference filenames to match with.
        ref_id : list
            Contains the refID of each reference file
        directory : str
            The directory containing the background and signal filenames.

        Returns
        -----------
        sig_ref_id : list
            Contains the refID of the reference file that each signal file needs to be normalised to.
        """
        sig_ref_id = [None] * len(sig_filenames)
        for index, sigfile in enumerate(sig_filenames):
            signame = directory + sigfile
            refs = [directory + ref for ref in ref_filenames]
            ref_match = self.get_closest_file(refs, signame)
            ref_id_index = ref_filenames.index(str(pathlib.Path(ref_match).name))
            sig_ref_id[index] = ref_id[ref_id_index]

        return sig_ref_id

    @staticmethod
    def create_matched_ref_list(sig_ref_id, ref_filenames, ref_bg_filenames, ref_id):
        """Create lists of the reference files matched to signal files for processing.

        Reads the list sig_ref_id and creates new lists of the same length as the list of signal files
        containing the right reference/reference background files for processing.

        Parameters
        -----------
        sig_ref_id : list
            Contains the refIDs that each signal file needs to be processed with.
        ref_filenames : list
            Contains the reference filenames.
        ref_bg_filenames : list
            Contains the reference background filenames.
        ref_id : list
            Contains the refIDs that each reference file corresponds to.

        Returns
        -----------
        ref_matched : list
            Contains the filenames of the reference files that each signal file needs to be normalised to.
        refbg_matched : list
            Contains the filenames of the reference background files that each signal file needs.
        ref_num : list
            The number of each reference file used (for display in GUI).
        """

        ref_matched = [ref_filenames[ref_id.index(i)] for i in sig_ref_id]
        refbg_matched = [ref_bg_filenames[ref_id.index(i)] for i in sig_ref_id]
        ref_num = [ref_id.index(i)+1 for i in sig_ref_id]

        return ref_matched, refbg_matched, ref_num

    def match_files(self, sig, bg, ref, refbg, refid, directory):
        """Match each signal file with its corresponding reference and background files.

        Calls previously defined methods to populate the lists needed to run data processing.

        To labour the point, the idea is that for processing you need up to four lists of the same length
        containing the file names to be processed. The background/reference/reference background file that
        correspond to element n of the signal list are in element n of their respective lists.

        Parameters
        -----------
        sig : list
            Signal files to be matched to.
        bg : list
            Laoded background files, unmatched.
        ref : list
            Loaded reference files, umatched.
        refbg : list
            Loadaed reference background files, unmatched.
        refid : list
            List of the refIDs that correspond to each reference file.
        directory : str
            Directory where all the data files are located.

        Returns
        -----------
        sig : list
            Signal files to be matched to.
        bg_matched : list
            Background files matched to signal files.
        ref_matched : list
            Reference files matched to signal files.
        refbg_matched : list
            Reference background files matched to signal files.
        sig_ref_id : list
            RefIDs of the reference file each signal file needs.
        ref_num :
            RefIDs of the reference files only.

        """
        bg_matched = self.match_files_with_background(sig, bg, directory)
        ref_bg_temp = self.match_files_with_background(ref, refbg, directory)
        sig_ref_id = self.match_files_with_reference(sig, ref, refid, directory)
        ref_matched, refbg_matched, ref_num = self.create_matched_ref_list(sig_ref_id, ref, ref_bg_temp,
                                                                           refid)

        return sig, bg_matched, ref_matched, refbg_matched, sig_ref_id, ref_num
