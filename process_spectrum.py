# -*- coding: utf-8 -*-
"""
Created on Tues 4 Jan 2022.

Compiles .txt files from nanophoton output into all combinations of multi-probe spectra.
Can compile single or multiple conditions (different analytes, concentrations)

Instructions to use:
    1. Create top-level folder containing all to-be-process txt files
    2. Create folder to store processed CSV files
    3. Change preprocessing conditions
    4. Run code
    5. Select top-level folder for processing
    6. Select folder to store processed CSV files

**Ensure that each probe contains equal number of data for concatenation!!**

"""


import os
import pandas as pd
import tkinter as tk
import numpy as np
from tkinter import filedialog, messagebox
from itertools import combinations
from scipy.sparse import csc_matrix, eye, diags
from scipy.sparse.linalg import spsolve
from scipy.integrate import simps
from scipy.interpolate import interp1d


def _air_pls(x, lambda_=100, porder=1, itermax=15):
    """
    Adaptive iteratively reweighted penalized least squares for baseline fitting

    input
        x: input data (i.e. chromatogram of spectrum)
        lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background, z
        porder: adaptive iteratively reweighted penalized least squares for baseline fitting

    output
        the fitted background vector
    """
    m = x.shape[0]
    w = np.ones(m)
    for i in range(1, itermax + 1):
        z = _whittaker_smooth(x, w, lambda_, porder)
        d = x - z
        dssn = np.abs(d[d < 0].sum())
        if (dssn < 0.001 * (abs(x)).sum() or i == itermax):
            # if (i == itermax):
                # print('WARING max iteration reached!')
            break
        w[d >= 0] = 0  # d>0 means that this point is part of a peak, so its weight is set to 0 in order to ignore it
        w[d < 0] = np.exp(i * np.abs(d[d < 0]) / dssn)
        w[0] = np.exp(i * (d[d < 0]).max() / dssn)
        w[-1] = w[0]
    return z


def _whittaker_smooth(x, w, lambda_, differences=1):
    """
    Penalized least squares algorithm for background fitting

    input
        x: input data (i.e. chromatogram of spectrum)
        w: binary masks (value of the mask is zero if a point belongs to peaks and one otherwise)
        lambda_: parameter that can be adjusted by user. The larger lambda is,  the smoother the resulting background
        differences: integer indicating the order of the difference of penalties

    output
        the fitted background vector
    """
    X = np.matrix(x)
    m = X.size
    E = eye(m, format='csc')
    D = E[1:] - E[:-1]  # numpy.diff() does not work with sparse matrix. This is a workaround.
    W = diags(w, 0, shape=(m, m))
    A = csc_matrix(W + (lambda_ * D.T * D))
    B = csc_matrix(W * X.T)
    background = spsolve(A, B)
    return np.array(background)


def baseline(data):
    """
    Baselines data.
    Currently includes airPLS only.
    :param data: single scan of data (dtype: numpy array)
    :return: baselined data (dtype: numpy array)
    """
    baseline_data = data - _air_pls(data)
    return baseline_data


def preprocessing(calibrated_data, normalize_minmax, normalize_area, first_wn_norm, last_wn_norm, start_wn, end_wn):
    """
    Preprocessing module after data calibration.
    Currently includes SMOOTHING, BASELINE, NORM, VARIABLE ALIGNMENT, TRIMMING.
    :param calibrated_data: single scan of calibrated data (dtype: numpy array)
    :return: processed data (dtype: numpy array)
    """
    baseline_data = baseline(calibrated_data)  # baseline
    if normalize_area:
        area_selected = simps(baseline_data[first_wn_norm-start_wn:last_wn_norm-start_wn], dx=1)
        norm_baseline_data = baseline_data / np.array(area_selected)  # normalise
        area_spectra = simps(norm_baseline_data[[first_wn_norm-start_wn, last_wn_norm-start_wn]], dx=1)        
    elif normalize_minmax:
        norm_baseline_data = baseline_data / np.amax(baseline_data)
    else:
        norm_baseline_data = baseline_data

    processed_data = norm_baseline_data

    return processed_data


def process_spectrum(input_path, output_path, trim, start_wn, end_wn, normalize_minmax, normalize_area):

    # input_path = 1
    # output_path = 1
    # normalize_area = False # Toggle for simple normalization
    # normalize_minmax = True #only one type of normalization can be True
    # trim = True
    # start_wn = 400
    # end_wn = 1800
    #trim_range = [start_wn, end_wn]
    first_wn_norm = 1400
    last_wn_norm = 1485 #change these variables to determine the range of normalization
    
    for root, dirs, files in os.walk(os.path.normpath(input_path)):
        # print("1." + root)
        if not dirs:
            sample_count = 0
            master_data = {}
            master_keys = []
            
            for file in files:
                # print(file)
                if '.txt' in file:
                    processed_data={}
                    filepath = os.path.join(root, file)
                    # print('Progress: %i/%i' % (sample_count+1, len(files)))
                    sample_count += 1
                    
                    # Reading each txt file
                    data_obj = pd.read_csv(filepath, sep="\t", comment='#')
                    filename = file.split('.')[0]
                    master_keys.append(filename)
                     
                    # Drop repeated x columns
                    drop_col = [col for col in data_obj.columns if 'wn(' in col]
                    data_obj.drop(columns=drop_col[1:], inplace=True)
                    data_obj = data_obj.iloc[:, :]
                    
                    # Trimming data
                    if trim:
                        data_obj_trim = data_obj[data_obj[drop_col[0]].between(start_wn-1, end_wn+1)]
                        data_obj_trim.reset_index(drop=True, inplace=True)
                        data_obj_trim_wn = data_obj_trim.iloc[:,0]
                        data_obj_trim_spectra = data_obj_trim.iloc[:,1:]

                    for i in range(0, len(data_obj_trim.T)-1):
                        #Interpolate
                        spectra = data_obj_trim_spectra.iloc[:,i]
                        spectra_name = str(data_obj_trim_spectra.columns.values[i])
                        f = interp1d(data_obj_trim_wn, spectra, kind='cubic', fill_value="extrapolate")
                        # f = interp1d(data_obj_trim_wn, spectra, kind='cubic')
                        new_wn = np.arange(start_wn, end_wn+1, 1)
                        spectra_interp = f(new_wn)
                        #Baseline correction
                        pp_spectra = preprocessing(spectra_interp, normalize_minmax, normalize_area, first_wn_norm, last_wn_norm, start_wn, end_wn)
                        processed_data[spectra_name] = pp_spectra    
                    
                    master_data[filename] = processed_data
    
                    # Create save pathway
                    savename = file.split('.')[0]
                    savepath = os.path.join(output_path, savename)
                    
                    processed_data_df = pd.DataFrame(processed_data.values(), index=processed_data.keys(), columns = new_wn)
                    processed_data_df.to_csv(savepath + '.csv')
