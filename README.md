# CATALOGUE TOOLKIT

The Catalogue Toolkit is an open-source set of Python tools for the compilation
and harmonisation of earthquake catalogues.

## FEATURES

Within the toolkit it is possible to do the following:

* Read/Write Earthquake Catalogues from common format (ISC (ISF), GCMT, csv)
* Search for duplicate events from multiple catalogues
* Using Pandas, query database for events reported in common magnitude scales
* Apply orthogonal regression techniques to compare magnitude scales within
  a database
* Homogenise a catalogue into a common magnitude scale by applying a user-
  defined hierarchy of conversion models

## DEPENDENCIES

The Catalogue toolkit requires the following dependencies:
1. [NumPy/Scipy](http://www.scipy.org/)

2. [h5py](http://www.h5py.org)

3. [PyTables] (http://www.pytables.org/)

4. [Pandas](http://pandas.pydata.org/)

5. [Matplotlib](http://matplotlib.org/)

6. [Basemap](http://matplotlib.org/basemap/)


## INSTALLATION

### WINDOWS (Vista/7/8)

The simplest process is to use the PythonXY distribution, which will
install all of the above dependences (except Basemap). This can be downloaded
from here: https://code.google.com/p/pythonxy/

The Basemap package will need to be installed separately. We recommend using
the Windows Binary installers here: http://sourceforge.net/projects/matplotlib/files/matplotlib-toolkits/

To install the catalogue toolkit simply download the zipped folder from
the main repository (or clone if you have Github installed) and unzip. 
Then add these manually to the Python Path by navigating to:

* Control Panel -> System -> Advanced System Settings -> Environment Variables

If no pythonpath exists create a new pythonpath and add:

> c:\path\to\catalogue_toolkit_unzipped\

otherwise append the above statement to an existing python path

### OSX/LINUX

The most universal approach to install the dependencies is via the python
package index (pip) (or the package manager of your preferred distro). Follow
the instructions given in the dependency links above.

N.B. Install h5py and PyTables before installing Pandas

Alternatively, [Anaconda](http://docs.continuum.io/anaconda/index) might prove
simpler if the above packages are not already installed on your system.

To download the toolkit simply open the terminal, navigate to a directory of
your choosing and clone the current repository:

> git clone https://github.com/GEMScienceTools/catalogue_toolkit.git

To install, simply add the folder to the pythonpath. Open your profile file
(~/.profile or ~/.bash_profile) and add the following line to the bottom:

> export PYTHONPATH=/full/path/to/catalogue/toolkit/folder/:$PYTHONPATH 

Then restart or source the terminal to complete installation


# LICENSE

Copyright (c) 2015 GEM Foundation

The Catalogue Toolkit is free software: you can redistribute 
it and/or modify it under the terms of the GNU Affero General Public 
License as published by the Free Software Foundation, either version 
3 of the License, or (at your option) any later version.

You should have received a copy of the GNU Affero General Public License
with this download. If not, see <http://www.gnu.org/licenses/>


# DISCLAIMER
 
The software Catalogue Toolkit provided herein 
is released as a prototype implementation on behalf of 
scientists and engineers working within the GEM Foundation (Global 
Earthquake Model). 

It is distributed for the purpose of open collaboration and in the 
hope that it will be useful to the scientific, engineering, disaster
risk and software design communities. 

The software is NOT distributed as part of GEM’s OpenQuake suite 
(http://www.globalquakemodel.org/openquake) and must be considered as a 
separate entity. The software provided herein is designed and implemented 
by scientific staff. It is not developed to the design standards, nor 
subject to same level of critical review by professional software 
developers, as GEM’s OpenQuake software suite.  

Feedback and contribution to the software is welcome, and can be 
directed to the hazard scientific staff of the GEM Model Facility 
(hazard@globalquakemodel.org). 

The Catalogue Toolkit is therefore distributed WITHOUT 
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
for more details.

The GEM Foundation, and the authors of the software, assume no 
liability for use of the software. 
