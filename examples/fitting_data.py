# -*- coding: utf-8 -*-
"""Shows how to use peak_fitting_gui from mcetl.

@author: Donald Erb
Created on Sat Aug 22 17:34:39 2020

"""

import pandas as pd
import matplotlib.pyplot as plt
import PySimpleGUI as sg
from mcetl import utils, peak_fitting_gui


#changes some defaults for the plot formatting
plt.rcParams['font.serif'] = "Times New Roman"
plt.rcParams['font.family'] = "serif"
plt.rcParams['font.size'] = 12
plt.rcParams['mathtext.default'] = "regular"
plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['xtick.minor.visible']=True
plt.rcParams['ytick.minor.visible']=True
plt.rcParams['xtick.major.size'] = 5
plt.rcParams['xtick.major.width'] = 0.6
plt.rcParams['xtick.minor.size'] = 2.5
plt.rcParams['xtick.minor.width'] = 0.6
plt.rcParams['ytick.major.size'] = 5
plt.rcParams['ytick.major.width'] = 0.6
plt.rcParams['ytick.minor.size'] = 2.5
plt.rcParams['ytick.minor.width'] = 0.6
plt.rcParams['lines.linewidth'] = 1.2
plt.rcParams['lines.markersize'] = 5
plt.rcParams['axes.linewidth'] = 0.6
plt.rcParams['legend.frameon'] = False

try:
    num_files = sg.popup_get_text('Enter number of files to open', 'Get Files', '1')
    if num_files:
        dataframes = []
        for _ in range(int(num_files)):
            #gets the values needed to import a datafile, and then imports the data to a dataframe
            import_values = utils.select_file_gui()
            dataframes.extend(
                utils.raw_data_import(import_values, import_values['file'], False)
            )

        #writer used to save fitting results to Excel
        writer = pd.ExcelWriter('temporary file from peak fitting.xlsx',
                                engine='xlsxwriter')

        #loops through the list of dataframes, fits each set of data, and writes the results to Excel
        peak_dfs = []
        params_dfs = []
        descriptors_dfs = []
        fit_results = []
        default_inputs = None
        for dataframe in dataframes:

            fit_output = peak_fitting_gui.fit_dataframe(dataframe, default_inputs)
            fit_results.append(fit_output[0])
            peak_dfs.append(fit_output[1])
            params_dfs.append(fit_output[2])
            descriptors_dfs.append(fit_output[3])
            default_inputs = fit_output[4]

            peak_fitting_gui.fit_to_excel(
                peak_dfs[-1], params_dfs[-1], descriptors_dfs[-1],
                writer, default_inputs['sample_name'], True
            )

        #save the Excel file
        writer.save()

except utils.WindowCloseError:
    pass
except KeyboardInterrupt:
    pass
