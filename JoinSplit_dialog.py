# -*- coding: utf-8 -*-
"""
/***************************************************************************
 JoinSplitDialog
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

from builtins import str
from builtins import range
import os

from PyQt5 import QtWidgets
from qgis.PyQt import QtGui, uic, QtCore
from qgis.core import QgsProject, Qgis

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'JoinSplit_dialog_base.ui'))


class JoinSplitDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, iface, parent=None):
        """Constructor."""
        super(JoinSplitDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.OutputButton.clicked.connect(self.outFolder)
        self.JoinTableCombo.currentIndexChanged.connect(self.updateFields)
        self.JoinFieldCombo.currentIndexChanged.connect(self.populateSplits) 
        self.checkStyle.stateChanged.connect(self.styleState)
        self.styleButton.clicked.connect(self.styleFile)

    def outFolder(self):
        # Show the folder dialog for output
        self.OutputLine.clear()
        fileDialog = QtWidgets.QFileDialog()
        outFolderName = fileDialog.getExistingDirectory(self, "Open a folder", ".", QtWidgets.QFileDialog.ShowDirsOnly)
        outPath = QtCore.QFileInfo(outFolderName).absoluteFilePath()
        if outFolderName:
            self.OutputLine.clear()
            self.OutputLine.insert(outPath)

    def styleFile(self):
        # Show the file dialog for choosing a style file
        self.styleLine.clear()
        fileDialog = QtWidgets.QFileDialog()
        styleFileName = fileDialog.getOpenFileName(self, "Open style file",
                                                   '', "QML Files (*.qml)")[0]
        styleFileName = QtCore.QFileInfo(styleFileName).absoluteFilePath()
        if styleFileName:
            self.styleLine.clear()
            self.styleLine.insert(styleFileName)

    def getOutFolder(self):
        return(self.OutputLine.text())

    def getJoinTable(self):
        return(str(self.JoinTableCombo.currentText()))

    def getJoinField(self):
        return(str(self.JoinFieldCombo.currentText()))

    def getGridLayer(self):
        return(str(self.GridLayerCombo.currentText()))

    def getIncZero(self):
        return(bool(self.includeZero.checkState()))

    def getcheckStyle(self):
        return(bool(self.checkStyle.checkState()))

    def getStyleFile(self):
        if self.getcheckStyle():
            return(self.styleLine.text())
        else:
            return(False)

    def updateCombos(self, items):
        if len(items) > 0:
            self.GridLayerCombo.clear()
            self.JoinTableCombo.clear()
            for item in items:
                self.GridLayerCombo.addItem(item)
                self.JoinTableCombo.addItem(item)

    def updateFields(self):
        joinTable = self.getJoinTable()
        if joinTable != "":
            allLayers = [layer for layer in QgsProject.instance().mapLayers().values()]
            allLyrNames = [lyr.name() for lyr in allLayers]
            if joinTable in allLyrNames:
                lyr = allLayers[allLyrNames.index(joinTable)]
                fields = lyr.fields()
                self.JoinFieldCombo.clear()
                fieldNames = [self.JoinFieldCombo.addItem(f.name()) for f in fields]

    def populateSplits(self):
        joinTable = self.getJoinTable()
        if joinTable != "":
            allLayers = [layer for layer in QgsProject.instance().mapLayers().values()]
            allLyrNames = [lyr.name() for lyr in allLayers]
            if joinTable in allLyrNames:
                lyr = allLayers[allLyrNames.index(joinTable)]
                fields = lyr.fields()
                self.splitFields.clear()
                for item in [f.name() for f in fields]:
                    if item != self.getJoinField():
                        self.splitFields.addItem(item)

    def getSplits(self):
        splits = []
        count = self.splitFields.count()
        for i in range(0, count):
            item = self.splitFields.item(i)
            if item.isSelected():
                splits.append(item.text())
        return(splits)

    def styleState(self, enable):
        self.styleButton.setEnabled(bool(enable))
        self.styleLine.setEnabled(bool(enable))

    def setProgressBar(self, main, text, maxVal=100):
        self.widget = self.iface.messageBar().createMessage(main, text)
        self.prgBar = QtWidgets.QProgressBar()
        self.prgBar.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.prgBar.setValue(0)
        self.prgBar.setMaximum(maxVal)
        self.widget.layout().addWidget(self.prgBar)
        self.iface.messageBar().pushWidget(self.widget, Qgis.Info)
        
    def showMessage(self, main, txt):
        self.widget.setTitle(main)
        self.widget.setText(txt)

    def ProgressBar(self, value):
        self.prgBar.setValue(value)
        if (value == self.prgBar.maximum()):
            self.iface.messageBar().clearWidgets()
            self.iface.mapCanvas().refresh()

    def emitMsg(self, main, text, type):
        # Emits a message to QGIS.
        # type is either Qgis.Warning or Qgis.Critical
        # TODO: Replace the warnMsg and the errorMsg to this function!!!
        msg = self.iface.messageBar().createMessage(main, text)
        self.iface.messageBar().pushWidget(msg, type)
    

    def warnMsg(self, main, text):
        self.warn = self.iface.messageBar().createMessage(main, text)
        self.iface.messageBar().pushWidget(self.warn)

    def errorMsg(self, main, text):
        self.warn = self.iface.messageBar().createMessage(main, text)
        self.iface.messageBar().pushWidget(self.warn)
