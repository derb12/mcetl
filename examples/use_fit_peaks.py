# -*- coding: utf-8 -*-
"""Shows how to use fit_peaks from mcetl.

Easier to use launch_fitting_gui from mcetl.fitting, but this is another
way to fit peaks using mcetl.

@author: Donald Erb
Created on Aug 22, 2020

"""

import time

import lmfit
import matplotlib.pyplot as plt
from mcetl import fitting
from mcetl.fitting import peak_fitting
import numpy as np


# create raw data
x_array = np.linspace(0, 60, 100)
background = 0.1 * x_array
noise = 0.1 * np.random.randn(len(x_array))
peaks = lmfit.lineshapes.gaussian(x_array, 30, 15, 5) + lmfit.lineshapes.gaussian(x_array, 50, 35, 3)
y_array = background + noise + peaks

# inputs for peak_fitting function
rel_height = 0
prominence = np.inf
center_offset = 10
peak_width = 10
x_min = 5
x_max = 55
additional_peaks = [2, 10, 36]
subtract_background=True
model_list = []
min_method = 'least_squares'
background_type = 'PolynomialModel'
background_kwargs = {'degree': 1}
default_model='Gaussian'
fit_kws = {}
vary_Voigt=False
fit_residuals=True
num_resid_fits=5
min_resid = 0.1
debug=True
bkg_min = 45

# options for plotting data after fitting
plot_data_wo_background=False
plot_data_w_background=True
plot_data_separatebackground=False
plot_fit_result=True
plot_CI=True
n_sig = 3
plot_peaks=True
plot_initial=False

time0 = time.time()

fitting_results = fitting.fit_peaks(
    x_array, y_array, height=rel_height, prominence=prominence,
    center_offset=center_offset, peak_width=peak_width, model_list=model_list,
    subtract_background=subtract_background, x_min=x_min, x_max=x_max,
    additional_peaks=additional_peaks, background_type=background_type,
    background_kwargs=background_kwargs, min_method=min_method,
    default_model=default_model, fit_kws=fit_kws, vary_Voigt=vary_Voigt,
    fit_residuals=fit_residuals, num_resid_fits=num_resid_fits,
    min_resid=min_resid, debug=debug, bkg_min=bkg_min
)

print('\n\n'+'-'*8+f' {time.time()-time0:.1f} seconds '+'-'*8)

# unpacks all of the data from the output of the plugNchug_fit function
output_list = [fitting_results[key] for key in fitting_results]
resid_found, resid_accept, peaks_found, peaks_accept, initial_fit, fit_results, individual_peaks, best_values = output_list
fit_result = fit_results[-1]
individual_peaks = individual_peaks[-1]
best_values = best_values[-1]

domain_mask = (x_array > x_min) & (x_array < x_max)
x_array = x_array[domain_mask]
y_array = y_array[domain_mask]

#Plot the peaks found or added, as well as if they were used in the fitting
if plot_peaks:
    peak_fitting.plot_peaks_for_model(x_array, y_array, x_min, x_max, peaks_found,
                                      peaks_accept, additional_peaks)

#Plot the initial model used for fitting
if plot_initial:
    plt.figure()
    plt.plot(x_array, y_array, 'o', initial_fit[0].userkws['x'], initial_fit[0], ms=2)
    plt.legend(['data', 'initial guess'])
    plt.show(block=False)

#Plot the best fit and residuals
if plot_fit_result:
    fitting.plot_fit_results(fit_results, True, True)

#Plots individual peaks from the fitting
peak_fitting.plot_individual_peaks(
    fit_result, individual_peaks, subtract_background,
    plot_data_wo_background, plot_data_separatebackground,
    plot_data_w_background
)

#Plot the data, fit, and the fit +- n_sig*sigma confidence intervals
if plot_CI:
    fitting.plot_confidence_intervals(fit_result, n_sig)

print('\n\n', fit_result.fit_report(min_correl=0.5))

# Ensures program will not end until all plots are closed
if plt.get_fignums():
    plt.show(block=True)
