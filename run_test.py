#!/opt/local/bin/python

# % load_ext autoreload
# % autoreload 2

import eqcat.isc_downloader as isc

cat1 = isc.ISCBulletinUrl()

cat1.UseMirror()
cat1.SetField("OutputFormat","ISF")
cat1.SetField("StartYear","2000")
cat1.SetField("EndYear","2004")
#cat1.ListFields()
cat1.GetCatalogue("Example_Catalogue2.txt",SplitYears=1)

#cat1.UseMirror()
#cat1.SetField("OutputFormat","FMCSV")
#cat1.SetField("StartYear","2000")
#cat1.SetField("EndYear","2004")
#cat1.ListFields()
#cat1.GetCatalogue("outputs/Example_FM_Catalogue.txt")

#cat1.SaveSettings("outputs/Example_Settings.par")
#cat2 = isc.ISCBulletinUrl()
#cat2.LoadSettings("outputs/Example_Settings.par")
#cat2.ListFields()
#cat2.GetCatalogue("outputs/Example_Catalogue.txt")
