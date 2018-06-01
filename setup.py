# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2015-2017 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

url = "https://github.com/GEMScienceTools/catalogue_toolkit"

README = """
The Catalogue Toolkit is an open-source set of Python tools for the compilation
and harmonisation of earthquake catalogues.

Within the toolkit it is possible to do the following:

* Read/Write Earthquake Catalogues from common format (ISC (ISF), GCMT, csv)
* Search for duplicate events from multiple catalogues
* Using Pandas, query database for events reported in common magnitude scales
* Apply orthogonal regression techniques to compare magnitude scales within
  a database
* Homogenise a catalogue into a common magnitude scale by applying
  a user-defined hierarchy of conversion models

Copyright (C) 2015-2017 GEM Foundation
"""

setup(
    name='eqcat',
    version='1.0.0',
    description="""The Catalogue Toolkit is an open-source set of Python tools
    for the compilation and harmonisation of earthquake catalogues.""",
    long_description=README,
    url=url,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'numpy',
        'scipy',
        'h5py',
        'geojson',
        'tables',
        'pandas',
        'matplotlib',
        'basemap',
    ],
    author='GEM Foundation',
    author_email='hazard@globalquakemodel.org',
    maintainer='GEM Foundation',
    maintainer_email='hazard@globalquakemodel.org',
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Scientific/Engineering',
    ),
    keywords="seismic hazard",
    license="AGPL3",
    platforms=["any"],
    package_data={"eqcat": [
        "README.md", "LICENSE"]},
    include_package_data=True,
    zip_safe=False,
)
