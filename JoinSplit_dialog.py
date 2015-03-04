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
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic, QtCore

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'JoinSplit_dialog_base.ui'))


class JoinSplitDialog(QtGui.QDialog, FORM_CLASS):
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

    def outFolder(self):
        # Show the folder dialog for output
        self.OutputLine.clear()
        fileDialog = QtGui.QFileDialog()
        outFolderName = fileDialog.getExistingDirectory(self, "Open a folder", ".", QtGui.QFileDialog.ShowDirsOnly)
        outPath = QtCore.QFileInfo(outFolderName).absoluteFilePath()
        if outFolderName:
            self.OutputLine.clear()
            self.OutputLine.insert(outPath)

    def getOutFolder(self):
        return(self.OutputLine.text())

    def getJoinTable(self):
        return(unicode(self.JoinTableCombo.currentText()))

    def getJoinField(self):
        return(unicode(self.JoinFieldCombo.currentText()))

    def getGridLayer(self):
        return(unicode(self.GridLayerCombo.currentText()))

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
            allLayers = self.iface.legendInterface().layers()
            allLyrNames = [lyr.name() for lyr in allLayers]
            if joinTable in allLyrNames:
                lyr = allLayers[allLyrNames.index(joinTable)]
                fields = lyr.pendingFields()
                self.JoinFieldCombo.clear()
                fieldNames = [self.JoinFieldCombo.addItem(f.name()) for f in fields]


    def setProgressBar(self, main, text, maxVal=100):
        self.widget = self.iface.messageBar().createMessage(main, text)
        self.prgBar = QtGui.QProgressBar()
        self.prgBar.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.prgBar.setValue(0)
        self.prgBar.setMaximum(maxVal)           
        self.widget.layout().addWidget(self.prgBar)
        self.iface.messageBar().pushWidget(self.widget, 
                                           self.iface.messageBar().INFO)

    def showMessage(self, main, txt):
        self.widget.setTitle(main)
        self.widget.setText(txt)

    def ProgressBar(self, value):
        self.prgBar.setValue(value)
        if (value == self.prgBar.maximum()):
            self.iface.messageBar().clearWidgets()
            self.iface.mapCanvas().refresh()

    def warnMsg(self, main, text):
        self.warn = self.iface.messageBar().createMessage(main, text)
        self.iface.messageBar().pushWidget(self.warn, 
                                           self.iface.messageBar().WARNING)


