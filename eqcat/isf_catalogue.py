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
General class for an earthquame catalogue in ISC (ISF) format
"""
import datetime
import numpy as np
import h5py
import pandas as pd
from utils import decimal_time
from math import fabs


DATAMAP = [("eventID", "a16"), ("originID", "a16"), ("Agency", "a14"), 
    ("year", "i2"), ("month", "i2"), ("day", "i2"), ("hour", "i2"),
    ("minute", "i2"), ("second", "f2"), ("time_error", "f4"),
    ("longitude", "f4"), ("latitude", "f4"), ("depth", "f4"),("depthSolution", "a1"), 
    ("semimajor90", "f4"), ("semiminor90", "f4"), ("error_strike", "f2"),
    ("depth_error", "f4"), ("prime", "i1")]

MAGDATAMAP = [("eventID", "a12"), ("originID", "a12"), ("magnitudeID", "a40"), 
    ("value", "f4"), ("sigma", "f4"), ("magType", "a6"), ("magAgency", "a14")]

def datetime_to_decimal_time(date, time):
    '''
    Converts a datetime object to decimal time
    '''
    # Seconds, microseconds to floating seconds
    seconds = np.array(float(time.second))
    microseconds = np.array(float(time.microsecond))
    seconds = seconds + (microseconds / 1.0E6)
    return decimal_time(np.array([date.year]), 
                        np.array([date.month]), 
                        np.array([date.day]), 
                        np.array([time.hour]),
                        np.array([time.minute]), 
                        np.array([seconds]))

class Magnitude(object):
    '''
    Stores an instance of a magnitude
    :param int identifier:
        Identifier as Origin ID
    :param float value:
        Magnitude value
    :param str author:
        Magnitude author
    :param str scale:
        Magnitude scale (defaults to UK if not entered)
    :param float sigma:
        Magnitude uncertainty
    :param int stations:
        Number of stations
    '''
    def __init__(self, event_id, origin_id, value, author, scale=None,
        sigma=None, stations=None):
        '''
        '''
        self.event_id = event_id
        self.origin_id = origin_id
        self.value = value
        self.author = author
        if scale:
            self.scale = scale
        else:
            self.scale = 'UK'
        self.sigma = sigma
        self.stations = stations
        self.magnitude_id = "|".join(["{:s}".format(self.origin_id),
                                      self.author,
                                      "{:.2f}".format(self.value),
                                      self.scale])
    
    def compare_magnitude(self, magnitude, tol=1E-3):
        '''
        Compares if a second instance of a magnitude class is the same as the
        current magnitude
        '''
        if (magnitude.origin_id == self.origin_id) and (magnitude.author == 
            self.author) and (magnitude.scale == self.scale):
            if fabs(magnitude.value - self.value) > 0.001:
                print "%s != %s" %(self.__str__(), str(magnitude))
                raise ValueError('Two magnitudes with same metadata contain '
                                 'different values!')
            return True
        else:
            return False
    
    def __str__(self):
        """
        Returns the magnitude identifier
        """
        return self.magnitude_id


class Location(object):
    '''
    Instance of a magnitude location
    :param int origin_id:
        Identifier as origin ID
    :param float longitude:
        Longitude (decimal degrees)
    :param float latitude:
        Latitude (decimal degrees)
    :param float depth:
        Depth (decimal degrees)
        :param str DepthSolution:
        depthSolution (flag) fixed flag (f = fixed depth station, 
                                         d = depth phases, 
                                         blank if not a fixed depth)
    :param float semimajor90:
        Semimajor axis of 90 % error ellipse (km)
    :param float semiminor90:
        Semiminor axis of 90 % error ellipse (km)
    :param float error_strike:
        Strike of the semimajor axis of the error ellipse
    :param float depth_error:
        1 s.d. Error on the depth value (km) 
    '''
    def __init__(self, origin_id, longitude, latitude, depth, depthSolution=None,
                semimajor90=None,
                semiminor90=None, error_strike=None, depth_error=None):
        '''
        '''
        self.identifier = origin_id
        self.longitude = longitude
        self.latitude = latitude
        self.depth=depth
        self.depthSolution=depthSolution
        self.semimajor90 = semimajor90
        self.semiminor90 = semiminor90
        self.error_strike = error_strike
        self.depth_error = depth_error

    def __str__(self):
        """
        Returns a simple location string that concatenates longitude,
        latitude and depth
        """
        if not self.depth:
            depth_str = ""
        else:
            depth_str = str(self.depth)
        return "%s|%s|%s" % (str(self.longitude),
                             str(self.latitude),
                             depth_str)

class Origin(object):
    '''
    In instance of an origin block
    :param int identifier:
        Origin identifier
    :param date:
        Date as instance of datetime.date object
    :param time:
        Time as instance of datetime.time object
    :param location:
        Location as instance of isf_catalogue.Location object
    :param str author:
        Author ID
    :param float time_error:
        Time error (s)
    :param float time_rms:
        Time root-mean-square error (s)
    :param dict metadata:
        Metadata of dictionary including - 
        - 'Nphases' - Number of defining phases
        - 'Nstations' - Number of recording stations
        - 'AzimuthGap' - Azimuth Gap of recodring stations
        - 'minDist' - Minimum distance to closest station (degrees)
        - 'maxDist' - Maximum distance to furthest station (degrees)
        - 'FixedTime' - Fixed solution (str)
        - 'DepthSolution' - 
        - 'AnalysisType' - Analysis type
        - 'LocationMethod' - Location Method
        - 'EventType' - Event type
    
    '''
    def __init__(self, identifier, date, time, location, author, 
        is_prime=False, is_centroid=False, time_error=None, time_rms=None, 
        metadata=None):
        """
        Instantiates
        """
        self.id = identifier
        self.date = date
        self.time = time
        self.location = location
        self.author=author
        self.metadata=metadata
        self.magnitudes = []
        self.is_prime = is_prime
        self.is_centroid = is_centroid
        self.time_error = time_error
        self.time_rms = time_rms
        self.date_time_str = "|".join([str(self.date).replace("-", "|"),
                                       str(self.time).replace(":", "|")])

    def get_number_magnitudes(self):
        """
        Returns the total number of magnitudes associated to the origin
        """
        return len(self.magnitudes)

    def get_magnitude_scales(self):
        """
        Returns the list of magnitude scales associated with the origin
        """
        if self.get_number_magnitudes() == 0:
            return None
        else:
            return [mag.scale for mag in self.magnitudes]

    def get_magnitude_values(self):
        """
        Returns the list of magnitude values associated with the origin
        """
        if self.get_number_magnitudes() == 0:
            return None
        else:
            return [mag.value for mag in self.magnitudes]


    def get_magnitude_tuple(self):
        """
        Returns a list of tuples of (Value, Type) for all magnitudes
        associated with the origin
        """
        if self.get_number_magnitudes() == 0:
            return None
        else:
            return [(mag.value, mag.scale) for mag in self.magnitudes]

    def merge_secondary_magnitudes(self, magnitudes):
        """
        Merge magnitudes as instances of isf_catalogue.Magnitude into origin
        list. 
        """
        if self.get_number_magnitudes() == 0:
            # As no magnitudes currently exist then add all input magnitudes
            # to origin
            self.magnitudes = magnitudes
        else:
            for magnitude1 in magnitudes:
                if not isinstance(magnitude1, Magnitude):
                    raise ValueError('Secondary magnitude must be instance of '
                                     'isf_catalogue.Magnitude')
                has_magnitude = False
                for magnitude2 in self.magnitudes:
                    # Compare magnitudes
                    has_magnitude = magnitude2.compare_magnitude(magnitude1)
                if not has_magnitude:
                    # Magnitude not in current list - append
                    self.magnitudes.append(magnitude1)
    
    def __str__(self):
        """
        Returns an string providing information regarding the origin (namely
        the ID, date, time and location
        """

        return "%s|%s|%s" % (self.id, self.date_time_str, str(self.location))

class Event(object):
    '''
    Instance of an event block
    :param int id:
        Event ID
    :param origins:
        List of instances of the Origin class
    :param magnitudes:
        List of instances of the Magnitude class
    :param str description:
        Description string

    '''
    def __init__(self, identifier, origins, magnitudes, description=None):
        """
        Instantiate event object
        """
        self.id = identifier
        self.origins = origins
        self.magnitudes = magnitudes
        self.description = description
        self.comment = ""

    def number_origins(self):
        '''
        Return number of origins associated to event
        '''
        return len(self.origins)

    def get_origin_id_list(self):
        '''
        Return list of origin IDs associated to event
        '''
        return [orig.id for orig in self.origins]

    def get_author_list(self):
        """
        Return list of origin authors associated to event
        """
        return [orig.author for orig in self.origins]

    def number_magnitudes(self):
        """
        Returns number of magnitudes associated to event
        """
        return len(self.magnitudes)

    def magnitude_string(self, delimiter=","):
        """
        Returns the full set of magnitudes as a delimited list of strings
        """
        mag_list = []
        for mag in self.magnitudes:
            mag_list.extend([str(mag.value), str(mag.sigma), mag.scale,
                             mag.author])
        return delimiter.join(mag_list)

    def assign_magnitudes_to_origins(self):
        """
        Will loop through each origin and assign magnitudes to origin
        """
        if self.number_magnitudes() == 0:
            return ValueError('No magnitudes in event!')
        if self.number_origins() == 0:
            return ValueError('No origins in event!')
        for origin in self.origins:
            for magnitude in self.magnitudes:
                if origin.id == magnitude.origin_id:
                    origin.magnitudes.append(magnitude)

    def merge_secondary_origin(self, origin2set):
        '''
        Merges an instance of an isf_catalogue.Origin class into the set 
        of origins. 
        '''
        current_id_list = self.get_origin_id_list()
        for origin2 in origin2set:
            if not isinstance(origin2, Origin):
                raise ValueError('Secondary origins must be instance of '
                                 'isf_catalogue.Origin class')
            if origin2.id in current_id_list:
                # Origin is already in list - process magnitudes
                location = current_id_list.index(origin2.id)
                origin = self.origins[location]
                origin.merge_secondary_magnitudes(origin2.magnitudes)
                self.origins[location] = origin
            else:
                self.origins.append(origin2)

    def get_origin_mag_vals(self):
        """
        Returns a list of origin and magnitude pairs
        """
        authors = []
        mag_scales = []
        mag_values = []
        mag_sigmas = []
        for origin in self.origins:
            for mag in origin.magnitudes:
                authors.append(mag.author)
                mag_scales.append(mag.scale)
                mag_values.append(mag.value)
                mag_sigmas.append(mag.sigma)
        return authors, mag_scales, mag_values, mag_sigmas

    def __str__(self):
        """
        Return string definition from the ID and description
        """
        return "%s|'%s'" % (str(self.id), self.description)


class ISFCatalogue(object):
    '''
    Instance of an earthquake catalogue
    '''
    def __init__(self, identifier, name, events=None):
        """
        Instantiate the catalogue with a name and identifier
        """
        self.id = identifier
        self.name = name
        if isinstance(events, list):
            self.events = events
        else:
            self.events = []


    def get_number_events(self):
        """
        Return number of events
        """
        return len(self.events)


    def get_event_key_list(self):
        """
        Returns list event IDs
        """
        if self.get_number_events() == 0:
            return []
        else:
            return [eq.id for eq in self.events]


    def merge_second_catalogue(self, catalogue):
        '''
        Merge in a second catalogue of the format ISF Catalogue and link via 
        Event Keys
        '''
        if not isinstance(catalogue, ISFCatalogue):
            raise ValueError('Input catalogue must be instance of ISF '
                             'Catalogue')

        native_keys = self.get_event_key_list()
        new_keys = catalogue.get_event_key_list()
        for iloc, key in enumerate(new_keys):
            if key in native_keys:
                # Add secondary to primary
                location = native_keys.index(key)
                # Merge origins into catalogue
                event = self.events[location]
                event.merge_secondary_origin(catalogue.events[iloc].origins)
                self.events[location] = event

    def get_decimal_dates(self):
        """
        Returns dates and time as a vector of decimal dates
        """
        neq = self.get_number_events()
        year = np.zeros(neq, dtype=int)
        month = np.zeros(neq, dtype=int)
        day = np.zeros(neq, dtype=int)
        hour = np.zeros(neq, dtype=int)
        minute = np.zeros(neq, dtype=int)
        second = np.zeros(neq, dtype=float)
        for iloc, event in enumerate(self.events):
            is_selected = False
            for origin in event.origins:
                if is_selected:
                    continue
                if origin.is_prime:
                    year[iloc] = origin.date.year
                    month[iloc] = origin.date.month
                    day[iloc] = origin.date.day
                    hour[iloc] = origin.time.hour
                    minute[iloc] = origin.time.minute
                    second[iloc] = float(origin.time.second) + \
                        (float(origin.time.microsecond) / 1.0E6)
                    is_selected = True
            if not is_selected:
                # No prime origins - take the first
                year[iloc] = event.origins[0].date.year
                month[iloc] = event.origins[0].date.month
                day[iloc] = event.origins[0].date.day
                hour[iloc] = event.origins[0].time.hour
                minute[iloc] = event.origins[0].time.minute
                second[iloc] = float(event.origins[0].time.second) + \
                    (float(event.origins[0].time.microsecond) / 1.0E6)
        return decimal_time(year, month, day, hour, minute, second)
                    

    def render_to_simple_numpy_array(self):
        '''
        Render to a simple array using preferred origin time and magnitude
        '''
        decimal_time = self.get_decimal_dates()
        decimal_time = decimal_time.tolist()
        simple_array = []
        for iloc, event in enumerate(self.events):
            for origin in event.origins:
                if not origin.is_prime:
                    continue
                else:
                    if len(origin.magnitudes) == 0:
                        continue

                    simple_array.append([event.id, 
                                         origin.id, 
                                         decimal_time[iloc],
                                         origin.location.latitude, 
                                         origin.location.longitude,
                                         origin.location.depth, 
                                         origin.magnitudes[0].value])
        return np.array(simple_array)


    def get_origin_mag_tables(self):
        """
        Returns the full ISF catalogue as a pair of tables, the first
        containing only the origins, the second containing the
        magnitudes
        """
        #Find out size of tables
        n_origins = 0
        n_mags = 0
        for eq in self.events:
            n_origins += len(eq.origins)
            n_mags += len(eq.magnitudes)
        # Pre-allocate data to zeros
        origin_data = np.zeros((n_origins,), dtype=DATAMAP)
        mag_data = np.zeros((n_mags,), dtype=MAGDATAMAP)
        o_counter = 0
        m_counter = 0
        for eq in self.events:
            for orig in eq.origins:
                # Convert seconds fromd datetime to float
                seconds = float(orig.time.second) +\
                    float(orig.time.microsecond) / 1.0E6
                # Optional defaults
                if orig.time_error:
                    time_error = orig.time_error
                else:    
                    time_error = 0.0
                if orig.location.semimajor90:
                    semimajor90 = orig.location.semimajor90
                    semiminor90 = orig.location.semiminor90
                    error_strike = orig.location.error_strike
                else:
                    semimajor90 = 0.0
                    semiminor90 = 0.0
                    error_strike = 0.0

                if orig.location.depth_error:
                    depth_error = orig.location.depth_error
                else: 
                    depth_error = 0.0
                
                if orig.location.depthSolution:
                    depthSolution = orig.location.depthSolution
                else: 
                    depthSolution = ""               

                
                if orig.is_prime:
                    prime = 1
                else:
                    prime = 0
                origin_data[o_counter] = (eq.id, orig.id, orig.author,
                    orig.date.year, orig.date.month, orig.date.day,
                    orig.time.hour, orig.time.minute, seconds, time_error,
                    orig.location.longitude, orig.location.latitude, 
                    orig.location.depth, orig.location.depthSolution,
                    semimajor90, semiminor90, 
                    error_strike, depth_error, prime)
                o_counter += 1

            for mag in eq.magnitudes:
                if mag.sigma:
                    sigma = mag.sigma
                else:
                    sigma = 0.0
                mag_data[m_counter] = (mag.event_id, mag.origin_id, 
                    mag.magnitude_id, mag.value, sigma, mag.scale, mag.author)
                m_counter += 1
        return origin_data, mag_data
    
    
    
    def build_dataframe(self, hdf5_file=None):
        """
        Renders the catalogue into two Pandas Dataframe objects, one
        representing the full list of origins, the other the full list
        of magnitudes
        :param str hd5_file:
            Path to the hdf5 for writing
        :returns:
            orig_df - Origin dataframe
            mag_df  - Magnitude dataframe
        """
        origin_data, mag_data = self.get_origin_mag_tables()
        orig_df = pd.DataFrame(origin_data,
                               columns=[val[0] for val in DATAMAP])
        mag_df = pd.DataFrame(mag_data,
                              columns=[val[0] for val in MAGDATAMAP])
        if hdf5_file:
            store = pd.HDFStore(hdf5_file)
            store.append("catalogue/origins", orig_df)
            store.append("catalogue/magnitudes", mag_df)
            store.close()
        return orig_df, mag_df

    def render_to_xyzm(self, filename, frmt='%.3f'):
        '''
        Writes the catalogue to a simple [long, lat, depth, mag] format - for
        use in GMT
        '''
        # Get numpy array
        print 'Creating array ...'
        #cat_array = self.render_to_simple_numpy_array('Mw')
        cat_array = self.render_to_simple_numpy_array()
        cat_array = cat_array[:, [4, 3, 5, 6]]
        print 'Writing to file ...'
        np.savetxt(filename, cat_array, fmt=frmt)
        print 'done!'

    def quick_export(self, filename, delimiter=","):
        """
        Rapidly exports the catalogue to an ascii format
        """
        f = open(filename, "w")
        print >> f, "eventID,Description,originID,year,month,day,hour,"\
            "minute,second,longitude,latitude,depth,magOriginID,magAgency,"\
            "magnitude,magScale"
        for event in self.events:
            base_str = str(event)
            for origin in event.origins:
                output_strings = [base_str, str(origin)]
                output_strings.extend([str(mag) for mag in origin.magnitudes])
                output_str = "|".join(output_strings)
                print >> f, output_str.replace("|", delimiter)
        f.close()
        print "Exported to %s" % filename
          
    def __iter__(self):
        """
        If iterable, returns list of events
        """
        return self.events

    def __len__(self):
        """
        For len return number of events
        """
        return self.get_number_events()


