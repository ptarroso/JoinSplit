# JoinSplit

JoinSplit is a plug-in for QGIS (version >= 2.0; http://www.qgis.org). It joins 
a spatial layer with a table with no geometry and exports all fields from the 
table as independent shapefiles. Spatial layer and table must share a common 
field with the same name. 

The original purpose of this plug-in was to generate individual species 
shapefiles using a single polygon grid for the area and a cross table with 
species presence per grid ID but without geometry. The plug-in can be useful for
other situations as well (e.g. split all fields of a shapefile by joining to 
itself). 

Currently, JoinSplit only support numeric fields.

## Features

The JoinSplit plug-in allows to:
 
* choose a spatial layer from the table of contents
* choose a table to join from the table of contents
* choose a common field between the layers
* select the fields to export (from the join table)
* include zeros (useful for limitng exported shapefiles only to presences)
* select an optional style file (.qml) to display all created shapefiles
* choose and output folder to export the shapefiles

## Installation

Download the files to your computer in a folder JoinSplit. Copy this folder to
the plug-in folder of your QGIS instalation. Usually is found in the 
PATH_TO_YOUR_USER/.qgis2/python/plugins/ (check http://docs.qgis.org/testing/en/docs/pyqgis_developer_cookbook/plugins.html for more details). 
In QGIS, activate the JoinSplit from the plug-in manager.

