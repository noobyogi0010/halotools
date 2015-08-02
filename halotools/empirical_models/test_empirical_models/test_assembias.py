#!/usr/bin/env python

from unittest import TestCase
import pytest
from copy import copy

import numpy as np 
from astropy.table import Table

from ..assembias import HeavisideAssembias, AssembiasZheng07Cens, AssembiasZheng07Sats

from .. import model_defaults
from ..hod_components import Zheng07Cens, Leauthaud11Cens
from ..sfr_components import BinaryGalpropInterpolModel
from ...sim_manager import FakeSim
from ...utils.table_utils import SampleSelector, compute_conditional_percentiles
from ...utils.array_utils import array_like_length as custom_len

class TestAssembias(TestCase):
    """
    """

    def setup_class(self):
        """
        """
        Npts = 1e4
        mass = np.zeros(Npts) + 1e12
        zform = np.linspace(0, 10, Npts)

        d1 = {'halo_mvir': mass, 'halo_zform': zform}
        self.toy_halo_table1 = Table(d1)

        halo_zform_percentile = (np.arange(Npts)+1) / float(Npts)
        halo_zform_percentile = 1. - halo_zform_percentile[::-1]
        d2 = {'halo_mvir': mass, 'halo_zform': zform, 'halo_zform_percentile': halo_zform_percentile}
        self.toy_halo_table2 = Table(d2)

        fakesim = FakeSim()
        self.fake_halo_table = fakesim.halo_table

    def init_test(self, model):

        assert hasattr(model, 'prim_haloprop_key')
        assert hasattr(model, 'sec_haloprop_key')
        assert hasattr(model, '_lower_bound')
        assert hasattr(model, '_upper_bound')

    def baseline_recovery_test(self, model):

        baseline_method = getattr(model, 'baseline_'+model._method_name_to_decorate)
        baseline_result = baseline_method(halo_table = self.toy_halo_table2)

        method = getattr(model, model._method_name_to_decorate)
        result = method(halo_table = self.toy_halo_table2)

        mask = self.toy_halo_table2['halo_zform_percentile'] >= 0.5
        oldmean = result[mask].mean()
        youngmean = result[np.invert(mask)].mean()
        baseline_mean = baseline_result.mean()
        assert oldmean != youngmean
        assert oldmean != baseline_mean
        assert youngmean != baseline_mean 

        split = model.percentile_splitting_function(halo_table = self.toy_halo_table2)
        split = np.where(mask, split, 1-split)
        derived_result = split*oldmean
        derived_result[np.invert(mask)] = split[np.invert(mask)]*youngmean
        derived_mean = derived_result[mask].mean() + derived_result[np.invert(mask)].mean()
        baseline_mean = baseline_result.mean()
        np.testing.assert_allclose(baseline_mean, derived_mean, rtol=1e-3)

    def test_assembias_zheng07_cens(self):
        abz = AssembiasZheng07Cens(sec_haloprop_key = 'halo_zform')

        self.init_test(abz)
        self.baseline_recovery_test(abz)

    def test_assembias_zheng07_sats(self):
        abz = AssembiasZheng07Sats(sec_haloprop_key = 'halo_zform')
        self.init_test(abz)
        self.baseline_recovery_test(abz)














