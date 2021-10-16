# -*- coding: utf-8 -*-
"""
Created on Thu Sep 30 16:24:45 2021

@author: au538552
"""

import sfgtools as sfgtools
import matplotlib.pyplot as plt


SFGTools = sfgtools.SFGProcessTools()

directory = './examples/'
signal = ['signal_example.spe']
background = ['background_example.spe']
reference = ['reference_example.spe']
reference_bg = ['reference_background_example.spe']

SFGTools.upconversion_line_num = 808
SFGTools.calibration_offset = 15
SFGTools.downconvert_check = True
SFGTools.calibrate_check = True
SFGTools.subtract_check = True
SFGTools.normalise_check = True
SFGTools.exposure_check = True
SFGTools.cosmic_kill_check = False


datastore = SFGTools.SFGDataStore()

SFGTools.read_files( directory+signal[0], datastore, 'sig')
SFGTools.read_files( directory+background[0], datastore, 'bg')
SFGTools.read_files( directory+reference[0], datastore, 'ref')
SFGTools.read_files( directory+reference_bg[0], datastore, 'refbg')

SFGTools.process_data(datastore, SFGTools.downconvert_check, SFGTools.subtract_check, 
                      SFGTools.normalise_check, SFGTools.exposure_check, 
                      SFGTools.calibrate_check, SFGTools.cosmic_kill_check )

SFGTools.custom_region_start = 2800
SFGTools.custom_region_end = 3300
SFGTools.plot_data(datastore, iteration=1, num_files=1, figure=plt.figure() ) 