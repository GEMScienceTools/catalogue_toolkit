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

'''
Reader for the catalogue in a reduced ISF Format considering only
headers
'''
import os
import re
import datetime
import numpy as np
from math import floor, ceil, fabs
from eqcat.parsers.base import (BaseCatalogueDatabaseReader,
                                _to_int, _to_str, _to_float)
from eqcat.isf_catalogue import (Magnitude,
                                 Location,
                                 Origin,
                                 Event,
                                 ISFCatalogue)


origin_header = '   Date       Time        Err   RMS Latitude Longitude  '\
    'Smaj  Smin  Az Depth   Err Ndef Nsta Gap  mdist  Mdist Qual   '\
    'Author      OrigID'

magnitude_header = 'Magnitude  Err Nsta Author      OrigID'

# Default to 'Global Catalogue' agency bulletins
GLOBAL_SELECTED_AGENCIES = ['ISC', 'EHB', 'GCMT', 'HRVD',
                            'GUTE', 'PAS', 'NIED']


def get_event_header_row(row):
    """
    Parses a header row from ISF format and returns an instance of the
    isf_catalogue.Event class
    """
    header_dat = row.split()
    return Event(header_dat[1], origins=[], magnitudes=[],
                 description=" ".join(header_dat[2:]))

def get_time_from_str(row):
    """
    Parses the time data from the origin line and returns an instance of the
    datetime.time class
    """
    # Get time hh:mm:ss.ss
    hms = row[11:22].split(':')
    #print "hh:mm:ss:", hms
    hours = int(hms[0])
    minutes = int(hms[1])
    secs = float(hms[2])
    seconds = int(floor(secs))
    microseconds = int((secs - seconds) * 1000000.)
    # Get time error
    time_error = _to_float(row[24:29])
    time_rms = _to_float(row[30:35])
    return datetime.time(hours, minutes, seconds, microseconds), time_error, \
        time_rms

def get_origin_metadata(row):
    """
    Returns the dictionary of metadata from the origins
    """
    metadata = {
        'Nphases': _to_int(row[83:87]),
        'Nstations': _to_int(row[88:92]),
        'AzimuthGap': _to_float(row[93:96]),
        'minDist': _to_float(row[97:103]),
        'maxDist': _to_float(row[104:110]),
        'FixedTime': _to_str(row[22]),
        'DepthSolution': _to_str(row[54]),
        'AnalysisType': _to_str(row[111]),
        'LocationMethod': _to_str(row[113]),
        'EventType': _to_str(row[115:117])}
    return metadata

def get_event_origin_row(row, selected_agencies=[]):
    '''
    Parses the Origin row from ISF format to an instance of an
    isf_catalogue.Origin class. If the author is not one of the selected
    agencies then None is returns
    '''
    origin_id = _to_str(row[128:])
    author = _to_str(row[118:127])
    if len(selected_agencies) and not author in selected_agencies:
        # Origin not an instance of ISC Reviewed, Engdahl, HRVD or GCMT -
        # origin not saved!
        return None
    # Get date yyyy/mm/dd
    ymd = map(int, row[:10].split('/'))
    #print "YMD",ymd
    date = datetime.date(ymd[0], ymd[1], ymd[2])
    # Get time
    time, time_error, time_rms = get_time_from_str(row)
    # Get longitude and latitude
    latitude = float(row[36:44])
    longitude = float(row[45:54])
    # Get error ellipse
    semimajor90 = _to_float(row[55:60])
    semiminor90 = _to_float(row[61:66])
    error_strike = _to_float(row[67:70])
    # Get depths
    #depth = _to_float(row[71:75])
    depth = _to_float(row[71:75])
    depthSolution = _to_str(row[76:78])
    #if depthSolution == "f":
    #    print "depth= ", depth, "DepthSolution =", depthSolution
    depth_error = _to_float(row[78:82])
    # Create location class
    location = Location(origin_id, longitude, latitude, depth,depthSolution, 
                        semimajor90,semiminor90, error_strike, depth_error)
    # Get the metadata
    metadata = get_origin_metadata(row)
    return Origin(origin_id, date, time, location, author, 
                  time_error=time_error, time_rms=time_rms,
                  metadata=metadata)

def get_event_magnitude(row, event_id, 
                        selected_agencies=[]):
                        #,selected_types=[]):
    """
    Creates an instance of an isf_catalogue.Magnitude object from the row
    string, or returns None if the author is not one of the selected agencies
    or magnitude types
    """
    origin_id = _to_str(row[30:])
    author = row[20:29].strip(' ')
    scale=row[:5].strip(' ')
    if (len(selected_agencies) and not author in selected_agencies):
        #\
        #or (len(selected_agencies) and not scale in selected_types)):
        # Magnitude does not correspond to a selected agency - ignore
        return None
    sigma = _to_float(row[11:14])
    nstations = _to_int(row[15:19])
    return Magnitude(event_id, origin_id, _to_float(row[6:10]), author, 
                     scale=scale, sigma=sigma, stations=nstations) 


class ISFReader(BaseCatalogueDatabaseReader):
    '''
    Class to read an ISF formatted earthquake catalogue considering only
    the origin agencies, the magnitude agencies and the magnitude types
    defined by the user
    '''

    def __init__(self, filename, 
                 selected_origin_agencies=[],
                 selected_magnitude_agencies=[],
                 #selected_magnitude_types =[],
                 rejection_keywords=[],
                 lower_magnitude=None, upper_magnitude=None):
        
        super(ISFReader, self).__init__(filename, 
                                        selected_origin_agencies,
                                        selected_magnitude_agencies)
#                                        ,selected_magnitude_types)
        
        self.rejected_catalogue = []
        self.rejection_keywords = rejection_keywords
        if lower_magnitude and upper_magnitude:
            assert upper_magnitude > lower_magnitude
        if lower_magnitude:
            self.lower_mag = lower_magnitude
        else:
            self.lower_mag = -np.inf
        if upper_magnitude:
            self.upper_mag = upper_magnitude
        else:
            self.upper_mag = np.inf

    def read_file(self, identifier, name):
        """
        Reads the catalogue from the file and assigns the identifier and name
        """
        self.catalogue = ISFCatalogue(identifier, name)
        f = open(self.filename, 'rt')
        counter = 0
        is_origin = False
        is_magnitude = False
        comment_str = ""
        for row in f.readlines():
            if not row.rstrip('\n'):
                # Ignore empty rows
                continue
            elif "DATA_TYPE EVENT IMS1.0" in row:
                # Ignore header row
                continue
            elif "ISC Bulletin" in row:
                # Yet anothet header row
                continue
            elif "STOP" in row:
                # Footer row
                continue
            else:
                pass
                
            if '(#PRIME)' in row:
                # Previous origin block was the prime origin
                if len(origins) > 0:
                    origins[-1].is_prime = True
                continue
                
            if '(#CENTROID)' in row:
                # Previous origin block is a centroid
                if len(origins) > 0:
                    origins[-1].is_centroid = True
                continue

            comment_find = re.search("\((.*?)\)", row)
            if comment_find:
                comment_find.group(1)
                comment_str += "{:s}\n".format(comment_find.group(1))
                continue

            if 'Event' in row[:5]:
                # Is an event header row
                if counter > 0:
                    # Add magnitudes and origins to previous event
                    # and previous event to catalogue
                    Event.origins = origins
                    Event.magnitudes = magnitudes
                    if len(Event.origins) and len(Event.magnitudes):
                        Event.assign_magnitudes_to_origins()
                        Event.comment = comment_str
                        #print "%s - %s" % (Event.id, Event.description)
                        #print Event.comment
                        if self._acceptance(Event):
                            Event.comment = ""
                            self.catalogue.events.append(Event)

                
                # Get a new event
                Event = get_event_header_row(row.rstrip('\n'))
                comment_str = ""
                origins = []
                magnitudes = []
                counter += 1
                continue

            if row.rstrip('\n') == origin_header:
                is_origin = True
                is_magnitude = False
                continue
            elif row.strip('\n') == magnitude_header:
                is_origin = False
                is_magnitude = True
                continue
            else:
                pass
            
            if is_magnitude and len(row.strip('\n')) == 38:
                # Is a magnitude row
                mag = get_event_magnitude(row.strip('\n'),
                                          Event.id,
                                          self.selected_magnitude_agencies)
#                                          ,self.selected_magnitude_types)

                if mag:
                    magnitudes.append(mag)
                continue

            if is_origin and len(row.strip('\n')) == 136:
                # Is an origin row
                orig = get_event_origin_row(row.strip('\n'),
                                            self.selected_origin_agencies)
                if orig:
                    origins.append(orig)

        if len(self.rejected_catalogue):
            # Turn list of rejected events into its own instance of
            # ISFCatalogue
            self.rejected_catalogue = ISFCatalogue(
                identifier + "-R",
                name + " - Rejected",
                events=self.rejected_catalogue)
        return self.catalogue

    def _acceptance(self, event):
        """
        Determines whether to accept the event according to the magnitude
        and keyword criteria
        :param event:
            Event as instance of Event class
        :returns:
            True (if event is accepted), False otherwise
        """
        # Magnitude rejection - based on an "any" criterion
        valid_magnitude = False
        for mag in event.magnitudes:
            if (mag.value >= self.lower_mag) and (mag.value <= self.upper_mag):
                valid_magnitude = True
                break
        if not valid_magnitude:
            return False
        for keyword in self.rejection_keywords:
            if keyword.lower() in event.comment.lower():
                self.rejected_catalogue.append(event)
                return False
        return True


