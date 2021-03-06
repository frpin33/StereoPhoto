'''
L'entièreté du code a été réalisé par Frédérick Pineault (frederick.pineault@mffp.gouv.qc.ca)

Ce dossier contient une classe de type QApplication qui permet l'affichage d'images de grandes tailles sur des 
écrans de type Planar

La classe stereoPhoto gère l'application complète via un interface utilisateur
L'application permet de :
    - Importer des fichiers TIF de grandes tailles via un drag n drop
    - Réaliser une rotation de 90°, 180° et 270°
    - Réaliser un effet miroir sur l'horizontal et la verticale
    - Afficher les deux images importées
    - Superposer automatiquement les images en fonction d'un pourcentage choisi par l'utilisateur
    - Offrir une interface de navigation qui permet le déplacement, le zoom (CTRL+Roulette) et le traçage (Click & 1,2,3,ESC) 
    - Offrir un déplacement de l'image de droite pour ajuster l'altitude (Roulette)
    - Rehausser les couleurs des images via une nouvelle fenêtre intéractive 
    - Traçage de forme géolocalisée
    - Communication avec QGIS
    - Utiliser un shapefile 2D déjà importé dans QGIS et afficher la région concernée
    - Afficher le Z du centre de l'image
    - Afficher les coordonnées XYZ lors d'un clic 
    - Permettre le choix des écrans
    - Utiliser un shapefile 3D

Le main permet tout simplement de lancer l'application

Plusieurs autres outils seront intégrés à cette application dans le futur :
    - Fonctionnalité de trace supplémentaire
    - Amélioration des fonctions de photogrammétrie 
    - Menu de choix de paramètres (curseur, keybinding, couleur des traces)
    - Affichage des zones supersposées seulement
    - Gestion de projet
    
    et bien d'autre

'''

from qgis.gui import *
from qgis.core import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *

#from PyQt5.QtWidgets import *
#from PyQt5.QtCore import *
#from PyQt5.QtGui import *

from PIL import Image, ImageDraw
import numpy as np
from . import resources

from .ui_optWindowCleaner import optionWindow
from .ui_graphicsWindow import graphicsWindow 
from .ui_getVectorLayer import getVectorLayer
from .worldManager import pictureManager, dualManager
from .enhanceManager import enhanceManager, threadShow, imageEnhancing, pictureLayout
from .drawFunction import *
from .folderManager import getParDict, findPossiblePair, findNeighbour
import sys, os, time, math, qimage2ndarray, win32api

#Permet l'ouverture avec PIL de fichier énorme!
Image.MAX_IMAGE_PIXELS = 1000000000 

class stereoPhoto(object):

    #Fonction d'initilisation 
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

    #Place le bouton de l'application dans QGIS
    def initGui(self):
        urlPicture = ":/Anaglyph/Icons/icon.png"
        self.action = QAction(QIcon(urlPicture), "StereoPhoto", self.iface.mainWindow())
        
        self.action.triggered.connect(self.run)
         
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&StereoPhoto", self.action)

    #Retire le bouton de l'application dans QGIS
    def unload(self):
        self.iface.removePluginMenu("&StereoPhoto", self.action)
        self.iface.removeToolBarIcon(self.action)
        
    #Initialisation de l'application et des variables
    #Connection entre les boutons du menu d'options (mOpt) et leurs fonctions attitrées
    #Ouverture du menu d'options
    def run(self):

        self.leftName = False 
        self.rightName = False 

        self.showThreadLeftInProcess = False
        self.newLeftRequest = False
        self.showThreadRightInProcess = False
        self.newRightRequest = False
        self.enableDraw = False
        self.enableShow = False

        self.isEstPicture = False

        self.polygonOnLeftScreen = []
        self.polygonOnRightScreen = []

        self.listParam = [0, 0, 0, 0, 0, 0, 0, False, False, []]

        self.optWindow = optionWindow()
        

        self.optWindow.ui.importLineProject.textChanged.connect(self.newPictureFile)
        self.optWindow.ui.importLineVectorLayer.textChanged.connect(self.mNewVectorLayer)
        self.optWindow.ui.pushButtonShowPicture.clicked.connect(self.startViewing)
        self.optWindow.ui.pushButtonShowIDList.clicked.connect(self.showIDList)
        self.optWindow.ui.enhanceButton.clicked.connect(self.enhanceClick)

        self.optWindow.ui.toolButtonNord.clicked.connect(lambda :self.toolButtonPressEvent('N'))
        self.optWindow.ui.toolButtonSud.clicked.connect(lambda : self.toolButtonPressEvent('S'))
        self.optWindow.ui.toolButtonEst.clicked.connect(lambda : self.toolButtonPressEvent('E'))
        self.optWindow.ui.toolButtonOuest.clicked.connect(lambda : self.toolButtonPressEvent('O'))
        
        self.optWindow.ui.pushButtonRemoveShape.clicked.connect(self.removePolygonOnScreen)
        self.optWindow.keyDrawEvent.connect(self.keyboardHandler)

        self.optWindow.closeWindow.connect(self.optWindowClose)

        nbScreen = QApplication.desktop().screenCount()-1
        self.optWindow.ui.spinBoxLeftScreen.setMaximum(nbScreen)
        self.optWindow.ui.spinBoxRightScreen.setMaximum(nbScreen)

        self.optWindow.show()
        

    #Fonction appelée lors de la fermeture du mOpt
    #Si l'on ferme le mOpt toutes les autres fenêtres Qt se ferment
    def closeAllSideWindows(self) :
        scene = QGraphicsScene()
        if hasattr(self, "graphWindowLeft"):
            self.graphWindowLeft.ui.graphicsView.setScene(scene)
            self.graphWindowLeft.close()
            del self.graphWindowLeft
        if hasattr(self, "graphWindowRight"):
            self.graphWindowRight.ui.graphicsView.setScene(scene)
            self.graphWindowRight.close()
            del self.graphWindowRight
        if hasattr(self, "enhanceManager"):
            self.enhanceManager.colorWindow.ui.graphicsView.setScene(scene)
            self.enhanceManager.colorWindow.close()
            del self.enhanceManager 
    
    def optWindowClose(self):
        self.closeAllSideWindows()
        self.optWindow.close()
    
    def newPictureFile(self):
        self.currentMainPath = self.optWindow.ui.importLineProject.text()
        self.currentParDict = getParDict(self.currentMainPath)
        for key in self.currentParDict :
            if self.setPairID(key) : break
        else : return 


        self.optWindow.ui.pushButtonShowIDList.setEnabled(True)
        self.optWindow.ui.enhanceButton.setEnabled(True)
        self.optWindow.ui.pushButtonShowPicture.setEnabled(True)

        self.closeAllSideWindows()
        self.addNewPair()

    def showIDList(self) : 
        self.pictureSelectWindow = getVectorLayer(sorted(self.currentParDict))
        self.pictureSelectWindow.setWindowTitle("Choix de l'image")
        self.pictureSelectWindow.ui.label.setText("Image disponible dans le dossier")
        self.pictureSelectWindow.ui.label.setGeometry(QtCore.QRect(50, 10, 260, 21))
        self.pictureSelectWindow.ui.buttonBox.accepted.connect(self.pictureSelectionAccept)
        self.pictureSelectWindow.ui.buttonBox.rejected.connect(self.pictureSelectionCancel)
        self.pictureSelectWindow.show()
    
    def pictureSelectionAccept(self):
        pictureID = self.pictureSelectWindow.ui.listWidget.selectedItems()[0].text()
        if self.setPairID(pictureID) :  self.addNewPair()
        self.pictureSelectWindow.close()

    def pictureSelectionCancel(self): self.pictureSelectWindow.close()

    def setPairID(self, pictureID) :
        pair = findPossiblePair(pictureID, self.currentParDict)
        if pair != ('', '') :
            if pair[1] :
                self.leftParID = pictureID
                self.rightParID = pair[1]
                self.isEstPicture = True if findPossiblePair(pair[1], self.currentParDict)[1] else False
                        
            else : 
                self.leftParID = pair[0] 
                self.rightParID = pictureID
                self.isEstPicture = False
            return True
        else : return False

    def addNewPair(self) :

        self.optWindow.ui.labelLeftName.setText(self.leftParID)
        self.optWindow.ui.labelRightName.setText(self.rightParID)
        
        self.currentLeftTIF = self.currentMainPath + '/' + self.leftParID + '.tif'
        self.currentLeftPAR = self.currentMainPath  + '/' + self.leftParID + '.par'
        self.currentRightTIF = self.currentMainPath  + '/' + self.rightParID + '.tif'
        self.currentRightPAR = self.currentMainPath  + '/' + self.rightParID + '.par'

        neighbour = findNeighbour(self.leftParID, self.currentParDict)

        if neighbour[0] : 
            self.optWindow.ui.toolButtonNord.setEnabled(True)
            self.currentNordID = neighbour[0]

        else : 
            self.optWindow.ui.toolButtonNord.setEnabled(False)
            self.currentNordID = ''

        if neighbour[1] :
            self.optWindow.ui.toolButtonSud.setEnabled(True)
            self.currentSudID = neighbour[1]

        else : 
            self.optWindow.ui.toolButtonSud.setEnabled(False)
            self.currentSudID = ''
  
        if neighbour[2] :
            self.optWindow.ui.toolButtonOuest.setEnabled(True)
            self.currentOuestID = neighbour[2]

        else : 
            self.optWindow.ui.toolButtonOuest.setEnabled(False)
            self.currentOuestID = ''

        if neighbour[3] and self.isEstPicture :
            self.optWindow.ui.toolButtonEst.setEnabled(True)
            self.currentEstID = neighbour[3]

        else : 
            self.optWindow.ui.toolButtonEst.setEnabled(False)
            self.currentEstID = ''
        

        self.demoLeftPic = Image.open(self.currentLeftTIF)
        self.demoRightPic = Image.open(self.currentRightTIF)

        if hasattr(self.demoLeftPic, "n_frames"): 
            for i in range(self.demoLeftPic.n_frames):
                self.demoLeftPic.seek(i)
                if self.demoLeftPic.size < (200,200) :
                    self.demoLeftPic.seek(i-1)
                    leftPic = pictureLayout(self.demoLeftPic, 0, 0, True)
                    sceneLeft = QGraphicsScene()
                    sceneLeft.addPixmap(QPixmap.fromImage(leftPic))
                    
                    self.optWindow.ui.graphicsViewLeft.setScene(sceneLeft)
                    self.optWindow.ui.graphicsViewLeft.show()
                    self.optWindow.ui.graphicsViewLeft.fitInView(self.optWindow.ui.graphicsViewLeft.sceneRect(), Qt.KeepAspectRatio)
                    break
        
        if hasattr(self.demoRightPic, "n_frames"): 
            for i in range(self.demoRightPic.n_frames):
                self.demoRightPic.seek(i)
                if self.demoRightPic.size < (200,200) :
                    self.demoRightPic.seek(i-1)
                    rightPic = pictureLayout(self.demoRightPic, 0, 0, True)
                    sceneRight = QGraphicsScene()
                    sceneRight.addPixmap(QPixmap.fromImage(rightPic))
                    
                    self.optWindow.ui.graphicsViewRight.setScene(sceneRight)
                    self.optWindow.ui.graphicsViewRight.show()
                    self.optWindow.ui.graphicsViewRight.fitInView(self.optWindow.ui.graphicsViewRight.sceneRect(), Qt.KeepAspectRatio)
                    break
 
        self.demoLeftPic.close()
        self.demoRightPic.close()
    
    def toolButtonPressEvent(self, ori):

        if ori == 'N': newID = self.currentNordID
        elif ori == 'O': newID = self.currentOuestID
        elif ori == 'S': newID = self.currentSudID
        elif ori == 'E':  newID = self.currentEstID
        else : return

        if self.setPairID(newID) :  self.addNewPair()

        if self.optWindow.ui.pushButtonShowPicture.isEnabled():
            pass 
            #self.closeAllSideWindows() ??
            #self.startViewing() ?? on doit concidérer des appels similaire, mais les fenêtres existent déjà 

        #Sera disponible avec WASD donc regarder pushbuttonShowPicture.isEnabled() -> plus tard
        #Toujours en fonction de l'image de gauche
        #selon l'orientation donnée, détermine la prochaine paire


    def startViewing(self):
        pass
        #Ouvre les 2 graphicsViews -> remplace loads windows
        #ajoute les fonctionnalités du bouton naviguer  
        #escape doit fermé les deux graphicsViews
        #rajouter wasd pour le déplacement de paire  
    

    
        
    #Fonction réaliser lorsqu'une photo est importée 
    #Elle permet de rendre le panneau de fonctionnalité accessible à l'utilisateur 
    #pour le traitement d'image ainsi que le bouton d'importation
    #L'image est affiché en petit format pour permettre une visualisation du 
    #résultat qui sera produit suite à l'importation  
    #Si une nouvelle photo est importée, l'ancienne est fermée 
    #Création d'un pictureManager pour associer le fichier .par à la photo
    #Récupération du choix de l'écran pour l'affichage
    def mNewLeftPic(self) : 

        self.intLeftScreen = self.optWindow.ui.spinBoxLeftScreen.value()
        self.screenLeft = QApplication.desktop().screenGeometry(self.intLeftScreen)
        self.panCenterLeft = (int(self.screenLeft.width()/2), int(self.screenLeft.height()/2))
        self.leftScreenCenter = ( self.screenLeft.x() + int(self.screenLeft.width()/2), self.screenLeft.y() + int(self.screenLeft.height()/2))
          

        self.leftName = False

        self.leftPic = Image.open(self.optWindow.ui.importLineLeft.text())

        self.graphWindowLeft = graphicsWindow("Image Gauche")
        self.graphWindowLeft.setWindowState(Qt.WindowMaximized)
        rect = QRect(0,0,self.screenLeft.width(),self.screenLeft.height())
        self.graphWindowLeft.ui.graphicsView.setGeometry(rect)
        self.graphWindowLeft.ui.widget.setGeometry(rect)
        self.graphWindowLeft.move(QPoint(self.screenLeft.x(), self.screenLeft.y()))
        self.graphWindowLeft.keyDrawEvent.connect(self.keyboardHandler)

        pathPAR = self.optWindow.ui.importLineLeft.text().split(".")[0] + ".par"
        self.leftPictureManager = pictureManager(self.leftPic.size, pathPAR, "aa")
        self.leftPicSize = self.leftPic.size

    #Idem à mNewLeftPic
    #L'image a un effet miroir horizontal dès son ouverture
    def mNewRightPic(self):
        

        self.intRightScreen = self.optWindow.ui.spinBoxRightScreen.value()
        self.screenRight = QApplication.desktop().screenGeometry(self.intRightScreen)
        self.panCenterRight = (int(self.screenRight.width()/2), int(self.screenRight.height()/2))

        self.rightName = False
        
        self.graphWindowRight = graphicsWindow("Image Droite")
        self.graphWindowRight.setWindowState(Qt.WindowMaximized)
        rect = QRect(0,0,self.screenRight.width(),self.screenRight.height())
        self.graphWindowRight.ui.graphicsView.setGeometry(rect)
        self.graphWindowRight.ui.widget.setGeometry(rect)
        self.graphWindowRight.move(QPoint(self.screenRight.x(), self.screenRight.y()))

        pathPAR = self.optWindow.ui.importLineRight.text().split(".")[0] + ".par"
        self.rightPictureManager = pictureManager(self.rightPic.size, pathPAR, "aa")
        self.rightPicSize = self.rightPic.size

    #Fonction qui récupère la couche vectorielle et change le SIG de QGIS 
    #Si possible appel la fonction pour afficher la couche vectorielle sur les images
    def mNewVectorLayer(self):

        self.enableDraw = True
        self.vectorLayer = self.optWindow.vLayer
        QgsProject.instance().setCrs(self.vectorLayer.crs())

        if self.enableShow :
            self.optWindow.ui.pushButtonRemoveShape.setEnabled(True)
            self.addPolygonOnScreen()

    
    #Fonction qui détermine la région approximative des photos
    #Retourne le rectangle de coordonnée
    def getShowRect(self) :
        
        if hasattr(self, "leftRect"): 
            endLeft = [self.leftRect.x() + self.leftRect.width(), self.leftRect.y() + self.leftRect.height()]
            
            #topXL, topYL = self.leftPictureManager.pixelToCoord([self.leftRect.x(),self.leftRect.y()],self.initAltitude)
            #botXL, botYL = self.leftPictureManager.pixelToCoord(endLeft,self.initAltitude)

            topXL, topYL = self.leftPictureManager.pixelToCoord([0,0],self.initAltitude)
            botXL, botYL = self.leftPictureManager.pixelToCoord([self.leftRect.width(), self.leftRect.height()],self.initAltitude)
            
            rectL = QgsRectangle(QgsPointXY(topXL, topYL), QgsPointXY(botXL, botYL))
            return rectL
        
        else :
            return QgsRectangle(QgsPointXY(0, 0), QgsPointXY(0, 0))
        
    #Fonction qui reçoit un pixel de chaque image
    #Utilise les deux pixels pour faire le calcul du Z et des coordonnées
    #Retourne la valeur des coordonnées moyennées
    def dualPixelToCoord(self, QPointLeft, QPointRight):
        
        if self.leftMiroir == 1 :
            mirrorX = self.leftPicSize[0] - QPointLeft.x()
            pixL = (mirrorX, QPointLeft.y())
    
        elif self.leftMiroir == 2 :
            mirrorY = self.leftPicSize[1] - QPointLeft.y()
            pixL = (QPointLeft.x(), mirrorY)
    
        else :
            pixL = (QPointLeft.x(), QPointLeft.y())            

        if self.rightMiroir == 1 :
            mirrorX = self.rightPicSize[0] - QPointRight.x()
            pixR = (mirrorX, QPointRight.y())

        elif self.rightMiroir == 2 :
            mirrorY = self.rightPicSize[1] - QPointRight.y()
            pixR = (QPointRight.x(), mirrorY)

        else : 
            pixR = (QPointRight.x(), QPointRight.y())
        
        Z = self.dualManager.calculateZ(pixL, pixR)
        XL, YL = self.leftPictureManager.pixelToCoord(pixL, Z)
        XR, YR = self.rightPictureManager.pixelToCoord(pixR, Z)

        X = (XL + XR) / 2
        Y = (YL + YR) / 2
        
        return X, Y


    #Fonction qui ouvre les deux fenêtres sur les écrans choisis
    #Récupère les valeurs en pixels du centre de l'image
    #Création du dualManager qui permet de calculer l'altitude
    #Premier calcul de l'altitude du centre des images 
    #Utilise le pourcentage de recouvrement pour placer les images
    #Affichage de l'image complète
    #Affichage d'un curseur au centre des fenêtres
    #Si possible appel la fonction pour afficher la couche vectorielle sur les images   
    def loadWindows(self, value):

        self.intLeftScreen = self.optWindow.ui.spinBoxLeftScreen.value()
        self.screenLeft = QApplication.desktop().screenGeometry(self.intLeftScreen)
        self.panCenterLeft = (int(self.screenLeft.width()/2), int(self.screenLeft.height()/2))
        self.leftScreenCenter = ( self.screenLeft.x() + int(self.screenLeft.width()/2), self.screenLeft.y() + int(self.screenLeft.height()/2))

        rect = QRect(0,0,self.screenLeft.width(),self.screenLeft.height())
        self.graphWindowLeft.ui.graphicsView.setGeometry(rect)
        self.graphWindowLeft.ui.widget.setGeometry(rect)
        self.graphWindowLeft.move(QPoint(self.screenLeft.x(), self.screenLeft.y()))

        self.intRightScreen = self.optWindow.ui.spinBoxRightScreen.value()
        self.screenRight = QApplication.desktop().screenGeometry(self.intRightScreen)
        self.panCenterRight = (int(self.screenRight.width()/2), int(self.screenRight.height()/2))

        rect = QRect(0,0,self.screenRight.width(),self.screenRight.height())
        self.graphWindowRight.ui.graphicsView.setGeometry(rect)
        self.graphWindowRight.ui.widget.setGeometry(rect)
        self.graphWindowRight.move(QPoint(self.screenRight.x(), self.screenRight.y()))


        self.dualManager = dualManager(self.leftPictureManager, self.rightPictureManager)
        xLeft = (self.leftPicSize[0]/2)*((100-self.optWindow.ui.spinBoxRecouvrementH.value())/100)
        xRight = (self.rightPicSize[0]/2)*((100-self.optWindow.ui.spinBoxRecouvrementH.value())/100)
        yLeft = (self.leftPicSize[1]/2)*((100-self.optWindow.ui.spinBoxRecouvrementV.value())/100)
        yRight = (self.rightPicSize[1]/2)*((100-self.optWindow.ui.spinBoxRecouvrementV.value())/100)
        self.leftRect = QRectF(xLeft, yLeft, self.leftPicSize[0], self.leftPicSize[1])
        self.rightRect = QRectF(xRight, yRight, self.rightPicSize[0], self.rightPicSize[1]) 
        
        self.graphWindowLeft.close()
        self.graphWindowRight.close()
        
        self.graphWindowLeft.cursorRectInit(self.screenLeft.width(), self.screenLeft.height())
        self.graphWindowRight.cursorRectInit(self.screenRight.width(), self.screenRight.height())

        self.graphWindowLeft.show()
        self.graphWindowRight.show()
        self.graphWindowLeft.ui.graphicsView.fitInView(self.leftRect, Qt.KeepAspectRatio)
        self.graphWindowRight.ui.graphicsView.fitInView(self.rightRect, Qt.KeepAspectRatio)
        self.graphWindowLeft.ui.graphicsView.update()
        self.graphWindowRight.ui.graphicsView.update()
        self.optWindow.activateWindow()
        self.optWindow.ui.panButton.setEnabled(True)
        self.enableShow = True
        
        centerPointLeft = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(self.panCenterLeft[0], self.panCenterLeft[1]))
        centerPointRight = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(self.panCenterRight[0], self.panCenterRight[1]))

        if self.leftMiroir == 1 :
            mirrorX = self.leftPicSize[0] - centerPointLeft.x()
            self.centerPixelLeft = (mirrorX, centerPointLeft.y())
        
        elif self.leftMiroir == 2 :
            mirrorY = self.leftPicSize[1] - centerPointLeft.y()
            self.centerPixelLeft = (centerPointLeft.x(), mirrorY)
       
        else :
            self.centerPixelLeft = (centerPointLeft.x(), centerPointLeft.y())            

        if self.rightMiroir == 1 :
            mirrorX = self.rightPicSize[0] - centerPointRight.x()
            self.centerPixelRight = (mirrorX, centerPointRight.y())

        elif self.rightMiroir == 2 :
            mirrorY = self.rightPicSize[1] - centerPointRight.y()
            self.centerPixelRight = (centerPointRight.x(), mirrorY)

        else : 
            self.centerPixelRight = (centerPointRight.x(), centerPointRight.y())


        Z = self.dualManager.calculateZ(self.centerPixelLeft, self.centerPixelRight)
        self.optWindow.ui.lineEditCurrentZ.setText(str(round(Z,2)))

        self.initAltitude = Z
        
        #Call set Extend QGIS here 
        extentRect = self.getShowRect()
        self.canvas.setExtent(extentRect)

        if self.enableDraw :
            self.optWindow.ui.pushButtonRemoveShape.setEnabled(True)
            self.addPolygonOnScreen()


    def removePolygonOnScreen(self) :
        if self.polygonOnLeftScreen :
            for item in self.polygonOnLeftScreen :
                self.graphWindowLeft.ui.graphicsView.scene().removeItem(item)
        self.polygonOnLeftScreen = []

        if self.polygonOnRightScreen :
            for item in self.polygonOnRightScreen :
                self.graphWindowRight.ui.graphicsView.scene().removeItem(item)
        self.polygonOnRightScreen = []

        self.vectorLayer = None 
        self.enableDraw = False

        self.optWindow.ui.importLineVectorLayer.textChanged.disconnect(self.mNewVectorLayer)
        self.optWindow.ui.importLineVectorLayer.setText("")
        self.optWindow.ui.importLineVectorLayer.textChanged.connect(self.mNewVectorLayer)

        self.optWindow.ui.pushButtonRemoveShape.setEnabled(False)

    #Fonction qui ajoute les polygones sur chaque image
    #Elle concidère les coordonnées approximatives pour récupérer
    #les polygones de la région sur la couche vectorielle
    def addPolygonOnScreen(self) :
        rectCoord = self.getShowRect()

        listGeo = list(self.vectorLayer.getFeatures(rectCoord))

        if self.polygonOnLeftScreen :
            for item in self.polygonOnLeftScreen :
                self.graphWindowLeft.ui.graphicsView.scene().removeItem(item)
        self.polygonOnLeftScreen = []

        if self.polygonOnRightScreen :
            for item in self.polygonOnRightScreen :
                self.graphWindowRight.ui.graphicsView.scene().removeItem(item)
        self.polygonOnRightScreen = []
            
        for item in listGeo : 
            featureGeo = item.geometry() #-Fonctionnement différent pour Polygone Z et ZM? as MultiPolygon
            
            if featureGeo.isNull() == False :

                #listQgsPoint = featureGeo.asMultiPolygon()[0][0]
                lenGeo =  len(featureGeo.asPolygon()[0])
                #listQgsPoint = featureGeo.vertexAt(int)
                #len(featureGeo.asPolygon()[0])
                polygonL = QPolygonF()
                polygonR = QPolygonF()
                for nb in range(lenGeo) :
                    data = featureGeo.vertexAt(nb)
                    xPixel, yPixel = self.leftPictureManager.coordToPixel((data.x() , data.y()), data.z())

                    if self.leftMiroir == 1 :
                        mirrorX = -xPixel + self.leftPicSize[0]
                        pixL = (mirrorX, yPixel)
                
                    elif self.leftMiroir == 2 :
                        mirrorY = -yPixel + self.leftPicSize[1] 
                        pixL = (xPixel, mirrorY)
                
                    else :
                        pixL = (xPixel, yPixel)            

                    xPixel, yPixel = self.rightPictureManager.coordToPixel((data.x() , data.y()), data.z())
                    
                    if self.rightMiroir == 1 :
                        mirrorX = -xPixel + self.rightPicSize[0]
                        pixR = (mirrorX, yPixel)

                    elif self.rightMiroir == 2 :
                        mirrorY = -yPixel + self.rightPicSize[1]
                        pixR = (xPixel, mirrorY)

                    else : 
                        pixR = (xPixel, yPixel)

                    polygonL.append(QPointF(pixL[0], pixL[1]))
                    polygonR.append(QPointF(pixR[0], pixR[1]))

                m_pen = QPen(QColor(0, 255, 255),10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                leftObj = self.graphWindowLeft.ui.graphicsView.scene().addPolygon(polygonL, m_pen)
                rightObj = self.graphWindowRight.ui.graphicsView.scene().addPolygon(polygonR, m_pen)
                self.polygonOnLeftScreen.append(leftObj)
                self.polygonOnRightScreen.append(rightObj)

    #Fonction pour permettre l'imporation de l'image sur le graphicsView
    #Similaire au fichier enhanceManager, une version de basse résolution de l'image est affichée immédiatement
    #Par la suite, un thread est lancé pour venir afficher les plus hautes résolutions
    #Le rehaussement, la rotation et l'effet miroir sont considérés
    #Les connections pour les fonctiones de navigations sont établies
    def mImportLeft(self):

        if hasattr(self, "tSeekLeft"): 
            try :
                self.tSeekLeft.newImage.disconnect(self.addLeftPixmap)
            except: 
                pass
            self.tSeekLeft.keepRunning = False

 
        self.leftPic.seek(3)

        t = imageEnhancing(self.leftPic, self.listParam)
        t.start()
        r = t.join()
        enhancePic = Image.merge("RGB", (r[0],r[1],r[2]))
        #enhancePic = enhancePic.rotate(0.8634, expand=1)
        
        QtImg = pictureLayout(enhancePic, self.leftOrientation, self.leftMiroir, True)   
        
        scene = QGraphicsScene()
        scene.setSceneRect(-100000,-100000,200000,200000)
        
        objPixmap = scene.addPixmap(QPixmap.fromImage(QtImg))      
        objPixmap.setScale(8)
        self.graphWindowLeft.ui.graphicsView.setScene(scene)
        
        pointZero = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(0,0))
        GV = self.graphWindowLeft.ui.graphicsView
        pointMax = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))

        if self.showThreadLeftInProcess == False :
            self.threadSeekLeft(pointZero, pointMax, 0.5, 1, 2)
            self.showThreadLeftInProcess = True
        else :
            self.newLeftRequest = True

        self.graphWindowLeft.ui.widget.mouseMoveEvent = self.mMoveEvent
        self.graphWindowLeft.ui.widget.mousePressEvent = self.mPressEvent
        self.graphWindowLeft.ui.widget.wheelEvent = self.wheelEvent
        self.graphWindowLeft.ui.graphicsView.show()
        self.leftName = True 
        if self.rightName :
            self.optWindow.ui.affichageButton.setEnabled(True)
            self.optWindow.ui.enhanceButton.setEnabled(True)

    #IDEM à mImportLeft
    def mImportRight(self):

        if hasattr(self, "tSeekRight"): 
            try :
                self.tSeekRight.newImage.disconnect(self.addRightPixmap)
            except: 
                pass
            self.tSeekRight.keepRunning = False

        self.optWindow.ui.importDoneRight.setStyleSheet("image: url(:/Anaglyph/Icons/loading.png);")
        self.optWindow.ui.importButtonRight.setEnabled(False)
      
        self.rightPic.seek(3)

        t = imageEnhancing(self.rightPic, self.listParam)
        t.start()
        r = t.join()      
        enhancePic = Image.merge("RGB", (r[0],r[1],r[2]))
        #enhancePic = enhancePic.rotate(0.8634, expand=1)
        
        QtImg = pictureLayout(enhancePic, self.rightOrientation, self.rightMiroir, True)   
        
        scene = QGraphicsScene()
        scene.setSceneRect(-100000,-100000,200000,200000)
        
        objPixmap = scene.addPixmap(QPixmap.fromImage(QtImg))
        objPixmap.setScale(8)
        self.graphWindowRight.ui.graphicsView.setScene(scene)
        
        pointZero = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(0,0))
        GV = self.graphWindowRight.ui.graphicsView
        pointMax = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))

        if self.showThreadRightInProcess == False :
            self.threadSeekRight(pointZero, pointMax, 0.5, 1, 2)
            self.showThreadRightInProcess = True
        else :
            self.newRightRequest = True

        self.graphWindowRight.ui.graphicsView.show()
        self.optWindow.ui.importDoneRight.setStyleSheet("image: url(:/Anaglyph/Icons/greenCheck.png);")
        self.optWindow.ui.importButtonRight.setEnabled(True)
        self.rightName = True 
        if self.leftName :
            self.optWindow.ui.affichageButton.setEnabled(True)
            self.optWindow.ui.enhanceButton.setEnabled(True)


    #Utiliser par threadShow pour afficher une portion de l'image à une certaine position
    def addLeftPixmap(self, pixmap, scaleFactor, topX, topY) :
        d = self.graphWindowLeft.ui.graphicsView.scene().addPixmap(pixmap)
        d.setScale(scaleFactor)
        d.setOffset(topX, topY)

    #IDEM à addLeftPixmap
    def addRightPixmap(self, pixmap, scaleFactor, topX, topY) :
        d = self.graphWindowRight.ui.graphicsView.scene().addPixmap(pixmap)
        d.setScale(scaleFactor)
        d.setOffset(topX, topY)

    #Fonction qui permet de lancer le thread d'affichage des images de plus grande qualité
    def threadSeekLeft(self, pointZero, pointMax, multiFactor, seekFactor, scaleFactor):
        self.tSeekLeft = threadShow(self.optWindow.ui.importLineLeft.text(), pointZero, pointMax, multiFactor, seekFactor, scaleFactor, self.listParam, self.leftOrientation, self.leftMiroir)
        self.tSeekLeft.newImage.connect(self.addLeftPixmap)
        self.tSeekLeft.finished.connect(self.seekLeftDone)
        self.showThreadLeftInProcess = True
        self.newLeftRequest = False
        self.tSeekLeft.start(QThread.IdlePriority)

    #IDEM à threadSeekLeft
    def threadSeekRight(self, pointZero, pointMax, multiFactor, seekFactor, scaleFactor):
        self.tSeekRight = threadShow(self.optWindow.ui.importLineRight.text(), pointZero, pointMax, multiFactor, seekFactor, scaleFactor, self.listParam, self.rightOrientation, self.rightMiroir)
        self.tSeekRight.newImage.connect(self.addRightPixmap)
        self.tSeekRight.finished.connect(self.seekRightDone)
        self.showThreadRightInProcess = True
        self.newRightRequest = False
        self.tSeekRight.start(QThread.IdlePriority)

    #Fonction exécutée lorsque le thread d'affichage se termine
    #Elle redessine les polygones sur les images
    #Elle relance le thread avec la même résolution si une requête a été faite sinon
    #elle relance le thread avec une plus grande résolution d'image 
    def seekLeftDone(self):

        if self.enableDraw and hasattr(self, "initAltitude"):
            self.addPolygonOnScreen()

        if self.newLeftRequest : 
            pointZero = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(0,0))
            GV = self.graphWindowLeft.ui.graphicsView
            pointMax = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))
            self.threadSeekLeft(pointZero, pointMax, 0.5, 1, 2)

        elif self.tSeekLeft.seekFactor == 1 :
            pointZero = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(0,0))
            GV = self.graphWindowLeft.ui.graphicsView
            pointMax = self.graphWindowLeft.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))
            self.threadSeekLeft(pointZero, pointMax, 1, 0, 1)

        else :
            self.showThreadLeftInProcess = False

    #IDEM à seekLeftDone
    def seekRightDone(self):

        if self.enableDraw and hasattr(self, "initAltitude") :
            self.addPolygonOnScreen()

        if self.newRightRequest : 
            pointZero = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(0,0))
            GV = self.graphWindowRight.ui.graphicsView
            pointMax = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))
            self.threadSeekRight(pointZero, pointMax, 0.5, 1, 2)

        elif self.tSeekRight.seekFactor == 1 :
            pointZero = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(0,0))
            GV = self.graphWindowRight.ui.graphicsView
            pointMax = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(GV.width(),GV.height()))
            self.threadSeekRight(pointZero, pointMax, 1, 0, 1)

        else :
            self.showThreadRightInProcess = False
       
    
    #Place la souris en mode pan, active/désactive les boutons de dessin   
    def panClick(self):

        if self.optWindow.ui.panButton.isChecked():
            
            #22 est la taille en pixel de la barre du haute de la fenetre
            #Il y a toujours un petit pan lorsqu'on active le Pan sinon 
            self.lastX = self.panCenterLeft[0]
            self.lastY = self.panCenterLeft[1] - 22
            win32api.SetCursorPos(self.leftScreenCenter)
            self.graphWindowLeft.ui.widget.setMouseTracking(True)
            self.graphWindowLeft.setCursor(self.graphWindowLeft.invisibleCursor)
        
        else : 
            self.graphWindowLeft.ui.widget.setMouseTracking(False)
            win32api.SetCursorPos((self.optWindow.pos().x(), self.optWindow.pos().y()))
            self.graphWindowLeft.setCursor(self.graphWindowLeft.normalCursor)
    
    #Ouverture de la fenêtre de rehaussement
    def enhanceClick(self):
        self.enhanceManager = enhanceManager(self.currentLeftTIF, self.currentRightTIF, self.listParam)
        self.enhanceManager.listParamSignal.connect(self.applyEnhance)

    #Permet le lancement du traitement de modification des images
    def applyEnhance(self, listParam):
        self.enhanceManager.listParamSignal.disconnect(self.applyEnhance)
        self.listParam = listParam
        #self.mImportLeft()
        #self.mImportRight()

    #Fonction appelée lorsque les touches respectives du clavier sont appuyées
    #Les touches sont utiles lorsque le mode pan est en cours d'utilisation
    #Possibilité d'ajouter d'autres fonctions plus tard
    def keyboardHandler(self, number):
        
        if number == "1" :
            pass
        
        elif number == "2" :
            pass
        
        elif number == "3" :

            pass

        elif number == "ESC":
            self.optWindow.ui.panButton.setChecked(False)
            self.panClick()
            

    #Fonction qui réalise le pan 
    #Lors du pan la souris est présente sur l'écran qui contient l'image de gauche
    #Cette fonction s'assure que la souris reste sur l'écran conserné pendant le Pan afin de garder le curseur invisible  
    def mMoveEvent(self, ev):

        if self.optWindow.ui.panButton.isChecked() :
            self.deltaX = int((ev.x()-self.lastX) / 2)
            self.lastX = ev.x()
            self.deltaY = int((ev.y()-self.lastY) / 2)
            self.lastY = ev.y()
            leftView = self.graphWindowLeft.ui.graphicsView
            rightView = self.graphWindowRight.ui.graphicsView
            pixRange = 400
            if ev.x() > (self.screenLeft.width() - pixRange) or ev.x() < pixRange or ev.y() < pixRange or ev.y() > (self.screenLeft.height() - pixRange) :
                self.graphWindowLeft.ui.widget.setMouseTracking(False)
                win32api.SetCursorPos(self.leftScreenCenter)
                self.lastX = self.panCenterLeft[0]
                self.lastY = self.panCenterLeft[1]
                self.graphWindowLeft.ui.widget.setMouseTracking(True)
                
            leftView.horizontalScrollBar().setValue(leftView.horizontalScrollBar().value() - self.deltaX)
            leftView.verticalScrollBar().setValue(leftView.verticalScrollBar().value() + self.deltaY)
            rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() + self.deltaX)
            rightView.verticalScrollBar().setValue(rightView.verticalScrollBar().value() + self.deltaY)
        
            
    

    #Fonction activer par la roulette de la souris
    #Avec la touche CTRL, il est possible de zoom In/Out sur les photos 
    #Sinon il est possible de déplacer l'image de droite et d'actualiser la valeur Z du centre 
    def wheelEvent(self, event):
        factor = 1.41 ** (event.angleDelta().y() / 240.0)
        leftView = self.graphWindowLeft.ui.graphicsView
        rightView = self.graphWindowRight.ui.graphicsView
        
        if self.optWindow.ctrlClick or self.graphWindowLeft.ctrlClick or self.graphWindowRight.ctrlClick :    
            if factor > 1 : 
                leftView.scale(1.25, 1.25)
                rightView.scale(1.25, 1.25)
            else :
                leftView.scale(0.8, 0.8)
                rightView.scale(0.8, 0.8)

        elif self.optWindow.shiftClick or self.graphWindowLeft.shiftClick or self.graphWindowRight.shiftClick :
            bPoint = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(self.panCenterRight[0], self.panCenterRight[1]))
            if factor > 1 : 
                #leftView.verticalScrollBar().setValue(leftView.verticalScrollBar().value() - 1)
                rightView.verticalScrollBar().setValue(rightView.verticalScrollBar().value() - 1)
            else :
                #leftView.verticalScrollBar().setValue(leftView.verticalScrollBar().value() + 1)
                rightView.verticalScrollBar().setValue(rightView.verticalScrollBar().value() + 1)

            aPoint = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(self.panCenterRight[0], self.panCenterRight[1]))
            diffY = aPoint.y() - bPoint.y()

            self.centerPixelRight = (self.centerPixelRight[0], self.centerPixelRight[1]-diffY) 
            Z = self.dualManager.calculateZ(self.centerPixelLeft, self.centerPixelRight)
            self.optWindow.ui.lineEditCurrentZ.setText(str(round(Z,2)))

        elif self.optWindow.altClick or self.graphWindowLeft.altClick or self.graphWindowRight.altClick : 
            valX = self.optWindow.ui.spinBoxMoveInX.value()
            valY = self.optWindow.ui.spinBoxMoveInY.value()
            if self.optWindow.ui.checkBoxMoveLeft.isChecked() :
                for item in self.polygonOnLeftScreen:
                    newPoly = QPolygonF()
                    poly = item.polygon()
                    for point in poly :
                        
                        if factor > 1 : newPoly << QPointF(point.x() - valX, point.y() - valY)
                        else : newPoly << QPointF(point.x() + valX, point.y() + valY)

                    item.setPolygon(newPoly)

            if self.optWindow.ui.checkBoxMoveRight.isChecked()  :
                for item in self.polygonOnRightScreen:
                    newPoly = QPolygonF()
                    poly = item.polygon()
                    for point in poly :
                        if factor > 1 : newPoly << QPointF(point.x() - valX, point.y() - valY)
                        else : newPoly << QPointF(point.x() + valX, point.y() + valY)

                    item.setPolygon(newPoly)

        else : 

            bPoint = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(self.panCenterRight[0], self.panCenterRight[1]))
            if factor > 1 : 
                #leftView.horizontalScrollBar().setValue(leftView.horizontalScrollBar().value() - 1)
                rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() - 1)
            else :
                #leftView.horizontalScrollBar().setValue(leftView.horizontalScrollBar().value() + 1)
                rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() + 1)

            aPoint = self.graphWindowRight.ui.graphicsView.mapToScene(QPoint(self.panCenterRight[0], self.panCenterRight[1]))
            diffX = aPoint.x() - bPoint.x()

            self.centerPixelRight = (self.centerPixelRight[0]-diffX, self.centerPixelRight[1]) 
            Z = self.dualManager.calculateZ(self.centerPixelLeft, self.centerPixelRight)
            self.optWindow.ui.lineEditCurrentZ.setText(str(round(Z,2)))


if __name__ == "__main__":
    app = stereoPhoto(sys.argv)
    sys.exit(app.exec_())