#
# LICENSE
#
# Copyright (c) 2015 GEM Foundation
#
# The Catalogue Toolkit is free software: you can redistribute
# it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
#
# You should have received a copy of the GNU Affero General Public License
# with this download. If not, see <http://www.gnu.org/licenses/>

#!/usr/bin/env/python

"""
Utility to download the ISC catalogue from website.
Version 30/10/2015
"""

import urllib2
import collections

class ISCBulletinUrl():

  #---------------------------------------

  def __init__(self):

    # DEFAULT VALUES

    self.BaseServer = "http://www.isc.ac.uk/cgi-bin/web-db-v4?"

    self.Request = collections.OrderedDict()

    # Compulsory fields
    self.Request["CatalogueType"]           = "request=REVIEWED"
    self.Request["OutputFormat"]            = "out_format=CATCSV"
    self.Request["SearchAreaShape"]         = "searchshape=RECT"
    self.Request["RectangleBottomLatitude"] = "bot_lat=36"
    self.Request["RectangleTopLatitude"]    = "top_lat=48"
    self.Request["RectangleLeftLongitude"]  = "left_lon=6"
    self.Request["RectangleRightLongitude"] = "right_lon=19"
    self.Request["CircularLatitude"]        = "ctr_lat="
    self.Request["CircularLongitude"]       = "ctr_lon="
    self.Request["CircularRadius"]          = "radius="
    self.Request["MaxDistanceUnits"]        = "max_dist_units=deg"
    self.Request["SeismicRegionNumber"]     = "srn="
    self.Request["GeogrephicRegionNumber"]  = "grn="
    self.Request["PolygonCoordinates"]      = "coordvals="
    self.Request["StartYear"]               = "start_year=2012"
    self.Request["StartMonth"]              = "start_month=01"
    self.Request["StartDay"]                = "start_day=01"
    self.Request["StartTime"]               = "start_time=00:00:00"
    self.Request["EndYear"]                 = "end_year=2013"
    self.Request["EndMonth"]                = "end_month=12"
    self.Request["EndDay"]                  = "end_day=31"
    self.Request["EndTime"]                 = "end_time=00:00:00"
    self.Request["MinimumDepth"]            = "min_dep="
    self.Request["MaximumDepth"]            = "max_dep="
    self.Request["NoDepthEvents"]           = "null_dep=on"
    self.Request["MinimumMagnitude"]        = "min_mag="
    self.Request["MaximumMagnitude"]        = "max_mag="
    self.Request["NoMagnitudeEvents"]       = "null_mag=on"
    self.Request["MagnitudeType"]           = "req_mag_type="
    self.Request["MagnitudeAgency"]         = "req_mag_agcy="
    self.Request["FocalMechanismAgency"]    = "req_fm_agcy=Any"

    # Optional Fields
    self.Request["IncludePhases"]           = "include_phases=off"
    self.Request["MinimumPhaseNumber"]      = "min_def="
    self.Request["MaximumPhaseNumber"]      = "max_def="
    self.Request["NoKnownPhases"]           = "null_phs="
    self.Request["PrimeOnly"]               = "prime_only="
    self.Request["IncludeMagnitudes"]       = "include_magnitudes=on"
    self.Request["IncludeHeaders"]          = "include_headers=on"
    self.Request["IncludeComments"]         = "include_comments=on"
    self.Request["IncludeLinks"]            = "include_links=off"

  #---------------------------------------

  def UseMirror(self):

    self.BaseServer = "http://isc-mirror.iris.washington.edu/cgi-bin/web-db-v4?"

  #---------------------------------------

  def ListFields(self):

    print "\nCURRENT SETTINGS:\n"

    for Key in self.Request:

      Value = self.Request[Key].split("=")[1]
      if not Value: Value = "[Empty]"
      print "\t" + Key + " = " + Value

  #---------------------------------------

  def SetField(self,field_name,field_value):

    buf = self.Request[field_name]
    buf = buf.split("=")[0]
    self.Request[field_name] = buf + "=%s" % field_value

  #---------------------------------------

  def SaveSettings(self,ParamFile):

    ParFile = open(ParamFile, "w")

    for Key in self.Request:

      Value = self.Request[Key].split("=")[1]
      if not Value: Value = "Null"
      ParFile.write("%s=%s" % (Key,Value))
      if Key != self.Request.keys()[-1]:
        ParFile.write("\n")

    ParFile.close()

  #---------------------------------------

  def LoadSettings(self,ParamFile):

    ParFile = open(ParamFile, "r")

    for Line in ParFile:
      Key = Line.split("=")[0]
      Value = Line.split("=")[1].strip('\n')
      if Value == "Null": Value = ""
      self.SetField(Key,Value)

    ParFile.close()

  #---------------------------------------

  def CreateUrl(self):

    UrlString = self.BaseServer
    for value in self.Request.itervalues():
      UrlString += value + "&"

    return UrlString

  #---------------------------------------

  def DownloadBlock(self):

    UrlString = self.CreateUrl()

    UrlReq = urllib2.Request(UrlString)
    UrlRes = urllib2.urlopen(UrlReq)
    Page = UrlRes.read()

    CatStart = Page.find("DATA_TYPE")
    CatStop = Page.find("STOP")

    if CatStart > -1 and CatStop > -1:

      CatBlock = Page[CatStart:CatStop-1]

    else:

      CatBlock = ""
      print "Warning: Cataloge not available for the selected period"

    return CatBlock

  #---------------------------------------

  def GetCatalogue(self,OutputFile,SplitYears=0):

    if not SplitYears:

      CatBlock = self.DownloadBlock()

    else:

      StartYear = int(self.Request["StartYear"].split("=")[1])
      EndYear = int(self.Request["EndYear"].split("=")[1])

      CatBlock = ""

      for SY in range(StartYear,EndYear,SplitYears):

        EY = min([EndYear,SY+SplitYears-1])
        self.SetField("StartYear",SY)
        self.SetField("EndYear",EY)

        print "Downloading block:",SY,"-",EY
        Chunk = self.DownloadBlock()

        if SY != StartYear:
          # Remove header from data blocks
          Chunk = Chunk.split('\n', 2)[-1]

        CatBlock = CatBlock + Chunk

    CatFile = open(OutputFile, "w")
    CatFile.write("%s" % CatBlock)
    CatFile.close()

