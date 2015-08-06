# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

#
# LICENSE
#
# Copyright (c) 2015 GEM Foundation
#
# The Catalogue Toolkit is free software: you can redistribute 
# it and/or modify it under the terms of the GNU Affero General Public 
# License as published by the Free Software Foundation, either version 
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# with this download. If not, see <http://www.gnu.org/licenses/>

#!/usr/bin/env/python

"""
Utility functions to support catalogue processing
"""

import os
import numpy as np
from math import fabs
import matplotlib.pyplot as plt

MARKER_NORMAL = np.array([0, 31, 59, 90, 120, 151, 181,
                          212, 243, 273, 304, 334])

MARKER_LEAP = np.array([0, 31, 60, 91, 121, 152, 182, 
                        213, 244, 274, 305, 335])

SECONDS_PER_DAY = 86400.0

def decimal_year(year, month, day):
    """
    Allows to calculate the decimal year for a vector of dates 
    (TODO this is legacy code kept to maintain comparability with previous 
    declustering algorithms!)

    :param year: year column from catalogue matrix
    :type year: numpy.ndarray
    :param month: month column from catalogue matrix
    :type month: numpy.ndarray
    :param day: day column from catalogue matrix
    :type day: numpy.ndarray
    :returns: decimal year column
    :rtype: numpy.ndarray
    """
    marker = np.array([0., 31., 59., 90., 120., 151., 181.,
                                 212., 243., 273., 304., 334.])
    tmonth = (month - 1).astype(int)
    day_count = marker[tmonth] + day - 1.
    dec_year = year + (day_count / 365.)

    return dec_year

def leap_check(year):
    """
    Returns logical array indicating if year is a leap year
    """
    return np.logical_and((year % 4) == 0, 
                          np.logical_or((year % 100 != 0), (year % 400) == 0))

def decimal_time(year, month, day, hour, minute, second):
    """
    Returns the full time as a decimal value
    :param year:
        Year of events (integer numpy.ndarray)
    :param month:
        Month of events (integer numpy.ndarray)
    :param day:
        Days of event (integer numpy.ndarray)
    :param hour:
        Hour of event (integer numpy.ndarray)
    :param minute:
        Minute of event (integer numpy.ndarray)
    :param second:
        Second of event (float numpy.ndarray)
    :returns decimal_time:
        Decimal representation of the time (as numpy.ndarray)
    """
    tmonth = month - 1
    day_count = MARKER_NORMAL[tmonth] + day - 1
    id_leap = leap_check(year)
    leap_loc = np.where(id_leap)[0]
    day_count[leap_loc] = MARKER_LEAP[tmonth[leap_loc]] + day[leap_loc] - 1
    year_secs = (day_count.astype(float) * SECONDS_PER_DAY) +  second + \
        (60. * minute.astype(float)) + (3600. * hour.astype(float))
    decimal_time = year.astype(float) + (year_secs / (365. * 24. * 3600.))
    decimal_time[leap_loc] = year[leap_loc].astype(float) + \
        (year_secs[leap_loc] / (366. * 24. * 3600.))
    return decimal_time


def haversine(lon1, lat1, lon2, lat2, radians=False, earth_rad=6371.227):
    """
    Allows to calculate geographical distance
    using the haversine formula.

    :param lon1: longitude of the first set of locations
    :type lon1: numpy.ndarray
    :param lat1: latitude of the frist set of locations
    :type lat1: numpy.ndarray
    :param lon2: longitude of the second set of locations
    :type lon2: numpy.float64
    :param lat2: latitude of the second set of locations
    :type lat2: numpy.float64
    :keyword radians: states if locations are given in terms of radians
    :type radians: bool
    :keyword earth_rad: radius of the earth in km
    :type earth_rad: float
    :returns: geographical distance in km
    :rtype: numpy.ndarray
    """
    if radians == False:
        cfact = np.pi / 180.
        lon1 = cfact * lon1
        lat1 = cfact * lat1
        lon2 = cfact * lon2
        lat2 = cfact * lat2

    # Number of locations in each set of points
    if not np.shape(lon1):
        nlocs1 = 1
        lon1 = np.array([lon1])
        lat1 = np.array([lat1])
    else:
        nlocs1 = np.max(np.shape(lon1))
    if not np.shape(lon2):
        nlocs2 = 1
        lon2 = np.array([lon2])
        lat2 = np.array([lat2])
    else:
        nlocs2 = np.max(np.shape(lon2))
    # Pre-allocate array
    distance = np.zeros((nlocs1, nlocs2))
    i = 0
    while i < nlocs2:
        # Perform distance calculation
        dlat = lat1 - lat2[i]
        dlon = lon1 - lon2[i]
        aval = (np.sin(dlat / 2.) ** 2.) + (np.cos(lat1) * np.cos(lat2[i]) *
             (np.sin(dlon / 2.) ** 2.))
        distance[:, i] = (2. * earth_rad * np.arctan2(np.sqrt(aval),
                                                    np.sqrt(1 - aval))).T
        i += 1
    return distance


def greg2julian(year, month, day, hour, minute, second):
    """ 
    Function to convert a date from Gregorian to Julian format
    :param year:
        Year of events (integer numpy.ndarray)
    :param month:
        Month of events (integer numpy.ndarray)
    :param day:
        Days of event (integer numpy.ndarray)
    :param hour:
        Hour of event (integer numpy.ndarray)
    :param minute:
        Minute of event (integer numpy.ndarray)
    :param second:
        Second of event (float numpy.ndarray)
    :returns julian_time:
        Julian representation of the time (as float numpy.ndarray)
    """
    year = year.astype(float)
    month = month.astype(float)
    day = day.astype(float)
    
    timeut = hour.astype(float) + (minute.astype(float) / 60.0) + \
        (second / 3600.0)

    julian_time = (367.0 * year) - np.floor(7.0 * (year +
             np.floor((month + 9.0) / 12.0)) / 4.0) - np.floor(3.0 *
             (np.floor((year + (month - 9.0) / 7.0) / 100.0) + 1.0) /
             4.0) + np.floor((275.0 * month) / 9.0) + day +\
             1721028.5 + (timeut / 24.0)
    return julian_time


def piecewise_linear_scalar(params, xval):
    '''Piecewise linear function for a scalar variable xval (float).
    :param params:
        Piecewise linear parameters (numpy.ndarray) in the following form:
        [slope_i,... slope_n, turning_point_i, ..., turning_point_n, intercept]
        Length params === 2 * number_segments, e.g. 
        [slope_1, slope_2, slope_3, turning_point1, turning_point_2, intercept]
    :param xval:
        Value for evaluation of function (float)
    :returns: 
        Piecewise linear function evaluated at point xval (float)
    '''
    n_params = len(params)
    if fabs(float(n_params / 2) - float(n_params) / 2.) > 1E-7:
        raise ValueError(
            'Piecewise Function requires 2 * nsegments parameters')
    
    n_seg = n_params / 2
    
    if n_seg == 1:
        return params[1] + params[0] * xval
    
    gradients = params[0 : n_seg]
    turning_points = params[n_seg: -1]
    c_val = np.array([params[-1]])
    
    for iloc in range(1, n_seg):
        c_val = np.hstack([c_val, (c_val[iloc - 1] + gradients[iloc - 1] * 
            turning_points[iloc - 1]) - (gradients[iloc] *
            turning_points[iloc - 1])])
    
    if xval <= turning_points[0]:
        return gradients[0] * xval + c_val[0]
    elif xval > turning_points[-1]:
        return gradients[-1] * xval + c_val[-1]
    else:
        select = np.nonzero(turning_points <= xval)[0][-1] + 1
    return gradients[select] * xval + c_val[select]

def piecewise_linear(params, xval):
    """
    Implements the piecewise linear analysis function as a vector
    """
    n_params = len(params)
    if fabs(float(n_params / 2) - float(n_params) / 2.) > 1E-7:
        raise ValueError(
            'Piecewise Function requires 2 * nsegments parameters')
    
    n_seg = n_params / 2
    
    if n_seg == 1:
        return params[1] + params[0] * xval
    gradients = params[0 : n_seg]
    turning_points = params[n_seg: -1]
    c_val = params[-1]
    for iloc, slope in enumerate(gradients):
        if iloc == 0:
            yval = (slope * xval) + c_val

        else:
            select = np.where(xval >= turning_points[iloc - 1])[0]
            # Project line back to x = 0
            c_val = c_val - turning_points[iloc - 1] * slope
            yval[select] = (slope * xval[select]) + c_val
        if iloc < (n_seg - 1):
            # If not in last segment then re-adjust intercept to new turning
            # point
            c_val = (slope * turning_points[iloc]) + c_val
    return yval
    
def polynomial(params, xval):
    """
    Returns the polynomial f(xval) where the order is defined by the
    number of params, i.e.
    yval = \SUM_{i=1}^{Num Params} params[i] * (xval ** i - 1)
    """
    yval = np.zeros_like(xval)
    for iloc, param in enumerate(params):
        yval += (param * (xval ** float(iloc)))
    return yval

def exponential(params, xval):
    """
    Returns an exponential function
    """
    assert len(params) == 3
    return np.exp(params[0] + params[1] * xval) + params[2]


def _set_string(value):
    """
    Turns a number into a string prepended with + or - depending on
    whether the number if positive or negative.
    """
    if value >= 0.0:
        return "+ {:.3f}".format(value)
    else:
        return "- {:.3f}".format(value)

def _to_latex(string):
    """
    For a string given in the form XX(YYYY) returns the LaTeX string to
    place bracketed contents as a subscript
    :param 
    """
    lb = string.find("(")
    ub = string.find(")")
    return "$" + string[:lb] + ("_{%s}$" % string[lb+1:ub])


class GeneralFunction(object):
    """
    Class (notionally abstract) for defining the properties of a fitting
    function
    """
    def __init__(self):
        """
        Instantiate
        """
        self.params = []

    def run(self, params, xval):
        """
        Executes the funtion
        :param list params:
            Functon parameters
        :param numpy.ndarray xval:
            Input data
        """
        raise NotImplementedError

    def get_string(self, output_string, input_string):
        """
        Returns a string describing the equation with its final parameters
        :param str output_string:
            Name of output parameter
        :param str input_string:
            Name of input parameter
        """
        raise NotImplementedError


class PiecewiseLinear(GeneralFunction):
    """
    Implements a Piecewise linear functional form with N-segements
    """

    def run(self, params, xval):
        """
        Executes the model
        :param list params:
            Contolling parameters as
            [slope_1, slope_2, ..., slope_i, turning_point1, turning_point2, 
             ..., turning_point_i-1, intercept]
        :param numpy.ndarray xval:
            Input data
        """
        self.params = []
        n_params = len(params)
        if fabs(float(n_params / 2) - float(n_params) / 2.) > 1E-7:
            raise ValueError(
                'Piecewise Function requires 2 * nsegments parameters')
        
        n_seg = n_params / 2
        
        if n_seg == 1:
            return params[1] + params[0] * xval
        gradients = params[0 : n_seg]
        turning_points = params[n_seg: -1]
        c_val = params[-1]
        for iloc, slope in enumerate(gradients):
            if iloc == 0:
                yval = (slope * xval) + c_val
                self.params.append((c_val, slope, turning_points[iloc]))
            else:
                select = np.where(xval >= turning_points[iloc - 1])[0]
                # Project line back to x = 0
                c_val = c_val - turning_points[iloc - 1] * slope
                yval[select] = (slope * xval[select]) + c_val
                if iloc < (n_seg - 1):
                    self.params.append(
                        (c_val, slope, turning_points[iloc - 1]))
                else:
                    # In the last segment
                    self.params.append(
                        (c_val, slope, turning_points[iloc - 1]))
            if iloc < (n_seg - 1):
                # If not in last segment then re-adjust intercept to turning
                # turning point
                c_val = (slope * turning_points[iloc]) + c_val
        
        return yval

    def get_string(self, output_string, input_string):
        """
        Returns the title string
        """
        n_seg = len(self.params)
        full_string = []
        for iloc, params in enumerate(self.params):
            eq_string = "{:s} = {:.3f} {:s} {:s}".format(
                _to_latex(output_string),
                params[0],
                _set_string(params[1]),
                _to_latex(input_string))
            if iloc == 0:
                cond_string = eq_string +  "    for {:s} < {:.3f}".format(
                    _to_latex(input_string),
                    params[2])
            elif iloc == (n_seg - 1):
                cond_string = eq_string + "    for {:s} $\geq$ {:.3f}".format(
                    _to_latex(input_string),
                    params[2])
            else:
                cond_string = eq_string +\
                    "    for {:.3f} $\leq$ {:s} < {:.3f}".format(
                        self.params[iloc - 1][2],
                        _to_latex(input_string),
                        params[2])
            full_string.append(cond_string)
        return "\n".join([case_string for case_string in full_string])
                    
class Polynomial(GeneralFunction):
    """
    Implements a nth-order polynomial function
    """
    def run(self, params, xval):
        """
        Returns the polynomial f(xval) where the order is defined by the
        number of params, i.e.
        yval = \SUM_{i=1}^{Num Params} params[i] * (xval ** i - 1)
        """
        yval = np.zeros_like(xval)
        for iloc, param in enumerate(params):
            yval += (param * (xval ** float(iloc)))
        self.params = params
        return yval

    def get_string(self, output_string, input_string):
        """
        Returns the title string
        """
        base_string = "{:s} = ".format(_to_latex(output_string))
        for iloc, param in enumerate(self.params):
            if iloc == 0:
                base_string = base_string + "{:.3f}".format(param)
            elif iloc == 1:
                base_string = base_string + " {:s}{:s}".format(
                    _set_string(param),
                    _to_latex(input_string))
            else:
                base_string = base_string + (" %s%s$^%d$" %(
                    _set_string(param),
                    _to_latex(input_string),
                    iloc))
        return base_string


class Exponential(GeneralFunction):
    """
    Implements an exponential function of the form y = exp(a + bX) + c
    """
    def run(self, params, xval):
        """
        Returns an exponential function
        """
        assert len(params) == 3
        self.params = params
        return np.exp(params[0] + params[1] * xval) + params[2]

    def get_string(self, output_string, input_string):
        """
        Returns the title string
        """
        base_string = "%s = e$^{(%.3f %s %s)}$ %s" % (
            _to_latex(output_string),
            self.params[0],
            _set_string(self.params[1]),
            self._to_latex(input_string),
            _set_string(self.params[2]))
        return base_string
    
    def _to_latex(self, string):
        """
        For a string given in the form XX(YYYY) returns the LaTeX string to
        place bracketed contents as a subscript
        :param 
        """
        lb = string.find("(")
        ub = string.find(")")
        return string[:lb] + ("_{%s}" % string[lb+1:ub])
                                                  
class TwoSegmentLinear(GeneralFunction):
    """
    Implements a two-segement piecewise linear model with a fixed (i.e. not
    optimisable) corner magnitude
    """
    def __init__(self, corner_magnitude):
        """
        :param float corner_magnitude:
            Corner magnitude
        """
        super(TwoSegmentLinear, self).__init__()
        setattr(self, "corner_magnitude", corner_magnitude)

    def run(self, params, xval):
        """
        Runs the model
        """
        yval = params[0] * xval + params[2]
        cval = params[0] * self.corner_magnitude + params[2]
        cval -= (self.corner_magnitude * params[1])
        idx = xval > self.corner_magnitude
        yval[idx] = cval + params[1] * xval[idx]
        self.params = [[params[0], params[2]], [params[1], cval]]
        return yval

    def get_string(self, output_string, input_string):
        """
        Returns the title string
        """
        base_string = "{:s} = ".format(_to_latex(output_string))
        # Equation 1
        upper_string = base_string +\
            "{:.3f} {:s}{:s}    for {:s} < {:.2f}".format(
                self.params[0][1],
                _set_string(self.params[0][0]),
                _to_latex(input_string),
                _to_latex(input_string),
                self.corner_magnitude)
        lower_string = base_string +\
            "{:.3f} {:s}{:s}    for {:s} $\geq$ {:.2f}".format(
                self.params[1][1],
                _set_string(self.params[1][0]),
                _to_latex(input_string),
                _to_latex(input_string),
                self.corner_magnitude)
        return "\n".join([upper_string, lower_string])
       

function_map = {"piecewise": PiecewiseLinear,
                "polynomial": Polynomial,
                "exponential": Exponential,
                "2segment": TwoSegmentLinear}


def build_filename(filename, filetype='png', resolution=300):
    """
    Uses the input properties to create the string of the filename
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    filevals = os.path.splitext(filename)
    if filevals[1]:
        filetype = filevals[1][1:]
    if not filetype:
        filetype = 'png'

    filename = filevals[0] + '.' + filetype

    if not resolution:
        resolution = 300
    return filename, filetype, resolution

def _save_image(filename, filetype='png', resolution=300):
    """
    If filename is specified, saves the image
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    if filename:
        filename, filetype, resolution = build_filename(filename,
                                                        filetype,
                                                        resolution)
        plt.savefig(filename, dpi=resolution, format=filetype)
    else:
        pass
    return

def _save_image_tight(fig, lgd, filename, filetype='png', resolution=300):
    """
    If filename is specified, saves the image
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    if filename:
        filename, filetype, resolution = build_filename(filename,
                                                        filetype,
                                                        resolution)
        fig.savefig(filename, bbox_extra_artists=(lgd,),
                    bbox_inches="tight", dpi=resolution, format=filetype)
    else:
        pass
    return
