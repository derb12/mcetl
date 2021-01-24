# -*- coding: utf-8 -*-
"""Provides additional models for fitting data.

@author  : Donald Erb
Created on Nov 29, 2020

"""


import lmfit
import numpy as np


def breit_wigner_fano_alt(x, height=1.0, center=0.0, sigma=1.0, q=-3.0):
    """
    An alternate Breit-Wigner-Fano lineshape that uses height rather than amplitude.

    breit_wigner_fano(x, height, center, sigma, q) =
        height * (1 + (x - center) / (q * sigma))**2 / (1 + ((x - center) / sigma)**2)

    """

    return height * (1 + (x - center) / (q * sigma))**2 / (1 + ((x - center) / sigma)**2)


class BreitWignerFanoModel(lmfit.model.Model):
    """
    A modified version of lmfit's BreitWignerModel.

    Initializes with q=-3 rather than q=1, which gives a better peak.
    Also defines terms for fwhm, height, x_mode, and maximum that were
    not included in lmfit's implementation, where x_mode is the x position
    at the maximum y-value, and maximum is the maximum y-value. Further,
    the lmfit implementation uses amplitude as value for bwf as abs(x)
    approaches infinity, which is different than for most other peaks
    where amplitude is defined as the peak area.

    Compared to lmfit's implementation, height = amplitude * q**2, and
    sigma (this model) = sigma (lmfit) / 2.

    """

    def __init__(self, independent_vars=['x'], prefix='', nan_policy='raise', **kwargs):
        kwargs.update({'prefix': prefix, 'nan_policy': nan_policy,
                       'independent_vars': independent_vars})
        super().__init__(breit_wigner_fano_alt, **kwargs)
        self._set_paramhints_prefix()


    def _set_paramhints_prefix(self):
        self.set_param_hint('sigma', min=0.0)
        self.set_param_hint(
            'fwhm',
            expr=f'2 * {self.prefix}sigma * (1 + {self.prefix}q**2) / max({lmfit.models.tiny}, abs(-1 + {self.prefix}q**2))')
        self.set_param_hint('mode', expr=f'UNDEFINED if {self.prefix}q == 0 else {self.prefix}center + {self.prefix}sigma/(2*{self.prefix}q)')
        self.set_param_hint('extremum', expr=f'{self.prefix}height * (1 + 1 / max({lmfit.models.tiny}, {self.prefix}q**2))')


    def guess(self, data, x=None, negative=False, **kwargs):
        """Estimate initial model parameter values from data."""

        if x is not None:
            pars = lmfit.models.guess_from_peak(self, data, x, negative)
            y = np.array(data)[np.argsort(x)]
            sign = -1 if abs(y[0]) > abs(y[-1]) else 1
        else:
            pars = self.make_params()
            sign = -1

        q = 3 * sign
        center = pars[f'{self.prefix}center'].value - pars[f'{self.prefix}sigma'].value / q
        pars[f'{self.prefix}center'].set(value=center)
        pars[f'{self.prefix}q'].set(value=q)
        pars[f'{self.prefix}height'].set(value=min(data) if negative else max(data))

        return lmfit.models.update_param_vals(pars, self.prefix, **kwargs)
