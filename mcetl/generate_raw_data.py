# -*- coding: utf-8 -*-
"""Creates folders and files with simulated data for various characterization techniques

Notes
-----
All data is made up and does not correspond to the materials listed.

@author: Donald Erb
Created on Mon Jun 15 08:38:19 2020

"""

from pathlib import Path

import numpy as np
import pandas as pd
from lmfit import lineshapes
import matplotlib.pyplot as plt
import PySimpleGUI as sg


__all__ = ['generate_raw_data']


def _generate_peaks(x, y, peak_type, params, param_var, **func_kwargs):
    """
    Used to generate peaks with a given variability.

    Parameters
    ----------
    x : array-like
        The x data.
    y : array-like
        The y data (can contain the background and noise).
    peak_type : function
        A peak generating function, which uses x and the items from
        params as the inputs.
    params : list or tuple
        The parameters to create the given peak_type; len(params) is
        how many peaks will be made by the function.
    param_var : list or tuple
        Random variability to add to the parameter; the sigma associated
        with the normal distribution of the random number generator.
    func_kwargs : dict
        Additional keyword arguments to pass to the peak generating function.

    Returns
    -------
    y : array-like
        The y data with the peaks added.

    """

    #to prevent overwriting the input collection objects
    new_params = [param.copy() for param in params]

    for param in new_params:
        for i, value in enumerate(param):
            value = value + param_var[i] * np.random.rand(1)
            param[i] = value

        y += peak_type(x, *param, **func_kwargs)

    return y, new_params


def _generate_XRD_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example XRD data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    This function will create two folders containing the same data
    with different file names, simply to create more files.

    The background is a second order polynomial.
    Peaks are all pseudovoigt.

    Purposes
    --------
    Shows general peak fitting with both peaks and background.

    """

    if num_data % 2 == 1:
        num_data += 1
    x = np.linspace(10, 90, 500)
    background =  0.4 * ((75 - x)**2) #equivalent to 0.4*x^2 - 60*x + 2250
    #[amplitude, center, sigma, fraction]
    params = [
        [3000, 18, 0.3, 0.5],
        [5000, 32, 0.2, 0.5],
        [5000, 36, 1, 0.5],
        [1000, 51, 0.5, 0.5],
        [1500, 65, 0.5, 0.5],
        [600, 80, 0.5, 0.5]
    ]
    param_var = [1000, 1, 1, 0.1]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 10 * np.random.randn(len(x))
        y = background + noise
        data_dict[f'y_{i+1}'], new_params = _generate_peaks(x, y, lineshapes.pvoigt,
                                                            params, param_var)
        param_list.append(new_params)

    data = {'x': x}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)

    fe_path = Path(directory, 'XRD/Fe')
    ti_path = Path(directory, 'XRD/Ti')

    fe_path.mkdir(parents=True, exist_ok=True)
    ti_path.mkdir(parents=True, exist_ok=True)

    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: ', 3: 'Fraction: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n'+'-' * 40 + '\nXRD\n' + '-' * 40)

    plt.figure(num='xrd')
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'Ti-{i}W-700'
            sample_name_2 = f'Fe-{i}W-700'
        else:
            sample_name = f'Ti-{(i-int(num_data / 2))}W-800'
            sample_name_2 = f'Fe-{(i-int(num_data / 2))}W-800'

        data_df.to_csv(Path(ti_path, f'{sample_name}.csv'),
                       columns=['x', f'y_{i+1}'], float_format='%.2f',
                       header=['2theta', 'Counts'], index_label='Number')
         #Same data as as for Ti, just included to make more files
        data_df.to_csv(Path(fe_path, f'{sample_name_2}.csv'),
                       columns=['x', f'y_{i+1}'], float_format='%.2f',
                       header=['2theta', 'Counts'], index_label='Number')
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.4*x^2 - 60*x + 2250\n')
            for j, param in enumerate(param_list[i]):
                f.write(f'\nPeak {j+1}:\nPeak type: pseudovoigt\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('XRD')
    plt.legend(ncol=2)
    plt.xlabel('$2\\theta$ $(\degree)$')
    plt.ylabel('Intensity (a.u.)')
    
    if show_plots:
        plt.show(block=False)
    else:
        plt.close('xrd')


def _generate_FTIR_data(directory, num_data=12, show_plots=True):
    """
    Generates the folders and files containing example FTIR data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    The background is a first order polynomial.
    Peaks are all gaussian.

    Purposes
    --------
    Shows how to manually select points to fit the background.

    """

    if num_data % 2 == 1:
        num_data += 1

    x = np.linspace(500, 4000, 2000)
    background = (- 0.06 / 1500) * x + 0.08 #equivalent to 0.08 - 0.00004*x
    background[x > 2000] = (0.03 / 2000) * x[x > 2000] - 0.03 #equivalent to -0.03 + 0.000015*x

    #[amplitude, center, sigma]
    params = [
        [9, 900, 20],
        [15, 1200, 10],
        [9, 1600, 30],
        [0.9, 2750, 40],
        [6, 2800, 30],
        [1.5, 2850, 30],
        [6, 2900, 30],
        [0.75, 2950, 8],
        [0.75, 3000, 5],
        [15, 3600, 150]
    ]
    param_var = [.200, 0.5, 10]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 0.002 * np.random.randn(len(x))
        y = background + noise
        data_dict[f'y_{i+1}'], new_params = _generate_peaks(x, y, lineshapes.gaussian,
                                                            params, param_var)
        param_list.append(new_params)

    data = {'x': x}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)

    file_path = Path(directory, 'FTIR')
    file_path.mkdir(parents=True, exist_ok=True)
    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nFTIR\n' + '-' * 40)

    plt.figure(num='ftir')
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'PE-{i*10}Ti-Ar'
        else:
            sample_name = f'PE-{(i-int(num_data/2))*10}Ti-Air'

        data_df.to_csv(Path(file_path, f'{sample_name}.csv'),
                       columns=['x', f'y_{i+1}'], float_format='%.2f',
                       header=None, index=False)
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.08 - 0.00004 * x for x <= 2000')
            f.write('\n                    -0.03 + 0.000015 * x for x > 2000\n')
            for j, param in enumerate(param_list[i]):
                f.write(f'\nPeak {j+1}:\nPeak type: gaussian\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('FTIR')
    plt.legend(ncol=2)
    plt.gca().invert_xaxis()
    plt.xlabel('Wavenumber (1/cm)')
    plt.ylabel('Absorbance (a.u.)')

    if show_plots:
        plt.show(block=False)
    else:
        plt.close('ftir')


def _generate_Raman_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example Raman data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    The background is a first order polynomial.
    Two peaks are lorentzian, and two peaks are gaussian.

    Purposes
    --------
    Shows how to fit residual peaks that are not immediately visible.
    Shows how to use Bayesian information criteria to select the optimum
        number of peaks and the optimum peak type.

    """

    if num_data % 2 == 1:
        num_data += 1

    x = np.linspace(200, 2600, 1000)
    background = 0.000001 * x

    #[amplitude, center, sigma]
    params = [[300, 1180, 90], [500, 1500, 80]]
    params2 = [[3000, 1350, 50], [2000, 1590, 40]]
    param_var = [400, 10, 20]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 0.1 * np.random.randn(len(x))
        y = background + noise
        temp_y, gaussian_params = _generate_peaks(x, y, lineshapes.gaussian,
                                                  params, param_var)
        data_dict[f'y_{i+1}'], lorentz_params = _generate_peaks(x, temp_y,
                                                                lineshapes.lorentzian,
                                                                params2, param_var)
        param_list.append(sorted([*gaussian_params, *lorentz_params],
                                 key=lambda x: x[1]))

    data = {'x': x}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)

    file_path = Path(directory, 'Raman')
    file_path.mkdir(parents=True, exist_ok=True)
    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nRaman\n' + '-' * 40)

    plt.figure(num='raman')
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'graphite-{(i+6)*100}C-Ar'
        else:
            sample_name = f'graphite-{(i+6-int(num_data/2))*100}C-Air'

        data_df.to_csv(Path(file_path, f'{sample_name}.txt'),
                       columns=['x', f'y_{i+1}'], float_format='%.2f',
                       header=None, index=False, sep="\t")
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.000001 * x\n')
            for j, param in enumerate(param_list[i]):
                peak_type = 'gaussian' if j % 2 == 0 else 'lorentzian'
                f.write(f'\nPeak {j+1}:\nPeak type: {peak_type}\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('Raman')
    plt.legend(ncol=2)
    plt.xlabel('Raman Shift (1/cm)')
    plt.ylabel('Intensity (a.u.)')
    
    if show_plots:
        plt.show(block=False)
    else:
        plt.close('raman')


def _generate_TGA_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example TGA data

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    Background function is 0.
    Mass losses centered at 200, 400 and 700 degrees C using step functions.

    Simulates a mass loss experiment, going up to a maximum temperature
    and then decreasing.

    Purposes
    --------
    Meant to show how to use the 'max_x' function of a CharacterizationTechnique
    object in excel_gui since only the first set of data where the
    temperature is increasing is wanted for analysis. Alternatively, the heating
    and cooling segments can be separated using the 'segment' column.

    """

    if num_data % 2 == 1:
        num_data += 1

    data_points = 100
    x = np.linspace(20, 1000, data_points)
    background = 0 * x

    #[amplitude, center, sigma]
    params = [[1, 200, 60], [10, 400, 20], [5, 700, 30]]
    param_var = [10, 20, 10]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 0.005 * np.random.randn(len(x))
        y = background + noise
        mass_loss, new_params = _generate_peaks(x, y, lineshapes.step, params,
                                                param_var, **{'form': 'logistic'})
        cooling = noise + mass_loss[-1]
        data_dict[f'y_{i+1}'] = 100 - np.array([*mass_loss, *cooling])
        param_list.append(new_params)

    #adds in the cooling section
    x = np.array([*x, *np.linspace(1000, 20, data_points)])
    time = x / 5
    segment = np.array([*[1] * data_points, *[2] * data_points])

    data = {'x': x, 't': time}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)
    data_df['seg'] = segment

    file_path = Path(directory, 'TGA')
    file_path.mkdir(parents=True, exist_ok=True)
    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nTGA\n' + '-' * 40)

    plt.figure(num='tga')
    filler = 'Text to fill up space\n' + 'filler...\n' * 32
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'graphite-{(i+6)*100}C-Ar'
        else:
            sample_name = f'graphite-{(i+6-int(num_data/2))*100}C-Air'

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f:
            f.write(filler)
        data_df.to_csv(Path(file_path, f'{sample_name}.txt'),
                       columns=['x', 't', f'y_{i+1}', 'seg'], float_format='%.2f',
                       header=['Temperature/degreesC', 'Time/minutes', 'Mass/%',
                               'Segment/#'],
                       index=False, sep=";", mode='a')
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0 * x\n')
            for j, param in enumerate(param_list[i]):
                f.write(f'\nPeak {j+1}:\nPeak type: step\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('TGA')
    plt.legend(ncol=2)
    plt.xlabel('Temperature ($\degree$C)')
    plt.ylabel('Mass (%)')
    
    if show_plots:
        plt.show(block=False)
    else:
        plt.close('tga')


def _generate_DSC_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example DSC data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    Background function is 0.
    Mass losses centered at 200, 400 and 700 degrees C using step functions.

    Simulates a DSC scan for a polymer; on heating, the polymer melts, and then
    it recrystallizes during cooling. No glass transition is shown because
    I am lazy.

    Purposes
    --------
    Shows when 'max_x' is not desirable for a CharacterizationTechnique object
    since both the heating and cooling curves have relavent data.

    Shows that both negative and positive peaks can be fit.

    Shows how to split data by first importing all of the data and saving
    to an Excel file, and then reimporting that data and only choosing
    rows that correspond to either the heating or cooling curves in
    order to do peak fitting. Alternatively, the heating and cooling segments
    can be separated using the 'segment' column.

    """

    if num_data % 2 == 1:
        num_data += 1

    data_points = 100
    x_heating = np.linspace(50, 200, data_points)
    x_cooling = np.linspace(200, 50, data_points)
    background = 0 * x_heating

    #[amplitude, center, sigma]
    params_heating = [[-100, 150, 5]]
    params_cooling = [[100, 100, 5]]
    param_var = [50, 10, 3]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 0.005 * np.random.randn(len(x_heating))
        heating, new_params_heating = _generate_peaks(x_heating, background + noise,
                                                      lineshapes.gaussian,
                                                      params_heating, param_var)
        cooling, new_params_cooling = _generate_peaks(x_cooling, background + noise + 5,
                                                      lineshapes.gaussian,
                                                      params_cooling, param_var)

        data_dict[f'y_{i+1}'] = np.array([*heating, *cooling])
        param_list.append([*new_params_heating, *new_params_cooling])

    #adds in the cooling section
    x = np.array([*x_heating, *x_cooling])
    time = x / 10
    segment = np.array([*[1] * data_points, *[2] * data_points])

    data = {'x': x, 't': time}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)
    data_df['seg'] = segment

    file_path = Path(directory, 'DSC')
    file_path.mkdir(parents=True, exist_ok=True)
    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nDSC\n' + '-' * 40)

    plt.figure(num='dsc')
    filler = 'Text to fill up space\n' + 'filler...\n' * 32
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'PET-{i}Ti'
        else:
            sample_name = f'PET-{i-int(num_data/2)}Fe'

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f:
            f.write(filler)
        data_df.to_csv(Path(file_path, f'{sample_name}.txt'),
                       columns=['x', 't', f'y_{i+1}', 'seg'], float_format='%.2f',
                       header=['Temperature/degreesC', 'Time/minutes',
                               'Heat_Flow_exo_up/(mW/mg)', 'Segment/#'],
                       index=False, sep=";", mode='a')
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0 * x for heating')
            f.write('\n                     5 + 0 * x for cooling\n')
            for j, param in enumerate(param_list[i]):
                f.write(f'\nPeak {j+1}:\nPeak type: gaussian\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('DSC')
    plt.legend(ncol=2)
    plt.xlabel('Temperature ($\degree$C)')
    plt.ylabel('Heat Flow (mW/mg), exotherm up')
    
    if show_plots:
        plt.show(block=False)
    else:
        plt.close('dsc')


def _generate_poresize_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example pore size meansurements.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.

    Notes
    -----
    Background function is 0.
    Peaks centered at 20 and 80 microns using lognormal functions.

    Simulates pore size measurements that would be generated using the
    program ImageJ to analyze scanning electron microscope images of
    macroporous materials.

    Purposes
    --------
    Shows how to use a SummarizingCalculation to perform a calculation on a
    group of files.

    Shows how to split data by first importing all of the data and saving
    to an Excel file, and then reimporting that data and only choosing
    rows that correspond to either the heating or cooling curves in
    order to do peak fitting. Alternatively, the heating and cooling segments
    can be separated using the 'segment' column.

    """

    if num_data % 2 == 1:
        num_data += 1

    data_points = 100
    x_heating = np.linspace(50, 200, data_points)
    x_cooling = np.linspace(200, 50, data_points)
    background = 0 * x_heating

    #[amplitude, center, sigma]
    params_heating = [[-100, 150, 5]]
    params_cooling = [[100, 100, 5]]
    param_var = [50, 10, 3]

    data_dict = {}
    param_list = []
    for i in range(num_data):
        noise = 0.005 * np.random.randn(len(x_heating))
        heating, new_params_heating = _generate_peaks(x_heating, background + noise,
                                                      lineshapes.gaussian,
                                                      params_heating, param_var)
        cooling, new_params_cooling = _generate_peaks(x_cooling, background + noise + 5,
                                                      lineshapes.gaussian,
                                                      params_cooling, param_var)

        data_dict[f'y_{i+1}'] = np.array([*heating, *cooling])
        param_list.append([*new_params_heating, *new_params_cooling])

    #adds in the cooling section
    x = np.array([*x_heating, *x_cooling])
    time = x / 10
    segment = np.array([*[1] * data_points, *[2] * data_points])

    data = {'x': x, 't': time}
    for key in data_dict:
        data[key] = data_dict[key]
    data_df = pd.DataFrame(data)
    data_df['seg'] = segment

    file_path = Path(directory, 'DSC')
    file_path.mkdir(parents=True, exist_ok=True)
    data_keys = {0: 'Area: ', 1: 'Center: ', 2: 'Sigma: '}
    with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nDSC\n' + '-' * 40)

    plt.figure(num='dsc')
    filler = 'Text to fill up space\n' + 'filler...\n' * 32
    for i in range(num_data):
        if i < num_data / 2:
            sample_name = f'PET-{i}Ti'
        else:
            sample_name = f'PET-{i-int(num_data/2)}Fe'

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f:
            f.write(filler)
        data_df.to_csv(Path(file_path, f'{sample_name}.txt'),
                       columns=['x', 't', f'y_{i+1}', 'seg'], float_format='%.2f',
                       header=['Temperature/degreesC', 'Time/minutes',
                               'Heat_Flow_exo_up/(mW/mg)', 'Segment/#'],
                       index=False, sep=";", mode='a')
        plt.plot(x, data_dict[f'y_{i+1}'], label=sample_name)

        with open(directory.joinpath('data peak parameters.txt'), 'a') as f:
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0 * x for heating')
            f.write('\n                     5 + 0 * x for cooling\n')
            for j, param in enumerate(param_list[i]):
                f.write(f'\nPeak {j+1}:\nPeak type: gaussian\n')
                for k, value in enumerate(param):
                    f.write(f'{data_keys[k]}')
                    f.write(f'{value[0]:.4f}\n')

    plt.title('DSC')
    plt.legend(ncol=2)
    plt.xlabel('Temperature ($\degree$C)')
    plt.ylabel('Heat Flow (mW/mg), exotherm up')
    
    if show_plots:
        plt.show(block=False)
    else:
        plt.close('dsc')


def generate_raw_data(directory=None, num_data=6, show_plots=True):
    """
    Generates data for all of the techniques in this file.
    
    Convenience function to generate data for all techniques rather
    that calling the functions one at a time.
    
    Parameters
    ----------
    directory : Path or str
        The file path to the Raw Data folder.
    num_data : int
        The number of files to create.
    show_plots : bool
        If True, will show plots of the created data. If False, will close
        the created figures and not show the plots.
        
    """
    
    #set the random seed so that data is repeatable
    np.random.seed(1)
    data_path = None

    if not directory:
        #layout for window to select where to put the raw data folder
        layout = [
            [sg.Text('Select destination for Raw Data folder', size=(35, 1))],
            [sg.InputText('', disabled=True, text_color='black'),
             sg.FolderBrowse(key='folder')],
            [sg.Button('Submit', bind_return_key=True)]
        ]
    
        window = sg.Window('Folder Selection', layout)
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                values['folder'] = False
                break
            elif event == 'Submit' and values['folder'] == '':
                sg.Popup('Please select a folder.')
            else:
                break
    
        window.close()
        del window, layout

        if values['folder']:
            data_path = Path(values['folder'], 'Raw Data')
    else:
        data_path = Path(directory, 'Raw Data')
    
    if data_path is not None:
        data_path.mkdir(parents=True, exist_ok=True)

        with open(data_path.joinpath('data peak parameters.txt'), 'w') as f:
            f.write('Parameters for all of the data in the Raw Data folder.')
            
        # ensures that plots are not shown until plt.show() is called.
        with plt.rc_context({'interactive': False}):
            #creates all of the data
            _generate_XRD_data(data_path, num_data, show_plots)
            _generate_FTIR_data(data_path, num_data, show_plots)
            _generate_Raman_data(data_path, num_data, show_plots)
            _generate_TGA_data(data_path, num_data, show_plots)
            _generate_DSC_data(data_path, num_data, show_plots)
        

if __name__ == '__main__':

    generate_raw_data(num_data=6)
