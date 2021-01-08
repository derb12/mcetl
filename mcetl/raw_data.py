# -*- coding: utf-8 -*-
"""Creates folders and files with simulated data for various characterization techniques

Notes
-----
All data is made up and does not correspond to the materials listed.
The data is meant to simply emulate real data and allow for basic analysis.

@author: Donald Erb
Created on Jun 15, 2020

"""

from pathlib import Path

from lmfit import lineshapes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import PySimpleGUI as sg

from . import utils


__all__ = ['generate_raw_data']

_PARAMETER_FILE = 'raw data parameters.txt'


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
    new_params : list
        The actual parameter values after applying the given variability.

    Notes
    -----
    Uses np.random.rand to only use random values in the range [0, 1). This
    was a mistake, and np.random.randn was supposed to be used, but the parameter
    values and variability are already optimized for use with np.random.rand, so
    there is no reason to change anything since it works.

    """

    # to prevent overwriting the input collection objects
    new_params = [param.copy() for param in params]
    for param in new_params:
        for i, value in enumerate(param):
            param[i] = value + param_var[i] * np.random.rand(1)

        y += peak_type(x, *param, **func_kwargs)

    return y, new_params


def _generate_XRD_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example XRD data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    This function will create two folders containing the same data
    with different file names, simply to create more files.

    The background is a second order polynomial.
    Peaks are all pseudovoigt.

    """

    fe_path = Path(directory, 'XRD/Fe')
    ti_path = Path(directory, 'XRD/Ti')
    fe_path.mkdir(parents=True, exist_ok=True)
    ti_path.mkdir(parents=True, exist_ok=True)

    x = np.linspace(10, 90, 500)
    background =  0.4 * ((75 - x)**2) # equivalent to 0.4*x^2 - 60*x + 2250
    # [amplitude, center, sigma, fraction]
    params = [
        [3000, 18, 0.3, 0.5],
        [5000, 32, 0.2, 0.5],
        [5000, 36, 1, 0.5],
        [1000, 51, 0.5, 0.5],
        [1500, 65, 0.5, 0.5],
        [600, 80, 0.5, 0.5]
    ]
    param_var = [1000, 1, 1, 0.1]

    plt.figure(num='xrd')
    param_dict = {}
    data = {'x': x}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'Ti-{i}W-700'
            sample_name_2 = f'Fe-{i}W-700'
        else:
            sample_name = f'Ti-{(i - int(np.ceil(num_data / 2)))}W-800'
            sample_name_2 = f'Fe-{(i - int(np.ceil(num_data / 2)))}W-800'

        noise = 10 * np.random.randn(x.size)
        data['y'], new_params  = _generate_peaks(
            x, background + noise, lineshapes.pvoigt, params, param_var
        )
        param_dict[sample_name] = new_params
        param_dict[sample_name_2] = new_params

        data_df = pd.DataFrame(data)
        data_df.to_csv(Path(ti_path, f'{sample_name}.csv'),
                       columns=['x', 'y'], float_format='%.2f',
                       header=['2theta', 'Counts'], index_label='Number')
        # Same data as as for Ti, just included to make more files
        data_df.to_csv(Path(fe_path, f'{sample_name_2}.csv'),
                       columns=['x', 'y'], float_format='%.2f',
                       header=['2theta', 'Counts'], index_label='Number')
        plt.plot(data['x'], data['y'], label=sample_name)

    param_keys = ('Area', 'Center', 'Sigma', 'Fraction')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n'+'-' * 40 + '\nXRD\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.4*x^2 - 60*x + 2250\n')
            for j, param in enumerate(param_values):
                f.write(f'\nPeak {j + 1}:\nPeak type: pseudovoigt\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{value[0]:.4f}\n')

    if not show_plots:
        plt.close('xrd')
    else:
        plt.title('XRD')
        plt.legend(ncol=2)
        plt.xlabel(r'$2\theta$ $(\degree)$')
        plt.ylabel('Intensity (a.u.)')
        plt.show(block=False)


def _generate_FTIR_data(directory, num_data=12, show_plots=True):
    """
    Generates the folders and files containing example FTIR data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    The background is a first order polynomial.
    Peaks are all gaussian.

    """

    file_path = Path(directory, 'FTIR')
    file_path.mkdir(parents=True, exist_ok=True)

    x = np.linspace(500, 4000, 2000)
    background = (- 0.06 / 1500) * x + 0.08 # equivalent to 0.08 - 0.00004*x
    background[x > 2000] = (0.03 / 2000) * x[x > 2000] - 0.03 # equivalent to -0.03 + 0.000015*x

    # [amplitude, center, sigma]
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
    param_var = [0.2, 0.5, 10]

    plt.figure(num='ftir')
    param_dict = {}
    data = {'x': x}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'PE-{i * 10}Ti-Ar'
        else:
            sample_name = f'PE-{(i - int(np.ceil(num_data / 2))) * 10}Ti-Air'

        noise = 0.002 * np.random.randn(x.size)
        data['y'], param_dict[sample_name]  = _generate_peaks(
            x, background + noise, lineshapes.gaussian, params, param_var
        )

        pd.DataFrame(data).to_csv(
            Path(file_path, f'{sample_name}.csv'),
            columns=['x', 'y'], float_format='%.2f',
            header=None, index=False
        )
        plt.plot(data['x'], data['y'], label=sample_name)

    param_keys = ('Area', 'Center', 'Sigma')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nFTIR\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.08 - 0.00004 * x for x <= 2000')
            f.write('\n                    -0.03 + 0.000015 * x for x > 2000\n')
            for j, param in enumerate(param_values):
                f.write(f'\nPeak {j + 1}:\nPeak type: gaussian\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{value[0]:.4f}\n')

    if not show_plots:
        plt.close('ftir')
    else:
        plt.title('FTIR')
        plt.legend(ncol=2)
        plt.gca().invert_xaxis()
        plt.xlabel('Wavenumber (1/cm)')
        plt.ylabel('Absorbance (a.u.)')
        plt.show(block=False)


def _generate_Raman_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example Raman data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    The background is a first order polynomial.
    Two peaks are lorentzian, and two peaks are gaussian.

    """

    file_path = Path(directory, 'Raman')
    file_path.mkdir(parents=True, exist_ok=True)

    x = np.linspace(200, 2600, 1000)
    background = 0.000001 * x

    # [amplitude, center, sigma]
    params = [[300, 1180, 90], [500, 1500, 80]]
    params_2 = [[3000, 1350, 50], [2000, 1590, 40]]
    param_var = [400, 10, 20]

    plt.figure(num='raman')
    param_dict = {}
    data = {'x': x}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'graphite-{(i + 6) * 100}C-Ar'
        else:
            sample_name = f'graphite-{(i + 6 - int(np.ceil(num_data / 2))) * 100}C-Air'

        noise = 0.1 * np.random.randn(x.size)
        temp_y, gaussian_params = _generate_peaks(
            x, background + noise, lineshapes.gaussian, params, param_var
        )
        data['y'], lorentz_params = _generate_peaks(
            x, temp_y, lineshapes.lorentzian, params_2, param_var
        )
        param_dict[sample_name] = sorted([*gaussian_params, *lorentz_params],
                                         key=lambda x: x[1])

        pd.DataFrame(data).to_csv(
            Path(file_path, f'{sample_name}.txt'),
            columns=['x', 'y'], float_format='%.2f',
            header=None, index=False, sep="\t"
        )
        plt.plot(data['x'], data['y'], label=sample_name)

    param_keys = ('Area', 'Center', 'Sigma')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nRaman\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0.000001 * x\n')
            for j, param in enumerate(param_values):
                peak_type = 'gaussian' if j % 2 == 0 else 'lorentzian'
                f.write(f'\nPeak {j + 1}:\nPeak type: {peak_type}\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{value[0]:.4f}\n')

    if not show_plots:
        plt.close('raman')
    else:
        plt.title('Raman')
        plt.legend(ncol=2)
        plt.xlabel('Raman Shift (1/cm)')
        plt.ylabel('Intensity (a.u.)')
        plt.show(block=False)


def _generate_TGA_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example TGA data

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    Background function is 0.
    Mass losses centered at 200, 400 and 700 degrees C using step functions.

    Simulates a mass loss experiment, going up to a maximum temperature
    and then decreasing.

    """

    file_path = Path(directory, 'TGA')
    file_path.mkdir(parents=True, exist_ok=True)

    x = np.linspace(20, 1000, 100)
    background = 0 * x
    x_full = np.hstack((x, x[::-1])) # adds in the cooling section
    time = x_full / 5 # heating rate of 5 degrees C / minute
    segments = np.hstack((np.full(x.size, 1), np.full(x.size, 2)))

    # [amplitude, center, sigma]
    params = [[1, 200, 60], [10, 400, 20], [5, 700, 30]]
    param_var = [10, 20, 10]

    plt.figure(num='tga')
    param_dict = {}
    data = {'x': x_full, 't': time, 'seg': segments}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'graphite-{(i + 6) * 100}C-Ar'
        else:
            sample_name = f'graphite-{(i + 6 - int(np.ceil(num_data / 2))) * 100}C-Air'

        noise = 0.005 * np.random.randn(x.size)
        mass_loss, param_dict[sample_name] = _generate_peaks(
            x, background + noise, lineshapes.step, params, param_var, **{'form': 'logistic'}
        )
        cooling = noise + mass_loss[-1]
        data['y'] = 100 - np.hstack((mass_loss, cooling))

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f:
            f.write('Text to fill up space\n' + 'filler...\n' * 32) # filler text
        pd.DataFrame(data).to_csv(
            Path(file_path, f'{sample_name}.txt'),
            columns=['x', 't', 'y', 'seg'], float_format='%.2f',
            header=['Temperature/degreesC', 'Time/minutes', 'Mass/%', 'Segment/#'],
            index=False, sep=";", mode='a'
        )
        plt.plot(data['x'], data['y'], label=sample_name)

    param_keys = ('Area', 'Center', 'Sigma')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nTGA\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0 * x\n')
            for j, param in enumerate(param_values):
                f.write(f'\nPeak {j + 1}:\nPeak type: step\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{value[0]:.4f}\n')

    if not show_plots:
        plt.close('tga')
    else:
        plt.title('TGA')
        plt.legend(ncol=2)
        plt.xlabel(r'Temperature ($\degree$C)')
        plt.ylabel('Mass (%)')
        plt.show(block=False)


def _generate_DSC_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example DSC data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    Background function is 0 during heating, 5 during cooling.
    Peak centered at 150 during heating and 100 during cooling; using step function.

    Simulates a DSC scan for a polymer; on heating, the polymer melts, and then
    it recrystallizes during cooling. No glass transition is shown because
    I am lazy.

    """

    file_path = Path(directory, 'DSC')
    file_path.mkdir(parents=True, exist_ok=True)

    x_heating = np.linspace(50, 200, 100)
    x_cooling = x_heating[::-1]
    background = 0 * x_heating
    x_full = np.hstack((x_heating, x_cooling))
    time = x_full / 10 # heating rate of 10 degrees C / minute
    segments = np.hstack((np.full(x_heating.size, 1), np.full(x_cooling.size, 2)))

    # [amplitude, center, sigma]
    params_heating = [[-100, 150, 5]]
    params_cooling = [[100, 100, 5]]
    param_var = [50, 10, 3]

    plt.figure(num='dsc')
    param_dict = {}
    data = {'x': x_full, 't': time, 'seg': segments}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'PET-{i}Ti'
        else:
            sample_name = f'PET-{i - int(np.ceil(num_data / 2))}Fe'

        noise = 0.005 * np.random.randn(x_heating.size)
        heating, new_params_heating = _generate_peaks(
            x_heating, background + noise, lineshapes.gaussian,
            params_heating, param_var
        )
        cooling, new_params_cooling = _generate_peaks(
            x_cooling, background + noise + 5, lineshapes.gaussian,
            params_cooling, param_var
        )
        data['y'] = np.hstack((heating, cooling))
        param_dict[sample_name] = [*new_params_heating, *new_params_cooling]

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f:
            f.write('Text to fill up space\n' + 'filler...\n' * 32) # filler text
        pd.DataFrame(data).to_csv(
            Path(file_path, f'{sample_name}.txt'),
            columns=['x', 't', 'y', 'seg'], float_format='%.2f',
            header=['Temperature/degreesC', 'Time/minutes',
                    'Heat_Flow_exo_up/(mW/mg)', 'Segment/#'],
            index=False, sep=";", mode='a'
        )
        plt.plot(data['x'], data['y'], label=sample_name)

    param_keys = ('Area', 'Center', 'Sigma')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nDSC\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write('\nBackground function: 0 * x for heating')
            f.write('\n                     5 + 0 * x for cooling\n')
            for j, param in enumerate(param_values):
                f.write(f'\nPeak {j + 1}:\nPeak type: gaussian\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{value[0]:.4f}\n')

    if not show_plots:
        plt.close('dsc')
    else:
        plt.title('DSC')
        plt.legend(ncol=2)
        plt.xlabel(r'Temperature ($\degree$C)')
        plt.ylabel('Heat Flow (mW/mg), exotherm up')
        plt.show(block=False)


def _generate_pore_size_data(directory, num_data=6, show_plots=True):
    """
    Generates the folders and files containing example pore size meansurements.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    Peaks centered at 20 and 60 microns using randomly sampled lognormal functions.

    The area and perimeter are not directly computed by the diameter because the
    shapes are not perfect circles.

    Simulates pore size measurements that would be generated using the
    program ImageJ to analyze scanning electron microscope images of
    macroporous materials.

    """

    file_path = Path(directory, 'Pore Size Analysis')
    file_path.mkdir(parents=True, exist_ok=True)

    plt.figure(num='pores')
    param_dict = {}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample = f'Fe-{i}Ti-700C'
        else:
            sample = f'Fe-{i - int(np.ceil(num_data / 2))}Co-700C'

        # Generate three measurements per sample
        sample_path = file_path.joinpath(sample)
        sample_path.mkdir(parents=True, exist_ok=True)
        for j in range(1, 4):
            sample_name = sample + f'_region-{j}'

            mean_1 = 20 + np.random.randn(1) * 5
            sigma_1 = 0.3 + np.random.randn(1) * 0.01
            mean_2 = 60 + np.random.randn(1) * 5
            sigma_2 = 0.2 + np.random.randn(1) * 0.01
            ratio = abs(3 + np.random.randn(1) * 1)

            diameters = np.hstack((
                np.random.lognormal(np.log(mean_1), sigma_1, int(100 * ratio)),
                np.random.lognormal(np.log(mean_2), sigma_2, 100)
            ))
            # area and perimeter are not directly related to diameters because pores are not perfect circles
            # image area is always less than the area from the feret diameter
            areas = (np.pi / 4) * (diameters * (1 - np.abs((np.random.randn(diameters.size) / 5))))**2
            perimeters = np.pi * (diameters * (1 + (np.random.randn(diameters.size) / 10)))

            data = {
                'number': np.arange(1, diameters.size + 1, 1),
                'area': areas,
                'perimeter': perimeters,
                'circularity': np.minimum(1, 4 * np.pi * (areas / (perimeters**2))),
                'diameters': diameters,
            }
            param_dict[sample_name] = (
                (int(100 * ratio), mean_1, np.log(mean_1), sigma_1),
                (100, mean_2, np.log(mean_2), sigma_2),
            )

            pd.DataFrame(data).to_csv(
                Path(sample_path, f'{sample_name}.csv'),
                float_format='%.3f', index=False, sep=",",
                header=['Number', 'Area (microns^2)', 'Perimeter (microns)',
                        'Circularity', 'Feret Diameter (microns)']
            )

            counts, bins = np.histogram(diameters, np.arange(-5, 125, 5))
            plt.plot(bins[1:], counts, 'o-', label=sample_name)

    param_keys = ('Total Count', 'Center', 'log(Center)', 'Sigma')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nPore Size Analysis\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            for j, param in enumerate(param_values):
                f.write(f'\nPeak {j + 1}:\nPeak type: lognormal\n')
                for k, value in enumerate(param):
                    f.write(f'{param_keys[k]}: ')
                    f.write(f'{float(value):.4f}\n')

    plt.title('Pore Size Analysis')
    plt.legend(ncol=2)
    plt.xlabel(r'Pore Size ($\mu$m)')
    plt.ylabel('Count (#)')

    if show_plots:
        plt.show(block=False)
    else:
        plt.close('pores')


def _generate_uniaxial_tensile_data(directory, num_data=6, show_plots=True):
    """
    Generates the folder and files containing example stress-strain measurements.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    Simulates a stress-strain curve for a material with a elastic modulus
    of ~70 GPa, yield stress of ~500 MPa, ultimate strength of ~550 MPa, and
    elongation at failure of ~15 %.

    Creates three measurements for each sample.

    The curve is simulated using stress = strain * elastic modulus for
    stress < yield stress, and stress = ultimate strength - mult * (strain - ultimate strain)^2,
    where mult is just a multiplicative factor used to get a good looking curvature
    for the data. The second equation is just an estimate for the strengthening and necking
    section of the stress-strain curve.

    A more accurate empirical function would be a power law, but the used function
    is good enough.

    """

    file_path = Path(directory, 'Tensile Test')
    file_path.mkdir(parents=True, exist_ok=True)

    strain_rate_1 = 0.00025 # 1/s, for 0 < strain <= 2% strain
    strain_rate_2 = 0.0067 # 1/s, for 2% < strain <= fracture
    mult = 8e9 # affects the curvature of the strengthening/necking region

    plt.figure(num='tensile')
    param_dict = {}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample = f'Al-{i}Ti'
        else:
            sample = f'Al-{i - int(np.ceil(num_data / 2))}Fe'

        # Generate three measurements per sample
        sample_path = file_path.joinpath(sample)
        sample_path.mkdir(parents=True, exist_ok=True)
        for j in range(1, 4):
            sample_name = sample + f'_test-{j}'

            fracture_strain = float(0.15 + np.random.randn(1) * 0.01)
            modulus = (70 + np.random.randn(1) * 5) * 1e9
            yield_stress = (500 + np.random.randn(1) * 10) * 1e6
            yield_strain = yield_stress / modulus
            ultimate_strength = (550 + np.random.randn(1) * 10) * 1e6
            # calculate strain at ultimate strength such that the two curves meet perfectly at the yield stress and strain
            # ie: E * strain = sigma_u - mult * (strain - strain_u)^2 when strain = yield strain
            ultimate_strain = ((mult * yield_strain) + np.sqrt(-mult * yield_strain * modulus + (mult * ultimate_strength))) / mult

            # measure every 0.2 seconds
            strain = np.hstack((
                np.linspace(0, 0.02, num=5 * int(0.02 / strain_rate_1)),
                np.linspace(0.02, fracture_strain + 0.005, num=5 * int((fracture_strain + 0.005) / strain_rate_2))[1:]
            ))
            # empirical approximation for the curve during hardening and necking
            second_func = ultimate_strength - (mult * (strain - ultimate_strain)**2)

            stress = modulus * strain
            stress[strain < 0.001] = stress[strain < 0.001] / 4 # slippage during experiment start
            stress[stress > yield_stress] = second_func[stress > yield_stress] # after yield
            stress[strain > fracture_strain] = 0 # failure
            stress += 0.5e6 * np.random.randn(stress.size) # measurement error

            data = {
                'time': np.linspace(0, 0.2 * (strain.size - 1), strain.size),
                'extension': strain * 80, # initial length = 80 mm
                'load': np.pi * (4.5 / 1000)**2 * stress / 1000, # diameter = 9 mm, load in kN
                'stress': stress / 1e6,
                'strain': strain * 100
            }
            param_dict[sample_name] = (
                modulus / 1e9, yield_stress / 1e6, ultimate_strength / 1e6, fracture_strain
            )

            with open(Path(sample_path, f'{sample_name}.txt'), 'w') as f: # filler text
                f.write('""\n')
                f.write('"Test Method", "uniaxial test.msm"\n')
                f.write(f'"Sample I.D.", "{sample_name}"\n')
                f.write('"Initial Dimensions", "Diameter (mm)", "9", "Gauge Length (mm)", "80"\n\n')
                f.write('"Time (s)", "Extension (mm)", "Load (kN)", "Stress (MPa)", "Strain (%)"\n\n')

            pd.DataFrame(data).to_csv(
                Path(sample_path, f'{sample_name}.txt'),
                columns=['time', 'extension', 'load', 'stress', 'strain'],
                float_format='%.3f', index=False, sep=",", mode='a', header=None
            )
            plt.plot(100 * strain, stress / 1e6, label=sample_name)

    param_keys = ('Elastic Modulus (GPa)', 'Yield Stress (MPa)',
                  'Ultimate Strength (MPa)', 'Fracture Strain (mm/mm)')
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nTensile Test\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            for k, value in enumerate(param_values):
                f.write(f'\n{param_keys[k]}: ')
                f.write(f'{float(value):.4f}')

    if not show_plots:
        plt.close('tensile')
    else:
        plt.title('Tensile Test')
        plt.legend(ncol=2)
        plt.xlabel('Strain (%)')
        plt.ylabel('Stress (MPa)')
        plt.show(block=False)


def _generate_rheometry_data(directory, num_data=6, show_plots=True):
    """
    Generates the folder and files containing example rheometry data.

    Parameters
    ----------
    directory : Path
        The file path to the Raw Data folder.
    num_data : int, optional
        The number of files to create.
    show_plots : bool, optional
        If True, will show a plot of the data.

    Notes
    -----
    Simulates the viscosity measurements for a shear-thinning polymer melt
    which obeys the Carreau-Yasuda model, in which the measured viscosity, mu, follows:
        mu = mu_inf + (mu_0 - mu_inf) * (1 + (lambda * shear_rate)**a)**((n - 1) / a)
    where mu_inf is the viscosity at infinite shear rate, mu_0 is the viscosity
    at zero shear rate, lambda is the relaxation time, n is the power law index
    (n - 1 is the slope of the line in the region between mu_0 and mu_inf),
    and a is a dimensionless parameter (will be equal to 2 for this data).

    """

    file_path = Path(directory, 'Rheometry')
    file_path.mkdir(parents=True, exist_ok=True)

    shear_rate = np.logspace(-1, 3, num=30) # from 0.1 to 1000 1/s, evenly spaced on log scale

    plt.figure(num='rheometry')
    param_dict = {}
    for i in range(num_data if not num_data % 2 else num_data + 1):
        if i < num_data / 2:
            sample_name = f'PDMS-{i}Ti'
        else:
            sample_name = f'PDMS-{i - int(np.ceil(num_data / 2))}Fe'

        mu_0 = 0.9 + np.random.randn(1) * 0.2
        mu_inf = 0.1 + np.random.randn(1) * 0.01
        lambda_ = abs(1 + np.random.randn(1) * 0.1)
        n = abs(0.3 + np.random.randn(1) * 0.1)

        viscosity = mu_inf + (mu_0 - mu_inf) * (1 + (lambda_ * shear_rate)**2)**((n - 1) / 2)
        viscosity +=  np.random.randn(viscosity.size) * viscosity / 20 # measurement error

        data = {
            'shear stress': shear_rate * viscosity,
            'shear rate': shear_rate,
            'viscosity': viscosity,
            'time': np.linspace(40, 40 * shear_rate.size, shear_rate.size) + np.random.randn(shear_rate.size),
            'temperature': np.full(shear_rate.size, 25),
            'normal stress': -250 + np.random.randn(shear_rate.size)
        }
        param_dict[sample_name] = [mu_0, mu_inf, lambda_, n, 2]

        with open(Path(file_path, f'{sample_name}.txt'), 'w') as f: # filler text
            f.write('Text to fill up space, data starts on line 166\n' + 'filler...\n' * 164)
            f.write('shear stress\tshear rate\tviscosity\ttime\ttemperature\tnormal stress\n')
            f.write('Pa\t1/s\tPa.s\ts\t\u00b0C\tPa\n\n')

        pd.DataFrame(data).to_csv(
            Path(file_path, f'{sample_name}.txt'),
            float_format='%.3f', index=False, sep="\t", mode='a', header=None
        )
        plt.plot(shear_rate, viscosity, 'o-', label=sample_name)

    param_keys = (
        'mu_0 (Pa*s)', 'mu_infinity (Pa*s)', 'lambda (s)',
        'power law index, n (unitless)', 'a, dimensionless-parameter (unitless)'
    )
    with open(directory.joinpath(_PARAMETER_FILE), 'a') as f:
        f.write('\n\n' + '-' * 40 + '\nRheometry\n' + '-' * 40)
        for sample_name, param_values in param_dict.items():
            f.write(f'\n\nData for {sample_name}\n' + '-' * 20)
            f.write(f'\nModel: Carreau-Yasuda model\n')
            for k, value in enumerate(param_values):
                f.write(f'\n{param_keys[k]}: ')
                f.write(f'{float(value):.4f}')

    if not show_plots:
        plt.close('rheometry')
    else:
        plt.title('Rheometry')
        plt.legend(ncol=2)
        plt.xlabel('Shear Rate (1/s)')
        plt.ylabel(r'Dynamic Viscosity (Pa$\cdot$s)')
        plt.gca().set_xscale('log')
        plt.gca().set_yscale('log')
        plt.show(block=False)


def generate_raw_data(directory=None, num_files=None, show_plots=False):
    """
    Generates data for all of the techniques in this file.

    Convenience function to generate data for all techniques rather
    that calling the functions one at a time.

    Parameters
    ----------
    directory : str, optional
        The file path to place the Raw Data folder.
    num_files : int, optional
        The number of files to create per characterization technique.
    show_plots : bool, optional
        If True, will show plots of the created data. If False (default),
        will close the created figures and not show the plots.

    Notes
    -----
    Currently supported characterization techniques include:
        XRD, FTIR, Raman, TGA, DSC, Rheometry, Uniaxial tensile test,
        Pore Size Analysis

    """

    function_mapping = {
        'XRD': _generate_XRD_data,
        'FTIR': _generate_FTIR_data,
        'Raman': _generate_Raman_data,
        'TGA': _generate_TGA_data,
        'DSC': _generate_DSC_data,
        'Rheometry': _generate_rheometry_data,
        'Uniaxial Tensile Test': _generate_uniaxial_tensile_data,
        'Pore Size Analysis': _generate_pore_size_data
    }

    validations = {
        'strings': [['folder', 'Raw Data folder']],
        'integers' : [['num_files', 'number of files']],
        'constraints': [['num_files', 'number of files', '> 0']]
    }

    layout = [
        [sg.Text('Select destination for Raw Data folder')],
        [sg.Input(directory if directory is not None else '', key='folder',
                  size=(35, 1), disabled=True, text_color='black'),
         sg.FolderBrowse(key='browse', target='folder')],
        [sg.Text('Number of files per characterization technique:'),
         sg.Input(num_files if num_files is not None else 6,
                  key='num_files', size=(5, 1))],
        [sg.Text('')],
        [sg.Text('Choose the techniques to generate data for:')],
        [sg.Listbox(list(function_mapping), select_mode='multiple',
                    key='selected_functions', size=(25, 5)),
         sg.Button('Select\nAll', key='all_techniques', size=(10, 4))],
        [sg.Text('')],
        [sg.Button('Submit', bind_return_key=True, button_color=utils.PROCEED_COLOR),
         sg.Check('Show Plots', show_plots, key='show_plots')]
    ]

    try:
        window = sg.Window('Raw Data Generation', layout)
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                utils.safely_close_window(window)

            elif event == 'all_techniques':
                window['selected_functions'].update(
                    set_to_index=list(range(len(function_mapping)))
                )

            elif event == 'Submit':
                if utils.validate_inputs(values, **validations):
                    if values['selected_functions']:
                        break
                    else:
                        sg.popup('Please select a characterization technique.\n',
                                 title='Error')

    except (utils.WindowCloseError, KeyboardInterrupt):
        pass

    else:
        window.close()
        del window

        data_path = Path(values['folder'], 'Raw Data')
        data_path.mkdir(parents=True, exist_ok=True)

        if not data_path.joinpath(_PARAMETER_FILE).exists():
            with open(data_path.joinpath(_PARAMETER_FILE), 'w') as f:
                f.write('Parameters for all of the data in the Raw Data folder.')

        np.random.seed(1) # Set the random seed so that data is repeatable
        # Ensures that plots are not shown until plt.show() is called.
        with plt.rc_context({'interactive': False}):
            for function in values['selected_functions']:
                function_mapping[function](
                    data_path, values['num_files'], values['show_plots']
                )
