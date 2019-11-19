# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JoinSplit
                                 A QGIS plugin
 JoinSplit
                              -------------------
        begin                : 2015-02-25
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Pedro Tarroso
        email                : ptarroso@cibio.up.pt
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; version 3.                              *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import map
from builtins import zip
from builtins import object
from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QCoreApplication
from PyQt5.QtCore import QThread, QVariant
from qgis.core import QgsProject, QgsMessageLog, QgsVectorLayerJoinInfo
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsField, QgsFeature
from qgis.core import QgsGeometry, QgsVectorFileWriter

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .JoinSplit_dialog import JoinSplitDialog
import os.path

def getListFields(lyr):
    # Returns a list of fields for a layer
    Fields = lyr.fields()
    FNames = [field.name() for field in Fields]
    return(FNames)


class Worker(QObject):
    def __init__(self, sp, grd, jFieldName, outFolder, splits, incZero, 
                 *args, **kwargs):
        QObject.__init__(self, *args, **kwargs)
        self.sp = sp
        self.grd = grd
        self.jFieldName = jFieldName
        if outFolder[-1] != '/' or outFolder[-1] != '\\':
            outFolder += '/'
        self.outFolder = outFolder
        self.splits = splits
        self.incZero = incZero
        self.crs = grd.crs().authid()
        self.geomType = grd.wkbType()


    def joinSpData(self):
        # join sp and grd tables based on a common field
        self.status.emit("Joining tables", "")
        joinInfo = QgsVectorLayerJoinInfo()
        joinInfo.setJoinFieldName(self.jFieldName)
        joinInfo.setTargetFieldName(self.jFieldName)
        joinInfo.setJoinLayerId(self.sp.id())
        joinInfo.setUsingMemoryCache(False)
        joinInfo.setJoinLayer(self.sp)
        self.grd.addJoin(joinInfo)
        self.grd.updateFields()

    def getAttrsGeo(self):
        # Compiles all data to two lists:
        #  geom - list of geometries: [geom1, geom2, ... geom_n] for n Features
        #  attrs- list of attrs: [[a1_grd1, a1_grd2, a1_grd3, a1_grd(m)], 
        #                         [a2_grd1, a2_grd2, a2_grid3, a1_grd(m)],
        #                         [a(n)_grd1, a(n)_grd2, a(n)_grd, a(n)grd(m)]]
        #                        for m Attributes and for n Features
        self.status.emit("Extracting features", "")
        attributes = []
        geom = []
        self.totalcounter = self.grd.featureCount()
        iter = self.grd.getFeatures()
        i = 1
        for feature in iter:
            self.updateProgress(i)
            geom.append(feature.geometry().asWkb())
            attributes.append(feature.attributes())
            i += 1
        attrs = [list(x) for x in zip(*attributes)]

        self.geom = geom
        self.attrs = attrs

    def getDataField(self, fName):
        # get data from field fID in layer
        allfields = getListFields(self.grd)
        gridFID = allfields.index(self.jFieldName)
        fID = allfields.index(fName)
        geom = self.geom
        attrs = self.attrs

        if self.incZero:
            myData = [x for x in zip(geom, attrs[gridFID], attrs[fID])]
        else:
            onlyData = [x for x in zip(geom, attrs[gridFID], attrs[fID]) if x[2] != None]
            myData = [x for x in onlyData if int(x[2]) != 0]
        self.fieldData = myData

    def createLayer(self, fieldName):
        # create layer
        lname = "%s?crs=%s" % (QgsWkbTypes.displayString(self.geomType), self.crs)
        vl = QgsVectorLayer(lname, fieldName, "memory")
        pr = vl.dataProvider()
        
        # Enter editing mode
        vl.startEditing()
        
        # add fields
        pr.addAttributes([QgsField(self.jFieldName, QVariant.Int),
                          QgsField("value",  QVariant.Double)])
        
        def addFet(feature):
            # add a feature to pr
            fet = QgsFeature()
            geo = QgsGeometry()
            QgsGeometry.fromWkb(geo, feature[0])
            fet.setGeometry(geo)
            fet.setAttributes([feature[1], feature[2]])
            pr.addFeatures([fet])
        
        res = list(map(addFet, self.fieldData))
        
        # Commit changes
        vl.commitChanges()
        vl.updateExtents()
        self.vl = vl

    def saveSHP(self, shpPath, load=True):
        writeVector = QgsVectorFileWriter.writeAsVectorFormat
        error = writeVector(self.vl, shpPath, "UTF-8", driverName="ESRI Shapefile")

    def updateProgress(self, i):
        progress = int(i / float(self.totalcounter) * 100)
        self.progress.emit(progress)

    def run(self):
        try:
            self.joinSpData()
            self.getAttrsGeo()

            i = 1
            for fieldName in self.splits:
                fJoinName = "%s_%s" % (self.sp.name(), fieldName)
                self.getDataField(fJoinName)
                self.createLayer(fieldName)
                shpPath = "%s%s.shp" % (self.outFolder, fieldName.replace(" ", "_"))
                self.saveSHP(shpPath)
                self.lyrInfo.emit(shpPath, self.vl.name())
                i += 1

        except:
            import traceback
            self.error.emit(traceback.format_exc())
            self.finished.emit(False)

        else:
            self.finished.emit(True)

    def kill(self):
        self.abort = True

    progress = pyqtSignal(int)
    status = pyqtSignal(str, str)
    error = pyqtSignal(str)
    killed = pyqtSignal()
    finished = pyqtSignal(bool)
    lyrInfo = pyqtSignal(str, str)


class JoinSplit(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'JoinSplit_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = JoinSplitDialog(iface)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&JoinSplit')
        # TODO: We are going to let the user set this up in a future iteration
        if self.iface.pluginToolBar():
            self.toolbar = self.iface.pluginToolBar()
        else:
            self.toolbar = self.iface.addToolBar(u'JoinSplit')
        self.toolbar.setObjectName(u'JoinSplit')

        # Init a style for display
        self.styleFile = False

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('JoinSplit', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/JoinSplit/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'JoinSplit'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&JoinSplit'),
                action)
            self.iface.removeToolBarIcon(action)

    def loadLayer(self, shppath, layername):
        vlayer = QgsVectorLayer(shppath, layername, "ogr")
        if self.styleFile:
            vlayer.loadNamedStyle(self.styleFile)
        QgsProject.instance().addMapLayer(vlayer)

    def run(self):
        """Run method that performs all the real work"""

        layerTree = QgsProject.instance().layerTreeRoot().findLayers()
        allLayers = [lyr.layer() for lyr in layerTree]
        allLyrNames = [lyr.name() for lyr in allLayers]

        # Update combos
        self.dlg.updateCombos(allLyrNames)

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()

        # See if OK was pressed
        if result:
            spLayerName = self.dlg.getJoinTable()
            grdLayerName = self.dlg.getGridLayer()
            jFieldName = self.dlg.getJoinField()
            outFolder = self.dlg.getOutFolder()
            splits = self.dlg.getSplits()
            incZero = self.dlg.getIncZero()
            self.styleFile = self.dlg.getStyleFile()

            # Get correct layers from Graphical Interface
            sp = allLayers[allLyrNames.index(spLayerName)]
            grd = allLayers[allLyrNames.index(grdLayerName)]
            
            if outFolder == "":
                self.dlg.errorMsg("Output folder is mandatory!", "")

            elif splits == []:
                self.dlg.errorMsg("At least one column should be selected.", "")

            elif not grd.geometryType() < 4:
                self.dlg.errorMsg("Spatial layer must have geometry.", "")

            else:
                self.dlg.setProgressBar("Processing", "", 100)

                thread = self.thread = QThread()
                worker = self.worker = Worker(sp, grd, jFieldName, outFolder, 
                                              splits, incZero)
                worker.moveToThread(thread)
                thread.started.connect(worker.run)
                worker.progress.connect(self.dlg.ProgressBar)
                worker.status.connect(self.dlg.showMessage)
                worker.error.connect(QgsMessageLog.logMessage)
                worker.lyrInfo.connect(self.loadLayer)
                worker.finished.connect(worker.deleteLater)
                thread.finished.connect(thread.deleteLater)
                worker.finished.connect(thread.quit)
                thread.start()
