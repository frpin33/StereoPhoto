# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui-optionWindow.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
import os
import resources

class Ui_optionWindow(object):
    def setupUi(self, optionWindow):
        optionWindow.setObjectName("optionWindow")
        optionWindow.resize(436, 524)
        self.label_5 = QtWidgets.QLabel(optionWindow)
        self.label_5.setGeometry(QtCore.QRect(70, 10, 91, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(optionWindow)
        self.label_6.setGeometry(QtCore.QRect(270, 10, 91, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.groupBoxRed = dropedit(optionWindow)
        self.groupBoxRed.setGeometry(QtCore.QRect(10, 30, 201, 271))
        self.groupBoxRed.setTitle("")
        self.groupBoxRed.setObjectName("groupBoxRed")
        self.importLineRed = QtWidgets.QLineEdit(self.groupBoxRed)
        self.importLineRed.setGeometry(QtCore.QRect(10, 20, 161, 20))
        self.importLineRed.setText("")
        self.importLineRed.setReadOnly(True)
        self.importLineRed.setObjectName("importLineRed")
        self.importToolRed = QtWidgets.QToolButton(self.groupBoxRed)
        self.importToolRed.setGeometry(QtCore.QRect(170, 20, 25, 19))
        self.importToolRed.setObjectName("importToolRed")
        self.boxOrientationRed = QtWidgets.QComboBox(self.groupBoxRed)
        self.boxOrientationRed.setEnabled(False)
        self.boxOrientationRed.setGeometry(QtCore.QRect(85, 60, 101, 22))
        self.boxOrientationRed.setObjectName("boxOrientationRed")
        self.boxOrientationRed.addItem("")
        self.boxOrientationRed.addItem("")
        self.boxOrientationRed.addItem("")
        self.boxOrientationRed.addItem("")
        self.label = QtWidgets.QLabel(self.groupBoxRed)
        self.label.setEnabled(False)
        self.label.setGeometry(QtCore.QRect(10, 60, 61, 20))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.groupBoxRed)
        self.label_2.setEnabled(False)
        self.label_2.setGeometry(QtCore.QRect(10, 100, 61, 16))
        self.label_2.setObjectName("label_2")
        self.boxMiroirRed = QtWidgets.QComboBox(self.groupBoxRed)
        self.boxMiroirRed.setEnabled(False)
        self.boxMiroirRed.setGeometry(QtCore.QRect(85, 100, 101, 22))
        self.boxMiroirRed.setObjectName("boxMiroirRed")
        self.boxMiroirRed.addItem("")
        self.boxMiroirRed.addItem("")
        self.boxMiroirRed.addItem("")
        self.importButtonRed = QtWidgets.QPushButton(self.groupBoxRed)
        self.importButtonRed.setEnabled(False)
        self.importButtonRed.setGeometry(QtCore.QRect(65, 230, 75, 23))
        self.importButtonRed.setObjectName("importButtonRed")
        self.graphicsViewRed = QtWidgets.QGraphicsView(self.groupBoxRed)
        self.graphicsViewRed.setGeometry(QtCore.QRect(10, 130, 181, 91))
        self.graphicsViewRed.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsViewRed.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsViewRed.setObjectName("graphicsViewRed")
        self.importDoneRed = QtWidgets.QLabel(self.groupBoxRed)
        self.importDoneRed.setGeometry(QtCore.QRect(150, 233, 21, 16))
        self.importDoneRed.setStyleSheet("image: url(:/Anaglyph/Icons/redCross.png);")
        self.importDoneRed.setText("")
        self.importDoneRed.setObjectName("importDoneRed")
        self.groupBoxCyan = dropedit(optionWindow)
        self.groupBoxCyan.setGeometry(QtCore.QRect(220, 30, 201, 271))
        self.groupBoxCyan.setTitle("")
        self.groupBoxCyan.setObjectName("groupBoxCyan")
        self.importLineCyan = QtWidgets.QLineEdit(self.groupBoxCyan)
        self.importLineCyan.setGeometry(QtCore.QRect(10, 20, 161, 20))
        self.importLineCyan.setText("")
        self.importLineCyan.setReadOnly(True)
        self.importLineCyan.setObjectName("importLineCyan")
        self.importToolCyan = QtWidgets.QToolButton(self.groupBoxCyan)
        self.importToolCyan.setGeometry(QtCore.QRect(170, 20, 25, 19))
        self.importToolCyan.setObjectName("importToolCyan")
        self.label_4 = QtWidgets.QLabel(self.groupBoxCyan)
        self.label_4.setEnabled(False)
        self.label_4.setGeometry(QtCore.QRect(10, 100, 61, 16))
        self.label_4.setObjectName("label_4")
        self.label_3 = QtWidgets.QLabel(self.groupBoxCyan)
        self.label_3.setEnabled(False)
        self.label_3.setGeometry(QtCore.QRect(10, 60, 61, 20))
        self.label_3.setObjectName("label_3")
        self.boxMiroirCyan = QtWidgets.QComboBox(self.groupBoxCyan)
        self.boxMiroirCyan.setEnabled(False)
        self.boxMiroirCyan.setGeometry(QtCore.QRect(85, 100, 101, 22))
        self.boxMiroirCyan.setObjectName("boxMiroirCyan")
        self.boxMiroirCyan.addItem("")
        self.boxMiroirCyan.addItem("")
        self.boxMiroirCyan.addItem("")
        self.boxOrientationCyan = QtWidgets.QComboBox(self.groupBoxCyan)
        self.boxOrientationCyan.setEnabled(False)
        self.boxOrientationCyan.setGeometry(QtCore.QRect(85, 60, 101, 22))
        self.boxOrientationCyan.setObjectName("boxOrientationCyan")
        self.boxOrientationCyan.addItem("")
        self.boxOrientationCyan.addItem("")
        self.boxOrientationCyan.addItem("")
        self.boxOrientationCyan.addItem("")
        self.importButtonCyan = QtWidgets.QPushButton(self.groupBoxCyan)
        self.importButtonCyan.setEnabled(False)
        self.importButtonCyan.setGeometry(QtCore.QRect(65, 230, 75, 23))
        self.importButtonCyan.setObjectName("importButtonCyan")
        self.graphicsViewCyan = QtWidgets.QGraphicsView(self.groupBoxCyan)
        self.graphicsViewCyan.setGeometry(QtCore.QRect(10, 130, 181, 91))
        self.graphicsViewCyan.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsViewCyan.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsViewCyan.setObjectName("graphicsViewCyan")
        self.importDoneCyan = QtWidgets.QLabel(self.groupBoxCyan)
        self.importDoneCyan.setGeometry(QtCore.QRect(150, 233, 21, 16))
        self.importDoneCyan.setStyleSheet("image: url(:/Anaglyph/Icons/redCross.png);")
        self.importDoneCyan.setText("")
        self.importDoneCyan.setObjectName("importDoneCyan")
        self.label_9 = QtWidgets.QLabel(optionWindow)
        self.label_9.setGeometry(QtCore.QRect(180, 340, 101, 16))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.groupBox = QtWidgets.QGroupBox(optionWindow)
        self.groupBox.setGeometry(QtCore.QRect(90, 430, 261, 71))
        self.groupBox.setTitle("")
        self.groupBox.setObjectName("groupBox")
        self.radioAnaglyph = QtWidgets.QRadioButton(self.groupBox)
        self.radioAnaglyph.setGeometry(QtCore.QRect(130, 40, 82, 17))
        self.radioAnaglyph.setObjectName("radioAnaglyph")
        self.radioSepare = QtWidgets.QRadioButton(self.groupBox)
        self.radioSepare.setGeometry(QtCore.QRect(130, 10, 121, 17))
        self.radioSepare.setChecked(True)
        self.radioSepare.setObjectName("radioSepare")
        self.affichageButton = QtWidgets.QPushButton(self.groupBox)
        self.affichageButton.setEnabled(False)
        self.affichageButton.setGeometry(QtCore.QRect(20, 25, 75, 23))
        self.affichageButton.setObjectName("affichageButton")
        self.groupBoxSuper = QtWidgets.QGroupBox(optionWindow)
        self.groupBoxSuper.setEnabled(False)
        self.groupBoxSuper.setGeometry(QtCore.QRect(90, 360, 261, 51))
        self.groupBoxSuper.setTitle("")
        self.groupBoxSuper.setObjectName("groupBoxSuper")
        self.radioCouleur = QtWidgets.QRadioButton(self.groupBoxSuper)
        self.radioCouleur.setGeometry(QtCore.QRect(20, 25, 82, 17))
        self.radioCouleur.setObjectName("radioCouleur")
        self.radioNoirBlanc = QtWidgets.QRadioButton(self.groupBoxSuper)
        self.radioNoirBlanc.setGeometry(QtCore.QRect(20, 5, 82, 17))
        self.radioNoirBlanc.setChecked(True)
        self.radioNoirBlanc.setObjectName("radioNoirBlanc")
        self.saveSuper = QtWidgets.QPushButton(self.groupBoxSuper)
        self.saveSuper.setGeometry(QtCore.QRect(150, 15, 75, 23))
        self.saveSuper.setObjectName("saveSuper")
        self.panButton = QtWidgets.QPushButton(optionWindow)
        self.panButton.setEnabled(False)
        self.panButton.setGeometry(QtCore.QRect(140, 310, 61, 23))
        self.panButton.setCheckable(True)
        self.panButton.setObjectName("panButton")
        self.offsetButton = QtWidgets.QPushButton(optionWindow)
        self.offsetButton.setEnabled(False)
        self.offsetButton.setGeometry(QtCore.QRect(230, 310, 61, 23))
        self.offsetButton.setCheckable(True)
        self.offsetButton.setObjectName("offsetButton")
        self.groupBoxCyan.raise_()
        self.label_5.raise_()
        self.label_6.raise_()
        self.label_9.raise_()
        self.groupBoxRed.raise_()
        self.groupBox.raise_()
        self.groupBoxSuper.raise_()
        self.panButton.raise_()
        self.offsetButton.raise_()

        self.retranslateUi(optionWindow)
        QtCore.QMetaObject.connectSlotsByName(optionWindow)

    def retranslateUi(self, optionWindow):
        _translate = QtCore.QCoreApplication.translate
        optionWindow.setWindowTitle(_translate("optionWindow", "Menu des options"))
        self.label_5.setText(_translate("optionWindow", "Image Gauche"))
        self.label_6.setText(_translate("optionWindow", "Image Droite"))
        self.importToolRed.setText(_translate("optionWindow", "..."))
        self.boxOrientationRed.setItemText(0, _translate("optionWindow", "0°"))
        self.boxOrientationRed.setItemText(1, _translate("optionWindow", "90°"))
        self.boxOrientationRed.setItemText(2, _translate("optionWindow", "180°"))
        self.boxOrientationRed.setItemText(3, _translate("optionWindow", "270°"))
        self.label.setText(_translate("optionWindow", "Rotation"))
        self.label_2.setText(_translate("optionWindow", "Effet miroir"))
        self.boxMiroirRed.setItemText(0, _translate("optionWindow", "Aucun"))
        self.boxMiroirRed.setItemText(1, _translate("optionWindow", "Horizontal"))
        self.boxMiroirRed.setItemText(2, _translate("optionWindow", "Vertical"))
        self.importButtonRed.setText(_translate("optionWindow", "Import"))
        self.importToolCyan.setText(_translate("optionWindow", "..."))
        self.label_4.setText(_translate("optionWindow", "Effet miroir"))
        self.label_3.setText(_translate("optionWindow", "Rotation"))
        self.boxMiroirCyan.setItemText(0, _translate("optionWindow", "Aucun"))
        self.boxMiroirCyan.setItemText(1, _translate("optionWindow", "Horizontal"))
        self.boxMiroirCyan.setItemText(2, _translate("optionWindow", "Vertical"))
        self.boxOrientationCyan.setItemText(0, _translate("optionWindow", "0°"))
        self.boxOrientationCyan.setItemText(1, _translate("optionWindow", "90°"))
        self.boxOrientationCyan.setItemText(2, _translate("optionWindow", "180°"))
        self.boxOrientationCyan.setItemText(3, _translate("optionWindow", "270°"))
        self.importButtonCyan.setText(_translate("optionWindow", "Import"))
        self.label_9.setText(_translate("optionWindow", "Anaglyphe"))
        self.radioAnaglyph.setText(_translate("optionWindow", "Anaglyphe"))
        self.radioSepare.setText(_translate("optionWindow", "Fenêtres séparées"))
        self.affichageButton.setText(_translate("optionWindow", "Afficher"))
        self.radioCouleur.setText(_translate("optionWindow", "Couleur"))
        self.radioNoirBlanc.setText(_translate("optionWindow", "Noir et blanc"))
        self.saveSuper.setText(_translate("optionWindow", "Enregistrer"))
        self.panButton.setText(_translate("optionWindow", "Pan"))
        self.offsetButton.setText(_translate("optionWindow", "Offset"))



class dropedit(QtWidgets.QGroupBox):   

    def __init__(self, parent=None):
        super(dropedit, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.accept()
        
    def dropEvent(self, event):
        fileURL = event.mimeData().urls()[0].toString()
        try :
            fileName = fileURL.split('file:///')[1]
        except :
            fileName = fileURL.split('file:')[1]
        for child in self.children(): 
            if child.metaObject().className() == "QLineEdit":
                child.setText(fileName)



class optionWindow(QtWidgets.QMainWindow): 
    closeWindow = pyqtSignal()
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = Ui_optionWindow()
        self.ui.setupUi(self)
        self.ui.importToolCyan.clicked.connect(self.showImportCyan)
        self.ui.importToolRed.clicked.connect(self.showImportRed)
        self.ctrlClick = False

    def showImportCyan(self) :
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Import picture', os.path.dirname(os.path.abspath(__file__)),"Image (*.png, *.jpg, *.tif)")[0]
        if fname:
            self.ui.importLineCyan.setText(fname)

    def showImportRed(self) :
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Import picture', os.path.dirname(os.path.abspath(__file__)), "Image (*.png, *.jpg, *.tif)")[0]
        if fname:
            self.ui.importLineRed.setText(fname)
            
    def closeEvent(self,event):
        self.closeWindow.emit()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Control:
            self.ctrlClick = True

    def keyReleaseEvent(self, event):
        self.ctrlClick = False







