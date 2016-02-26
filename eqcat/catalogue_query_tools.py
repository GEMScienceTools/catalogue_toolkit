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
Collection of Catalogue Database Query Tools
"""
import h5py
import numpy as np
import pandas as pd
from copy import copy, deepcopy
from datetime import datetime, date, time
from collections import OrderedDict
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LogNorm
import eqcat.utils as utils
from matplotlib.path import Path
from scipy import odr
from eqcat.isf_catalogue import (Magnitude, Location, Origin,
                                 Event, ISFCatalogue)

try:
    from mpl_toolkits.basemap import Basemap
except:
    print "Basemap not installed or unavailable!"
    print "Catalogue Plotting Functions will not work"

# RESET Axes tick labels
matplotlib.rc("xtick", labelsize=14)
matplotlib.rc("ytick", labelsize=14)
# Switch to Type 1 fonts
matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42
matplotlib.rcParams["ps.useafm"] = True

class CatalogueDB(object):
    """
    Holder class for the catalogue database
    """
    def __init__(self, filename=None):
        """
        Instantiate the class. If a filename is supplied this will load the
        data from the file
        :param str filename:
            Path to input file
        """
        self.filename = filename
        self.origins = []
        self.magnitudes = []
        self.number_origins = None
        self.number_magnitudes = None
        self.load_data_from_file()

    def load_data_from_file(self):
        """
        If a filename is specified then will import data from file
        """
        if self.filename:
            self.origins = pd.read_hdf(self.filename, "catalogue/origins")
            self.magnitudes = pd.read_hdf(self.filename,
                                          "catalogue/magnitudes")
            _ = self._get_number_origins_magnitudes()
        else:
            pass

    def _get_number_origins_magnitudes(self):
        """
        Returns the number of origins and the number of magnitudes
        """
        self.number_origins = len(self.origins) 
        self.number_magnitudes = len(self.magnitudes)
        return self.number_origins, self.number_magnitudes

    def export_current_selection(self, output_file):
        """
        Exports the current selection to file   
        """
        store = pd.HDFStore(output_file)
        store.append("catalogue/origins", self.origins)
        store.append("catalogue/magnitudes", self.magnitudes)
        store.close()

    def build_isf(self, identifier, name):
        """
        Creates an instance of the ISFCatalogue class from the hdf5 format
        :param str identifier:
            Identifier string of the ISFCatalogue object
        :param str name:
            Name for the ISFCatalogue object
        :returns:
            Catalogue as instance of :class: ISFCatalogue  
        """
        isf_catalogue = ISFCatalogue(identifier, name)
        event_groups = self.origins.groupby("eventID")
        mag_groups = self.magnitudes.groupby("eventID")
        mag_keys = mag_groups.indices.keys()
        ngrps = len(event_groups)
        for iloc, grp in enumerate(event_groups):
            if (iloc % 1000) == 0:
                print "Processing event %d of %d" % (iloc, ngrps)
            # Get magnitudes list
            if grp[0] in mag_keys:
                # Magnitudes associated to this origin
                mag_list = self._get_magnitude_classes(
                    mag_groups.get_group(grp[0]))
            else:
                mag_list = []
            # Get origins
            origin_list = self._get_origin_classes(grp[1], mag_list)
            event = Event(grp[0], origin_list, mag_list)
            isf_catalogue.events.append(event)
        return isf_catalogue


    def _get_origin_classes(self, orig_group, mag_list):
        """
        Gets the Origin class representation for a particular event
        :param orig_group:
            Pandas Group object
        :param list:
            List of :class: Magnitude objects
        """
        origin_list = []
        norig = orig_group.shape[0]
        for iloc in range(0, norig):
            # Get location
            location = Location(orig_group.originID.values[iloc],
                                orig_group.longitude.values[iloc],
                                orig_group.latitude.values[iloc],
                                orig_group.depth.values[iloc],
                                orig_group.semimajor90.values[iloc],
                                orig_group.semiminor90.values[iloc],
                                orig_group.error_strike.values[iloc],
                                orig_group.depth_error.values[iloc])
            # origin
            orig_date = date(orig_group.year.values[iloc],
                             orig_group.month.values[iloc],
                             orig_group.day.values[iloc])
            micro_seconds = (orig_group.second.values[iloc] -
                np.floor(orig_group.second.values[iloc])) * 1.0E6
            seconds = int(orig_group.second.values[iloc])
            if seconds > 59:
                seconds = 0
                minute_inc = 1
            else:
                minute_inc = 0
            orig_time = time(orig_group.hour.values[iloc],
                             orig_group.minute.values[iloc] + minute_inc,
                             seconds,
                             int(micro_seconds))
            origin = Origin(orig_group.originID.values[iloc],
                            orig_date,
                            orig_time,
                            location,
                            orig_group.Agency.values[iloc],
                            is_prime=bool(orig_group.prime.values[iloc]),
                            time_error = orig_group.time_error.values[iloc])
            for mag in mag_list:
                if mag.origin_id == origin.id:
                    origin.magnitudes.append(mag)
            origin_list.append(origin)
        return origin_list
                               
    def _get_magnitude_classes(self, mag_group):
        """
        For a given event, returns the list of magnitudes
        :param mag_group:
            Group of magnitudes for a given event as instance of Pandas
            Group object
        """
        mag_list = []
        nmags = mag_group.shape[0]
        for iloc in range(0, nmags):
            mag = Magnitude(mag_group.eventID.values[iloc],
                            mag_group.originID.values[iloc],
                            mag_group.value.values[iloc],
                            mag_group.magAgency.values[iloc],
                            mag_group.magType.values[iloc],
                            mag_group.sigma.values[iloc])
            mag.magnitude_id = mag_group.magnitudeID.values[iloc]
            mag_list.append(mag)
        return mag_list


class CatalogueSelector(object):
    """
    Tool to select sub-sets of the catalogue
    """
    def __init__(self, catalogue, create_copy=True):
        """

        """
        self.catalogue = catalogue
        self.copycat = create_copy

    def _select_by_origins(self, idx, select_type="any"):
        """
        Returns a catalogue selected from the original catalogue by
        origin
        :param idx:
            Pandas Series object indicating the truth of an array
        """
        if select_type == "any":
            valid_origins = self.catalogue.origins.eventID[idx]
            event_list = valid_origins.unique()

        elif select_type == "all":
            self.catalogue.origins["idx"] = idx
            origin_cat = pd.DataFrame({
                "eventID": self.catalogue.origins.eventID[idx],
                "idx": idx[idx]})
            grps = origin_cat.groupby("eventID")
            original_grps = self.catalogue.origins.groupby("eventID")
            event_list = []
            for key in grps.groups.keys():
                if np.all(original_grps.get_group(key)["idx"].values):
                    event_list.append(key)
            event_list = np.array(event_list)
            del self.catalogue.origins["idx"]
        else:
            raise ValueError(
                "Selection Type must correspond to 'any' or 'all'")
        
        select_idx1 = self.catalogue.origins.eventID.isin(event_list)
        select_idx2 = self.catalogue.magnitudes.eventID.isin(event_list)
        if self.copycat:
            output_catalogue = CatalogueDB()
            output_catalogue.origins = self.catalogue.origins[select_idx1]
            output_catalogue.magnitudes =\
                self.catalogue.magnitudes[select_idx2]
            _ = output_catalogue._get_number_origins_magnitudes
        else:
            self.catalogue.origins = self.catalogue.origins[select_idx1]
            self.catalogue.magnitudes = self.catalogue.magnitudes[select_idx2]
        return output_catalogue
            
    def _select_by_magnitudes(self, idx, select_type="any"):
        """
        Returns a catalogue selected from the original catalogue by
        magnitude
        :param idx:
            Pandas Series object indicating the truth of an array
        """
        if select_type == "any":
            valid_mags = self.catalogue.magnitudes.eventID[idx]
            event_list = valid_mags.unique()
        elif select_type == "all":
            self.catalogue.magnitudes["idx"] = idx
            mag_cat = pd.DataFrame({
                "eventID": self.catalogue.origins.eventID[idx],
                "idx": idx[idx]})
            grps = mag_cat.groupby("eventID")
            mag_grps = self.catalogue.magnitudes.groupby("eventID")
            event_list = []
            for key in grps.groups.keys():
                if np.all(mag_grps.get_group(key)["idx"].values):
                    event_list.append(key)
            event_list = np.array(event_list)
            del self.catalogue.magnitudes["idx"]
        else:
            raise ValueError(
                "Selection Type must correspond to 'any' or 'all'")
            
        select_idx1 = self.catalogue.magnitudes.eventID.isin(event_list)
        select_idx2 = self.catalogue.origins.eventID.isin(event_list)
        if self.copycat:
            output_catalogue = CatalogueDB()
            output_catalogue.magnitudes =\
                self.catalogue.magnitudes[select_idx1]
            output_catalogue.origins = self.catalogue.origins[select_idx2]
            _ = output_catalogue._get_number_origins_magnitudes
        else:
            self.catalogue.magnitudes = self.catalogue.magnitude[select_idx1]
            self.catalogue.origins = self.catalogue.origins[select_idx2]
        return output_catalogue
    
    def select_by_agency(self, agency, select_type="any"):
        """
        Selects by agency type
        """
        idx = self.catalogue.origins.Agency == agency
        return self._select_by_origins(idx, select_type)

    def limit_to_agency(self, agency, mag_agency=None):
        """
        Limits the catalogue to just those origins and magnitudes reported by
        the specific agency
        """
        if not mag_agency:
            mag_agency = agency
        select_idx1 = self.catalogue.magnitudes.magAgency == mag_agency
        select_idx2 = self.catalogue.origins.Agency == agency
        if self.copycat:
            output_catalogue = CatalogueDB()
            output_catalogue.magnitudes =\
                self.catalogue.magnitudes[select_idx1]
            output_catalogue.origins = self.catalogue.origins[select_idx2]
            _ = output_catalogue._get_number_origins_magnitudes
        else:
            self.catalogue.magnitudes = self.catalogue.magnitude[select_idx1]
            self.catalogue.origins = self.catalogue.origins[select_idx2]
        return output_catalogue

    def select_within_depth_range(self, upper_depth=None, lower_depth=None,
            select_type="any"):
        """
        Selects within a depth range
        """
        if not upper_depth:
            upper_depth = 0.0
        if not lower_depth:
            lower_depth = np.inf
        idx = (self.catalogue.origins["depth"] >= upper_depth) &\
            (self.catalogue.origins["depth"] <= lower_depth) &\
            (self.catalogue.origins["depth"].notnull())
        
        #idx[np.logical_not(np.isnan(self.catalogue.origins["depth"]))] = False
        #idix[np.isnan(self.catalogue.origins["depth"])]
        return self._select_by_origins(idx, select_type)

    def select_within_magnitude_range(self, lower_mag=None, upper_mag=None,
            select_type="any"):
        """
        Selects within a magnitude range
        """
        if not lower_mag:
            lower_mag = -np.inf
        if not upper_mag:
            upper_mag = np.inf
        idx = (self.catalogue.magnitudes["value"] >= lower_mag) &\
            (self.catalogue.magnitudes["value"] <= upper_mag)
        return self._select_by_magnitudes(idx, select_type)

    def select_within_polygon(self, poly_lons, poly_lats, select_type="any"):
        """
        Select within a polygon
        """
        polypath = Path(np.column_stack([poly_lons, poly_lats]))
        idx = pd.Series(polypath.contains_points(np.column_stack([
            self.catalogue.origins["longitude"].values,
            self.catalogue.origins["latitude"].values])))
        idx = idx & self.catalogue.origins["depth"].notnull()
        return self._select_by_origins(idx, select_type)

    def select_within_bounding_box(self, bounds, select_type="any"):
        """
        Selects within a bounding box
        """
        llon = bounds[0]
        ulon = bounds[2]
        llat = bounds[1]
        ulat = bounds[3]
        bbox = np.array([[llon, ulat],
                         [ulon, ulat],
                         [ulon, llat],
                         [llon, llat]])
        return self.select_within_polygon(bbox[:, 0], bbox[:, 1], select_type)

    
    def select_within_date_range(self, start_date=None, end_date=None,
                                 select_type="any"):
        """
        Selects within a date[years] range
        """
        if not start_date:
            start_date = 0
        if not end_date:
            end_date = 2015
        idx = (self.catalogue.origins["year"] >= start_date) &\
            (self.catalogue.origins["year"] <= end_date)
        return self._select_by_origins(idx, select_type)



def get_agency_origin_count(catalogue):
    """
    Returs a list of tuples of the agecny and the number of origins per
    agency
    """
    agency_count = catalogue.origins["Agency"].value_counts()
    count_list = []
    agency_list = agency_count.keys()
    for iloc in range(0, len(agency_count)):
        count_list.append((agency_list[iloc], agency_count[iloc]))
    return count_list


def get_agency_magnitude_count(catalogue):
    """
    Returs a list of tuples of the agency and the number of magnitudes per
    agency
    """
    agency_count = catalogue.magnitudes["magAgency"].value_counts()
    count_list = []
    agency_list = agency_count.keys()
    for iloc in range(0, len(agency_count)):
        count_list.append((agency_list[iloc], agency_count[iloc]))
    return count_list


def get_agency_magtype_statistics(catalogue, pretty_print=True):
    """
    Returns an analysis of the number of different magnitude types found for
    each agency
    """
    agency_count = get_agency_origin_count(catalogue)
    mag_group = catalogue.magnitudes.groupby("magAgency")
    mag_group_keys = mag_group.groups.keys()
    output = []
    for agency, n_origins in agency_count:

        print "Agency: %s - %d Origins" % (agency, n_origins)
        if not agency in mag_group_keys:
            print "No magnitudes corresponding to this agency"
            print "".join(["=" for iloc in range(0, 40)])
            continue

        grp1 = mag_group.get_group(agency)
        mag_counts = grp1["magType"].value_counts()
        mag_counts = mag_counts.iteritems()
        if pretty_print:
            print "%s" % " | ".join(["{:s} ({:d})".format(val[0], val[1])
                                     for val in mag_counts])
            print "".join(["=" for iloc in range(0, 40)])
        agency_dict = {"Origins": n_origins, "Magnitudes": dict(mag_counts)}
        output.append((agency, agency_dict))
    return OrderedDict(output)
    

def get_agency_magtype_statistics_with_agency_code(catalogue, agency_dict = None, pretty_print=True):
    """
    Returns an analysis of the number of different magnitude types found for
    each agency
    """
    agency_count = get_agency_origin_count(catalogue)
    mag_group = catalogue.magnitudes.groupby("magAgency")
    mag_group_keys = mag_group.groups.keys()
    output = []
    agency_name = []
    agency_country = []
    agency_codes = agency_dict
    
    
    for agency, n_origins in agency_count:
        for key, value in sorted(agency_codes.iteritems()):
               if key == agency:
                  agency_name = value.get('name')
                  agency_country = value.get('country')
        print "Agency: %s - %s - %s " % (agency, agency_name, agency_country)
        print "Origins: %d " % (n_origins)
    
        if not agency in mag_group_keys:
            print "No magnitudes corresponding to this agency"
            print "".join(["=" for iloc in range(0, 40)])
            continue

        grp1 = mag_group.get_group(agency)
        mag_counts = grp1["magType"].value_counts()
        mag_counts = mag_counts.iteritems()
        if pretty_print:
            print "%s" % " | ".join(["{:s} ({:d})".format(val[0], val[1])
                                     for val in mag_counts])
            print "".join(["=" for iloc in range(0, 40)])
        agency_dict = {"Origins": n_origins, "Magnitudes": dict(mag_counts)}
        output.append((agency, agency_dict))
    return OrderedDict(output)

            
def get_agency_magnitude_pairs(catalogue, pair1, pair2, no_case=False):
    """
    Returns a set of vectors corresponding to the common magnitudes
    recorded by an (Agency, Magnitude Type) pair.
    :params catalogue:
        Instance of the CatalogueDB class
    :params tuple pair1:
        Agency and magnitude combination (Agency, Magnitude Type) for defining
        the independent variable
    :params tuple pair2:
        Agency and magnitude combination (Agency, Magnitude Type) for defining
        the dependent variable
    :params bool no_case:
        Makes the selection case sensitive (True) or ignore case (False)
    """
    if no_case:
        case1_select = (
            catalogue.magnitudes["magAgency"].str.lower() == pair1[0].lower()
            ) &\
            (catalogue.magnitudes["magType"].str.lower() == pair1[1].lower())
        case2_select = (
            catalogue.magnitudes["magAgency"].str.lower() == pair2[0].lower()
            ) &\
            (catalogue.magnitudes["magType"].str.lower() == pair2[1].lower())
    else:
        case1_select = (catalogue.magnitudes["magAgency"] == pair1[0]) &\
            (catalogue.magnitudes["magType"] == pair1[1])
        case2_select = (catalogue.magnitudes["magAgency"] == pair2[0]) &\
            (catalogue.magnitudes["magType"] == pair2[1])
    
    if not np.any(case1_select):
        print "Agency-Pair: (%s, %s) returned no magnitudes" %(pair1[0],
                                                               pair1[1])
        return None, None
    if not np.any(case2_select):
        print "Agency-Pair: (%s, %s) returned no magnitudes" %(pair2[0],
                                                               pair2[1])
        return None, None
    select_cat1 = catalogue.magnitudes[case1_select]
    select_cat2 = catalogue.magnitudes[case2_select]
    # See if any eventIDs in the second catalogues are in the first
    idx = select_cat2.eventID.isin(select_cat1.eventID)
    num_events = np.sum(idx)
    if np.any(idx):
        print "Agency-Pairs: (%s, %s) & (%s, %s) returned %d events" % (
            pair1[0], pair1[1], pair2[0], pair2[1], np.sum(idx))
    
    else:
        # No common events
        print "Agency-Pairs: (%s, %s) & (%s, %s) returned 0 events" % (
            pair1[0], pair1[1], pair2[0], pair2[1])
        return None, None
        
    common_catalogue = select_cat2[idx]
    cat1_groups = select_cat1.groupby("eventID")
    mag1 = []
    sigma1 = []
    mag2 = []
    sigma2 = []
    for row in list(common_catalogue.iterrows()):
        #print row
        mag2.append(row[1].value)
        sigma2.append(row[1].sigma)
        event1 = cat1_groups.get_group(row[1].eventID)
        if len(event1) > 1:
            event1 = event1.iloc[np.argmax(event1["originID"].values)]
            mag1.append(event1.value.tolist())
            sigma1.append(event1.sigma.tolist())
        else:
            mag1.extend(event1.value.tolist())
            sigma1.extend(event1.sigma.tolist())

    output_catalogue = CatalogueDB()
    output_catalogue.origins = catalogue.origins[
        catalogue.origins.eventID.isin(common_catalogue.eventID)]
    output_catalogue.magnitudes = catalogue.magnitudes[
        catalogue.magnitudes.eventID.isin(common_catalogue.eventID)]
    _, _ = output_catalogue._get_number_origins_magnitudes()
    pair_1_key = "{:s}({:s})".format(pair1[1],pair1[0])
    pair_2_key = "{:s}({:s})".format(pair2[1],pair2[0])
    return OrderedDict([
        (pair_1_key, np.array(mag1)),
        (pair_1_key + " Sigma", np.array(sigma1)),                   
        (pair_2_key, np.array(mag2)),
        (pair_2_key + " Sigma", np.array(sigma2))]), output_catalogue

def mine_agency_magnitude_combinations(catalogue, agency_mag_data, threshold,
        no_case=False):
    """
    Return list of possible agency and magnitude combinations that would
    exceed a threshold number of points
    """
    results_dict = []
    for iloc, agency_1 in enumerate(agency_mag_data.keys()):
        for mag_1 in agency_mag_data[agency_1]["Magnitudes"].keys():
            if agency_mag_data[agency_1]["Magnitudes"][mag_1] < threshold:
                continue
            for agency_2 in agency_mag_data.keys()[iloc:]:
                for mag_2 in agency_mag_data[agency_2]["Magnitudes"].keys():
                    if (agency_1 == agency_2) and (mag_1 == mag_2):
                        # Redundent
                        continue
                    if agency_mag_data[agency_2]["Magnitudes"][mag_2] <\
                        threshold:
                        # Skip
                        continue
                    print "Trying: (%s, %s) and (%s, %s)" % (agency_1, mag_1,
                                                             agency_2, mag_2)
                    data, _ = get_agency_magnitude_pairs(catalogue,
                                                         (agency_1, mag_1),
                                                         (agency_2, mag_2),
                                                         no_case)
                    if data:
                        # Report number of values
                        data_keys = data.keys()
                        npairs = len(data[data_keys[0]])
                        if npairs > threshold:
                            results_dict.append(
                                ("|".join([data_keys[0], data_keys[2]]),
                                 data))
                    else:
                        print "----> No pairs found!"
    return OrderedDict(results_dict)


def mine_agency_magnitude_combinations_to_file(output_file, catalogue,
        agency_mag_data, threshold, no_case=False):
    """
    Return list of possible agency and magnitude combinations that would
    exceed a threshold number of points
    """
    results_dict = []
    fle = h5py.File(output_file, "a")
    for iloc, agency_1 in enumerate(agency_mag_data.keys()):
        for mag_1 in agency_mag_data[agency_1]["Magnitudes"].keys():
            if agency_mag_data[agency_1]["Magnitudes"][mag_1] < threshold:
                continue
            for agency_2 in agency_mag_data.keys()[iloc:]:
                for mag_2 in agency_mag_data[agency_2]["Magnitudes"].keys():
                    if (agency_1 == agency_2) and (mag_1 == mag_2):
                        # Redundent
                        continue
                    if agency_mag_data[agency_2]["Magnitudes"][mag_2] <\
                        threshold:
                        # Skip
                        continue
                    print "Trying: (%s, %s) and (%s, %s)" % (agency_1, mag_1,
                                                             agency_2, mag_2)
                    data, _ = get_agency_magnitude_pairs(catalogue,
                                                         (agency_1, mag_1),
                                                         (agency_2, mag_2),
                                                         no_case)
                    if data:
                        # Report number of values
                        data_keys = data.keys()
                        npairs = len(data[data_keys[0]])
                        if npairs > threshold:
                            combo_key = "|".join([data_keys[0],
                                                  data_keys[2]])

                            results_dict.append(
                                ("|".join([data_keys[0], data_keys[2]]),
                                 data))
                            dset = fle.create_dataset(combo_key,
                                                      (npairs, 4),
                                                      dtype="f")
                            dset[:] = np.column_stack([data[data_keys[0]],
                                                       data[data_keys[1]],
                                                       data[data_keys[2]],
                                                       data[data_keys[3]]])
                    else:
                        print "----> No pairs found!"
    fle.close()
    
def join_query_results(data1, data2):
    """
    Joins the results of two magnitude-agency queries
    """
    if not data1:
        if data2:
            return data2
        else:
            return None
    if not data2:
        if data1:
            return data1
        else:
            return None
    joint_data = []
    data2_keys = data2.keys()
    for iloc, key in enumerate(data1.keys()):
        if not (key == data2_keys[iloc]):
            joint_key = key + " & " + data2_keys[iloc]
        else:
            joint_key = key
        data_key = (joint_key,
                    np.hstack([data1[key], data2[data2_keys[iloc]]]))
        joint_data.append(data_key)
    return OrderedDict(joint_data)
       
    
def plot_agency_magnitude_pair(data, overlay=False, xlim=[], ylim=[],
        marker="o", figure_size=(7, 8), filetype="png", resolution=300,
        filename=None):
    """
    Plots the agency magnitude pair
    :param dict data:
        Query result for a particular joint agency-magnitude pair combination
    :param bool overlay:
        Allows another layer to be rendered on top (True) or closes the figure
        for plotting (False)
    :param list xlim:
        Lower and upper bounds for x-axis
    :param list ylim:
        Lower and upper bounds for y-axis
    """
    if not data:
        print "No pairs found - abandoning plot!"
        return
    fig = plt.figure(figsize=figure_size)
    keys = data.keys()
    plt.errorbar(data[keys[0]], data[keys[2]],
                 xerr=data[keys[1]], yerr=data[keys[3]],
                 marker=marker, mfc="b", mec="k", ls="None",
                 ecolor="r")
    plt.xlabel(utils._to_latex(keys[0]), fontsize=16)
    plt.ylabel(utils._to_latex(keys[2]), fontsize=16)
    plt.grid(True)
    if len(xlim) == 2:
        lowx = xlim[0]
        highx = xlim[1]
    else:
        lowx = np.floor(np.min(data[keys[0]]))
        highx = np.ceil(np.max(data[keys[0]]))

    if len(ylim) == 2:
        lowy = ylim[0]
        highy = ylim[1]
    else:
        lowy = np.floor(np.min(data[keys[2]]))
        highy = np.ceil(np.max(data[keys[2]]))

    if lowy < lowx:
        lowx = lowy
    if highy > highx:
        highx = highy
    plt.ylim(lowx, highx)
    plt.xlim(lowx, highx)
    # Overlay 1:1 line
    plt.plot(np.array([lowx, highx]), np.array([lowx, highx]), ls="--",
        color=[0.5, 0.5, 0.5], zorder=1)
    plt.tight_layout()
        
    if filename:
        utils._save_image(filename, filetype, resolution)
    if not overlay:
        plt.show()
    return data

def sample_agency_magnitude_pairs(data, xbins, ybins, number_samples=1):
    """

    """
    keys = data.keys()
    n_data = len(data[keys[0]])
    if not number_samples or (number_samples == 1):
        # Only one sample, return simple histogram
        #print xbins, ybins
        return np.histogram2d(np.around(data[keys[0]], 2),
                              np.around(data[keys[2]], 2),
                              bins=[xbins, ybins])[0]
    elif (np.max(data[keys[1]]) < 1E-15) and (np.max(data[keys[3]]) < 1E-15):
        # No uncertainty on magnitudes
        return np.histogram2d(np.around(data[keys[0]], 2),
                              np.around(data[keys[2]], 2),
                              bins=[xbins, ybins])[0]
    else:
        counter = np.zeros([len(xbins) - 1, len(ybins) - 1])
        for i in xrange(number_samples):
            # Sample data sets
            data_x = data[keys[0]] + data[keys[1]] * np.random.normal(0., 1.,
                                                                      n_data)
            data_y = data[keys[2]] + data[keys[3]] * np.random.normal(0., 1.,
                                                                      n_data)
            counter += np.histogram2d(data_x, data_y, bins=[xbins, ybins])[0]
        
        return counter / float(number_samples)
             


def plot_agency_magnitude_density(data, overlay=False, number_samples=0,
        xlim=[], ylim=[], figure_size=(7, 8), lognorm=True,
        filetype="png", resolution=300, filename=None):
    """

    """
    keys = data.keys()
    if not data:
        print "No pairs found - abandoning plot!"
        return
    
    if len(xlim) == 2:
        lowx = xlim[0]
        highx = xlim[1]
    else:
        lowx = np.floor(np.min(data[keys[0]]))
        highx = np.ceil(np.max(data[keys[0]]))

    if len(ylim) == 2:
        lowy = ylim[0]
        highy = ylim[1]
    else:
        lowy = np.floor(np.min(data[keys[2]]))
        highy = np.ceil(np.max(data[keys[2]]))
    
    if lowy < lowx:
        lowx = lowy
    if highy > highx:
        highx = highy

    xbins = np.linspace(lowx - 0.05, highx + 0.05,
                        ((highx + 0.05 - lowx - 0.05) / 0.1) + 2.0)
    ybins = np.linspace(lowx - 0.05, highx + 0.05, 
                        ((highx + 0.05 - lowx - 0.05) / 0.1) + 2.0)
    density = sample_agency_magnitude_pairs(data, xbins, ybins, number_samples)
    fig = plt.figure(figsize=figure_size)

    if lognorm:
        cmap = deepcopy(matplotlib.cm.get_cmap("jet"))
        data_norm = LogNorm(vmin=0.1, vmax=np.max(density))
    else:
        cmap = deepcopy(matplotlib.cm.get_cmap("jet"))
        cmap.set_under("w")
        data_norm = Normalize(vmin=0.1, vmax=np.max(density))
        #density[density < 1E-15] == np.nan  
    plt.pcolormesh(xbins[:-1] + 0.05, ybins[:-1] + 0.05, density.T,
                   norm=data_norm, cmap=cmap)
    cbar = plt.colorbar()
    cbar.set_label("Number Events", fontsize=16)
    plt.xlabel(utils._to_latex(keys[0]), fontsize=16)
    plt.ylabel(utils._to_latex(keys[2]), fontsize=16)
    plt.grid(True)
    plt.ylim(lowx, highx)
    plt.xlim(lowx, highx)
    # Overlay 1:1 line
    plt.plot(np.array([lowx, highx]), np.array([lowx, highx]), ls="--",
        color=[0.5, 0.5, 0.5], zorder=1)
    plt.tight_layout()
        
    if filename:
        utils._save_image(filename, filetype, resolution)
    if not overlay:
        plt.show()
    return data


DEFAULT_SIGMA = {"minimum": lambda x : np.nanmin(x),
                 "maximum": lambda x : np.nanmax(x),
                 "mean": lambda x : np.nanmean(x)}


class CatalogueRegressor(object):
    """
    Class to perform an orthodonal distance regression on a pair of magnitude
    data tuples
    :param dict data:
        Output of agency-magnitude query
    :param common_catalogue:
        Catalogue of common events as instance of :class: CatalogueDB
    :param list keys():
        List of keys in the data set
    :param model:
        Regression model (eventually as instance of :class: scipy.odr.Model)
    :param regression_data:
        Regression data (eventually as instance of :class: scipy.ord.RealData)
    :param results:
        Regression results as instance of :class: scipt.odr.Output
    :param str model_type:
        Type of model used for regression
    """
    def __init__(self, data, common_catalogue=None):
        """
        Instantiate with data
        """
        self.data = data
        self.common_catalogue = common_catalogue
        self.keys = self.data.keys()
        self.model = None
        self.regression_data = None
        self.results = None
        self.model_type = None
        self.standard_deviation = None

    @classmethod
    def from_catalogue(cls, catalogue, pair1, pair2, no_case=False):
        """
        Class method to instansiate the regression object with the agency-
        magnitude query parameters
        :param catalogue:
            Earthquake catalogue as instance of :class: CatalogueDB
        :params tuple pair1:
            Agency and magnitude combination (Agency, Magnitude Type) for
            defining the independent variable
        :params tuple pair2:
            Agency and magnitude combination (Agency, Magnitude Type) for
            defining the dependent variable
        :params bool no_case:
            Makes the selection case sensitive (True) or ignore case (False)
        """
        data, common_catalogue = \
            get_agency_magnitude_pairs(catalogue, pair1, pair2, no_case)
        if not data:
            raise ValueError("Cannot build regression!")  
        return cls(data, common_catalogue)

    @classmethod
    def from_array(cls, data, keys):
        """
        Class method to build the regression object from a simple four-column
        array of data and the corresponding keys
        """
        data_keys = keys.split("|")
        data_dict = OrderedDict([
            (data_keys[0], data[:, 0]),
            (data_keys[0] + " Sigma", data[:, 1]),
            (data_keys[1], data[:, 2]),
            (data_keys[1] + " Sigma", data[:, 3])])
        return cls(data_dict)

    def plot_data(self, overlay, xlim=[], ylim=[], marker="o",
            figure_size=(7, 7), filetype="png", resolution=300, filename=None):
        """
        Plots the result of the agency-magnitude query
        """
        plot_agency_magnitude_pair(self.data, overlay, xlim, ylim, marker,
            figure_size, filetype, resolution, filename)


    def plot_density(self, overlay, xlim=[], ylim=[], lognorm=True, sample=0,
            figure_size=(7, 7), filetype="png", resolution=300, filename=None):
        """
        Plots the result of the agency-magnitude query
        """
        plot_agency_magnitude_density(self.data, overlay, sample, xlim, ylim,
            figure_size, lognorm, filetype, resolution, filename)


    def run_regression(self, model_type, initial_params, setup_parameters={}):
        """
        Runs the regression analysis on the retreived data
        :param str model_type:
            Model type. Choose from {"polynomial", "piecewise", "exponential",
                "2segmentM#.#"} where M#.# is the corner magnitude
        :param list initial_params:
            Initial estimate of the parameters
            * polynomial = [c_1, c_2, c_3, ...] where
                  f(X) = \Sum_i^N c_i X^{i-1}
            * piecewise = [m_1, m_2, ..., m_i, xc_1, xc_2, ..., xc_i-1, c]
            * exponential =[c_1, c_2, c_3] where f(X) = exp(c_1 + c_2 X) + c_3
            * 2segmentM#.# = [m_1, m_2, c_1] where m_1 and m_2 are the gradient
                of slope 1 and 2, respectively, and c_1 is the intercept
        :param dict setup_parameters:
            Optionl parameters to control how to define missing uncertainties

        """
        if "2segment" in model_type:
            model_type, mag = model_type.split("M")
            mag = float(mag)
            self.model_type = utils.function_map[model_type](mag)
        else:
            if not model_type in utils.function_map.keys():
                raise ValueError("Model type %s not supported!" % model_type)
            self.model_type = utils.function_map[model_type]()
        self.model = odr.Model(self.model_type.run)
        if (model_type=="exponential") and (len(initial_params) != 3):
            raise ValueError("Exponential model requires three initial "
                             "parameters")
        setup_parameters.setdefault("Missing X", "Default")
        setup_parameters.setdefault("Missing Y", "Default")
        setup_parameters.setdefault("sx", 0.1)
        setup_parameters.setdefault("sy", 0.1)
        
        # Setup X
        s_x = self.data[self.keys[1]]
        idx = (np.isnan(s_x)) | (s_x < 1E-20)
        if np.any(idx):
            # Need to apply default sigma values
            if (setup_parameters["Missing X"] == "Default") or np.all(idx):
                s_x[idx] = setup_parameters["sx"]
            else:
                s_x[idx] = DEFAULT_SIGMA[setup_parameters["Missing X"]](s_x)
        # Setup Y
        s_y = self.data[self.keys[3]]
        idx = (np.isnan(s_y)) | (s_y < 1E-20)
        if np.any(idx):
            # Need to apply default sigma values
            if (setup_parameters["Missing Y"] == "Default") or np.all(idx):
                s_y[idx] = setup_parameters["sy"]
            else:
                s_y[idx] = DEFAULT_SIGMA[setup_parameters["Missing Y"]](s_y)
        self.regression_data = odr.RealData(self.data[self.keys[0]],
                                            self.data[self.keys[2]],
                                            sx=s_x,
                                            sy=s_y)
        regressor = odr.ODR(self.regression_data,
                            self.model,
                            initial_params)
        regressor.set_iprint(final=2)
        self.results = regressor.run()
        return self.results

    
    def plot_model(self, overlay, xlim=[], ylim=[], marker="o", line_color="g",
            figure_size=(7, 8), filetype="png",
            resolution=300, filename=None):
        """
        Plots the resulting regression model of the data
        """
        # Plot data
        plot_agency_magnitude_pair(self.data, True,
                                   xlim, ylim,
                                   marker, figure_size)
        # Plot Model
        model_x, model_y, self.standard_deviation = self.retrieve_model()
        title_string = self.model_type.get_string(self.keys[2], self.keys[0])
        plt.plot(model_x, model_y, line_color,
                 linewidth=2.0,
                 label=title_string)
        #plt.title(r"{:s}".format(title_string), fontsize=14)
        plt.legend(loc=2, frameon=False)
        if filename:
            utils._save_image(filename, filetype, resolution)
        if not overlay:
            plt.show()

    def plot_model_density(self, overlay, sample, xlim=[], ylim=[],
            line_color="g", figure_size=(7, 8), lognorm=True, filetype="png",
            resolution=300, filename=None):
        """
        Plots the resulting regression model of the data
        """
        # Plot data
        plot_agency_magnitude_density(self.data, True, sample, xlim, ylim,
                                      figure_size, lognorm)
        # Plot Model
        model_x, model_y, self.standard_deviation = self.retrieve_model()
        title_string = self.model_type.get_string(self.keys[2], self.keys[0])
        plt.plot(model_x, model_y, line_color,
                 linewidth=2.0,
                 label=title_string)
        #plt.title(r"{:s}".format(title_string), fontsize=14)
        plt.legend(loc=2, frameon=False)
        if filename:
            utils._save_image(filename, filetype, resolution)
        if not overlay:
            plt.show()

    def plot_magnitude_conversion_model(self, model, overlay, line_color="g",
            filetype="png", resolution=300, filename=None):
        """
        Plots a specific magnitude conversion model (to overlay on top of
        a current figure)
        """
        model_x = np.arange(0.9 * np.min(self.data[self.keys[0]]),
                            1.1 * np.max(self.data[self.keys[0]]),
                            0.01)
        model_y, _ = model.convert_value(model_x, 0.0)
        plt.plot(model_x, model_y, line_color,
                 linewidth=2.0,
                 label=model.model_name)
        plt.legend(loc=2, frameon=False)
        if filename:
            utils._save_image(filename, filetype, resolution)
        if not overlay:
            plt.show()

    def retrieve_model(self):
        """
         
        """
        model_x = np.arange(0.9 * np.min(self.data[self.keys[0]]),
                            1.1 * np.max(self.data[self.keys[0]]),
                            0.01)
        model_y = self.model_type.run(self.results.beta, model_x)
        if isinstance(self.model_type, utils.TwoSegmentLinear):

            idx = self.data[self.keys[0]] < self.model_type.corner_magnitude
            data_xl = self.data[self.keys[0]][idx]
            data_yl = self.data[self.keys[2]][idx]
            sigma_l = np.std(data_yl -
                             self.model_type.run(self.results.beta, data_xl))
            idx = self.data[self.keys[0]] >= self.model_type.corner_magnitude
            data_xu = self.data[self.keys[0]][idx]
            data_yu = self.data[self.keys[2]][idx]
            sigma_u = np.std(data_yu -
                             self.model_type.run(self.results.beta, data_xu))
            standard_deviation = [sigma_l, sigma_u]
        elif isinstance(self.model_type, utils.PiecewiseLinear):
            standard_deviation = []
            npar = len(self.results.beta)
            corner_magnitudes = [-np.inf]
            corner_magnitudes.extend(self.results.beta[(npar / 2):(npar - 1)])
            corner_magnitudes.extend(np.inf)
            for iloc, m_c in range(0, len(corner_magnitudes) - 1):
            
                idx = np.logical_and(
                    self.data[self.keys[0]] >= m_c,
                    self.data[self.keys[0]] < corner_magnitudes[iloc + 1])
                data_x = self.data[self.keys[0]][idx]
                data_y = self.data[self.keys[2]][idx]
                standard_deviation.append(
                        np.std(data_y - self.model_type.run(self.results.beta,
                                                            data_x)))
        else:
            standard_deviation = np.std(
                self.data[self.keys[2]] -
                self.model_type.run(self.results.beta, self.data[self.keys[0]])
                )
        return model_x, model_y, standard_deviation


def plot_catalogue_map(config, catalogue, magnitude_scale=False,
        color_norm=None, overlay=False, figure_size=(7,8), filename=None,
        filetype="png", dpi=300):
    """
    Creates a map of the catalogue
    """
    plt.figure(figsize=figure_size)
    lat0 = config["llat"] + ((config["ulat"] - config["llat"]) / 2)
    lon0 = config["llon"] + ((config["ulon"] - config["llon"]) / 2)
    map1 = Basemap(llcrnrlon=config["llon"], llcrnrlat=config["llat"],
                   urcrnrlon=config["ulon"], urcrnrlat=config["ulat"],
                   projection='stere', resolution=config['resolution'],
                   area_thresh=1000.0, lat_0=lat0, lon_0=lon0)
    map1.drawcountries()
    map1.drawmapboundary()
    map1.drawcoastlines()
    map1.drawstates()
    parallels = np.arange(config["llat"],
                          config["ulat"] + config["parallel"],
                          config["parallel"])
    meridians = np.arange(config["llon"],
                          config["ulon"] + config["meridian"],
                          config["meridian"])
    map1.drawparallels(parallels, color=[0.5, 0.5, 0.5], 
                       labels=[1, 0, 0, 0], fontsize=12)
    map1.drawmeridians(meridians, color=[0.5, 0.5, 0.5],
                       labels=[0, 0, 0, 1], fontsize=12)
    map1.drawmapboundary(fill_color='#C2DFFF')
    map1.fillcontinents(color='wheat', lake_color="#C2DFFF")
    lon, lat = map1(catalogue.origins["longitude"].values,
                    catalogue.origins["latitude"].values)
    if magnitude_scale:
        magnitudes = []
        mag_grps = catalogue.magnitudes.groupby("originID")
        for key in catalogue.origins.originID.values:
            if key in catalogue.magnitudes.originID.values:
                grp = mag_grps.get_group(key)
                if magnitude_scale in grp.magType.values:
                    magnitudes.append(
                        grp[grp.magType==magnitude_scale].value.values[0])
                else:
                    magnitudes.append(1.0)
        #print magnitudes
        magnitudes = np.array(magnitudes) ** 2.0
    else:
        magnitudes = 10.0
    
    map1.scatter(lon, lat,
                 marker="o",
                 s=magnitudes,
                 c=catalogue.origins["depth"].values,
                 norm=color_norm,
                 alpha=1.0,
                 linewidths=0.1,
                 edgecolor="w",
                 zorder=5)
    cbar = map1.colorbar()
    cbar.set_label("Depth", fontsize=14)
    if filename:
        plt.savefig(filename, format=filetype, dpi=dpi)
    if not overlay:
        plt.show()
