# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JoinSplit
                                 A QGIS plugin
 JoinSplit
                             -------------------
        begin                : 2015-02-25
        copyright            : (C) 2015 by Pedro Tarroso
        email                : ptarroso@cibio.up.pt
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load JoinSplit class from file JoinSplit.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .JoinSplit import JoinSplit
    return JoinSplit(iface)
