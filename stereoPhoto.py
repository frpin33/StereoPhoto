'''
L'entièreté du code a été réalisé par Frédérick Pineault (frederick.pineault@mffp.gouv.qc.ca)

Ce dossier contient une classe de type QApplication qui permet l'affichage d'images de grandes tailles sur des 
écrans de type Planar

La classe stereoPhoto gère l'application complète via un interface utilisateur
L'application permet de :
    - Importer des fichiers TIF de grandes tailles via un drag n drop
    - Réaliser une rotation de 90°, 180° et 270°
    - Réaliser un effet miroir sur l'horizontal et la verticale
    - Afficher les deux images importées sur les écrans Planar
    - Superposer automatiquement les images en fonction de leur fichier PAR associé
    - Offrir une interface de navigation qui permet le déplacement, le zoom (CTRL+Roulette) et le traçage (Click & 1,2,3,ESC) 
    - Offrir un déplacement opposé des deux images pour ajuster la stéréoscopie (Roulette)
    - Rehausser les couleurs des images via une nouvelle fenêtre intéractive 
    - Traçage de forme géolocalisée
    - Communication avec QGIS

Le main permet tout simplement de lancer l'application

Plusieurs autres outils seront intégrés à cette application dans le futur :
    - Fonctionnalité de trace supplémentaire
    - Amélioration des fonctions de photogrammétrie 
    - Menu de choix de paramètres (numéro des écrans, curseur, keybinding, couleur des traces)
    - Affichage des zones supersposées seulement
    - Gestion de projet
    - Utiliser un shapefile déjà importé dans QGIS et afficher la région concernée  
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

from .ui_optionWindow import optionWindow
from .ui_graphicsWindow import graphicsWindow 
from .worldManager import pictureManager, dualManager
from .enhanceManager import enhanceManager, threadShow, imageEnhancing, pictureLayout
from .drawFunction import *
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
        
        self.action.setCheckable(True)
        self.action.toggled.connect(self.run)
         
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&StereoPhoto", self.action)

    #Retire le bout de l'application dans QGIS
    def unload(self):
        self.iface.removePluginMenu("&StereoPhoto", self.action)
        self.iface.removeToolBarIcon(self.action)
        
    #Initialisation de l'application, des variables
    #Connection entre les boutons du menu d'options (mOpt) et leur fonction attitrée
    #On fait apparaître le menu des options seul
    #Les écrans où l'on veut que les fênetres s'ouvrent sont choisi ici 
    def run(self):

        if self.action.isChecked() :
            self.intRightScreen = 1
            self.intLeftScreen = 2

            #Sur Windows 10 la barre windows en bas existe sur toutes les écrans, faire attention pour ce cas
            #Sur windows 10 il y a un problème avec le Pan et le retour au centre, il y a un plus grand décalage que celui désiré (seulement sur windows 10?)
            #Problème avec mon PC trop lent?
            self.screenRight = QApplication.desktop().screenGeometry(self.intRightScreen)
            self.screenLeft = QApplication.desktop().screenGeometry(self.intLeftScreen)

            self.panCenterLeft = (int(self.screenLeft.width()/2), int(self.screenLeft.height()/2))
            self.panCenterRight = (int(self.screenRight.width()/2), int(self.screenRight.height()/2))
            self.leftScreenCenter = ( self.screenLeft.x() + int(self.screenLeft.width()/2), self.screenLeft.y() + int(self.screenLeft.height()/2))

            self.leftOrientation = 0
            self.rightOrientation = 0
            self.leftMiroir = 0
            self.rightMiroir = 0


            self.leftName = False 
            self.rightName = False 
            self.anaglyphActivate = False 

            self.showThreadLeftInProcess = False
            self.newLeftRequest = False
            self.showThreadRightInProcess = False
            self.newRightRequest = False
            self.enableDraw = False
            self.enableShow = False

            #MTM 1 à 17 prendre de 32181 à 32197 
            #MTM 10 32190
            #MTM 9  32189   
            self.crs = 32190
            self.Z = 300

            self.polygonOnLeftScreen = []
            self.polygonOnRightScreen = []

            self.listParam = [0, 0, 0, 0, 0, 0, 0, False, False, []]

            self.optWindow = optionWindow()

            self.optWindow.ui.boxMiroirLeft.currentIndexChanged.connect(self.mMiroirLeft)
            self.optWindow.ui.boxMiroirRight.currentIndexChanged.connect(self.mMiroirRight)
            self.optWindow.ui.boxOrientationLeft.currentIndexChanged.connect(self.mOrientationLeft)
            self.optWindow.ui.boxOrientationRight.currentIndexChanged.connect(self.mOrientationRight)
            self.optWindow.ui.importLineLeft.textChanged.connect(self.mNewLeftPic)
            self.optWindow.ui.importLineRight.textChanged.connect(self.mNewRightPic)
            self.optWindow.ui.importLineVectorLayer.textChanged.connect(self.mNewVectorLayer)
            
            #self.optWindow.ui.importButtonLeft.clicked.connect(self.getShowRect)
            self.optWindow.ui.importButtonLeft.clicked.connect(self.mImportLeft)
            self.optWindow.ui.importButtonRight.clicked.connect(self.mImportRight)
            
            self.optWindow.ui.panButton.clicked.connect(self.panClick)
            self.optWindow.ui.enhanceButton.clicked.connect(self.enhanceClick)
            self.optWindow.keyDrawEvent.connect(self.keyboardHandler)

            self.optWindow.ui.affichageButton.clicked.connect(self.loadWindows)
            self.optWindow.closeWindow.connect(self.optWindowClose)

            self.optWindow.show()
        
        else:
            self.optWindowClose()


    #Fonction appelée lors de la fermeture du mOpt
    #Si l'on ferme le mOpt toutes les autres fenêtres Qt se ferment
    def optWindowClose(self):
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
        self.optWindow.close()
        
    #Fonction de traitement d'image pour modifier l'orientation
    #Les angles de rotation possible sont 0, 90, 180 et 270
    def mOrientationLeft(self, value):
        self.leftOrientation = value
        QtImg = pictureLayout(self.demoLeftPic, self.leftOrientation, self.leftMiroir, True)
        scene = QGraphicsScene()
        scene.addPixmap(QPixmap.fromImage(QtImg))
        self.optWindow.ui.graphicsViewLeft.setScene(scene)
        self.optWindow.ui.graphicsViewLeft.fitInView(self.optWindow.ui.graphicsViewLeft.sceneRect(), Qt.KeepAspectRatio)

    #Idem à mOrientationLeft
    def mOrientationRight(self, value):
        self.rightOrientation = value
        QtImg = pictureLayout(self.demoRightPic, self.rightOrientation, self.rightMiroir, True)
        scene = QGraphicsScene()
        scene.addPixmap(QPixmap.fromImage(QtImg))
        self.optWindow.ui.graphicsViewRight.setScene(scene)
        self.optWindow.ui.graphicsViewRight.fitInView(self.optWindow.ui.graphicsViewRight.sceneRect(), Qt.KeepAspectRatio)
        
    #Fonction de traitement d'image pour ajouter un effet mirroir à l'image
    #Deux modes sont possible, soit un effet mirroir à l'horizontal et un à la verticale
    def mMiroirLeft(self, value):
        self.leftMiroir = value
        QtImg = pictureLayout(self.demoLeftPic, self.leftOrientation, self.leftMiroir, True)
        scene = QGraphicsScene()
        scene.addPixmap(QPixmap.fromImage(QtImg))
        self.optWindow.ui.graphicsViewLeft.setScene(scene)
        self.optWindow.ui.graphicsViewLeft.fitInView(self.optWindow.ui.graphicsViewLeft.sceneRect(), Qt.KeepAspectRatio)
        
    #Idem à mMiroirLeft
    def mMiroirRight(self,value):
        self.rightMiroir = value
        QtImg = pictureLayout(self.demoRightPic, self.rightOrientation, self.rightMiroir, True)
        scene = QGraphicsScene()
        scene.addPixmap(QPixmap.fromImage(QtImg))
        self.optWindow.ui.graphicsViewRight.setScene(scene)
        self.optWindow.ui.graphicsViewRight.fitInView(self.optWindow.ui.graphicsViewRight.sceneRect(), Qt.KeepAspectRatio)


    #Fonction réaliser lorsqu'une photo est importée 
    #Elle permet de rendre le panneau de fonctionnalité accessible à l'utilisateur 
    #pour le traitement d'image ainsi que le bouton d'importation
    #L'image est affiché en petit format pour permettre une visualisation du 
    #résultat qui sera produit suite à l'importation  
    #Si une nouvelle photo est importée, l'ancienne est fermée 
    #Si la photo est un fichier tif avec plusieurs versions de l'image, 
    #on récupère une version plus petite plutot que la produire, le résultat est donc instantané
    #Création d'un pictureManager pour associer les pixels à des coordonnées en fonction du .par de la photo
    def mNewLeftPic(self) : 

        self.optWindow.ui.boxOrientationLeft.setCurrentIndex(0)
        self.optWindow.ui.boxMiroirLeft.setCurrentIndex(0)
          
        self.leftName = False
        self.optWindow.ui.affichageButton.setEnabled(False)

        try :
            del self.graphWindowLeft
            self.graphWindowRight.close()
        except :
            pass

        self.leftPic = Image.open(self.optWindow.ui.importLineLeft.text())
        self.demoLeftPic = Image.open(self.optWindow.ui.importLineLeft.text())

        if hasattr(self.demoLeftPic, "n_frames"): 
            for i in range(self.demoLeftPic.n_frames):
                self.demoLeftPic.seek(i)
                if self.demoLeftPic.size < (200,200) :
                    self.demoLeftPic.seek(i-1)
                    break

        elif self.leftPic.size[0] > self.leftPic.size[1] :
            self.demoLeftPic = self.leftPic.resize((300,200))
        else :
            self.demoLeftPic = self.leftPic.resize((200,300))

        draw = ImageDraw.Draw(self.demoLeftPic)
        draw.ellipse((20,20,60,60), fill="red", outline="white")
        
        npPicture = np.array(self.demoLeftPic)
        sceneLeft = QGraphicsScene()
        img = qimage2ndarray.array2qimage(npPicture)
        sceneLeft.addPixmap(QPixmap.fromImage(img))

        self.optWindow.ui.graphicsViewLeft.setScene(sceneLeft)
        self.optWindow.ui.graphicsViewLeft.show()
        self.optWindow.ui.graphicsViewLeft.fitInView(self.optWindow.ui.graphicsViewLeft.sceneRect(), Qt.KeepAspectRatio)
        self.optWindow.ui.label.setEnabled(True)
        self.optWindow.ui.label_2.setEnabled(True)
        self.optWindow.ui.boxMiroirLeft.setEnabled(True)        
        self.optWindow.ui.boxOrientationLeft.setEnabled(True)
        self.optWindow.ui.importButtonLeft.setEnabled(True)
        self.optWindow.ui.importDoneLeft.setStyleSheet("image: url(:/Anaglyph/Icons/redCross.png);")

        self.graphWindowLeft = graphicsWindow("Image Gauche")
        self.graphWindowLeft.setWindowState(Qt.WindowMaximized)
        rect = QRect(0,0,self.screenLeft.width(),self.screenLeft.height())
        self.graphWindowLeft.ui.graphicsView.setGeometry(rect)
        self.graphWindowLeft.ui.widget.setGeometry(rect)
        self.graphWindowLeft.move(QPoint(self.screenLeft.x(), self.screenLeft.y()))
        self.graphWindowLeft.keyDrawEvent.connect(self.keyboardHandler)

        fname = self.optWindow.ui.importLineLeft.text()
        filename = "/" +  fname.split("/")[-1].split(".")[0]
        self.path = fname.partition(filename)[0]

        pathPAR = self.optWindow.ui.importLineLeft.text().split(".")[0] + ".par"
        self.leftPictureManager = pictureManager(self.leftPic.size, pathPAR, "aa")
        self.leftPicSize = self.leftPic.size

    #Idem à mNewLeftPic
    def mNewRightPic(self):
        
        self.optWindow.ui.boxOrientationRight.setCurrentIndex(0)
        self.optWindow.ui.boxMiroirRight.setCurrentIndex(0)

        self.rightOrientation = 0
        self.rightMiroir = 0
        self.rightName = False
        self.optWindow.ui.affichageButton.setEnabled(False)

        try :
            del self.graphWindowRight
            self.graphWindowLeft.close()
        except :
            pass

        self.rightPic = Image.open(self.optWindow.ui.importLineRight.text())
        self.demoRightPic = Image.open(self.optWindow.ui.importLineRight.text())

        if hasattr(self.demoRightPic, "n_frames"): #and format == tif??
            for i in range(self.demoRightPic.n_frames):
                self.demoRightPic.seek(i)
                if self.demoRightPic.size < (200,200) :
                    self.demoRightPic.seek(i-1)
                    break

        elif self.rightPic.size[0] > self.rightPic.size[1] :
            self.demoRightPic = self.rightPic.resize((300,200))
        else :
            self.demoRightPic = self.rightPic.resize((200,300))

        draw = ImageDraw.Draw(self.demoRightPic)
        draw.ellipse((20,20,60,60), fill="red", outline="white")

        npPicture = np.array(self.demoRightPic)
        img = qimage2ndarray.array2qimage(npPicture)

        sceneRight = QGraphicsScene()
        sceneRight.addPixmap(QPixmap.fromImage(img))
        self.optWindow.ui.graphicsViewRight.setScene(sceneRight)
        self.optWindow.ui.graphicsViewRight.show()
        self.optWindow.ui.graphicsViewRight.fitInView(self.optWindow.ui.graphicsViewRight.sceneRect(), Qt.KeepAspectRatio)
        self.optWindow.ui.importButtonRight.setEnabled(True)
        self.optWindow.ui.label_3.setEnabled(True)
        self.optWindow.ui.label_4.setEnabled(True)        
        self.optWindow.ui.boxMiroirRight.setEnabled(True)        
        self.optWindow.ui.boxOrientationRight.setEnabled(True)
        self.optWindow.ui.importDoneRight.setStyleSheet("image: url(:/Anaglyph/Icons/redCross.png);")

        self.graphWindowRight = graphicsWindow("Image Droite")
        self.graphWindowRight.setWindowState(Qt.WindowMaximized)
        rect = QRect(0,0,self.screenRight.width(),self.screenRight.height())
        self.graphWindowRight.ui.graphicsView.setGeometry(rect)
        self.graphWindowRight.ui.widget.setGeometry(rect)
        self.graphWindowRight.move(QPoint(self.screenRight.x(), self.screenRight.y()))

        pathPAR = self.optWindow.ui.importLineRight.text().split(".")[0] + ".par"
        self.rightPictureManager = pictureManager(self.rightPic.size, pathPAR, "aa")
        self.rightPicSize = self.rightPic.size

    #Fonction qui créer une nouvelle couche de type VectorLayer dans QGIS 
    #La couche permet d'afficher les polygones tracés sur l'image dans QGIS
    def mNewVectorLayer(self):
        #shapeName = self.optWindow.ui.importLineVectorLayer.text()
            
        self.enableDraw = True

        self.vectorLayer = self.optWindow.vLayer
        QgsProject.instance().setCrs(self.vectorLayer.crs())

        if self.enableShow :
            self.addPolygonOnScreen()

    
    def getShowRect(self) :
        
        #Serait appeler dans le import donc non nécessaire
        #self.dualManager = dualManager(self.leftPictureManager, self.rightPictureManager, self.Z)
        #self.leftRect, self.rightRect = self.dualManager.getRect()
        
        #print(self.leftRect)
        #print(self.rightRect)
        
        
        #endRight = [-self.rightRect.x() + self.rightRect.width(), self.rightRect.y() + self.rightRect.height()]
        if hasattr(self, "leftRect"): 
            endLeft = [self.leftRect.x() + self.leftRect.width(), self.leftRect.y() + self.leftRect.height()]
            topXL, topYL = self.leftPictureManager.pixelToCoord([self.leftRect.x(),self.leftRect.y()],self.Z)
            botXL, botYL = self.leftPictureManager.pixelToCoord(endLeft,self.Z)
            rectL = QgsRectangle(QgsPointXY(topXL, topYL), QgsPointXY(botXL, botYL))
            return rectL
        
        else :
            return QgsRectangle(QgsPointXY(0, 0), QgsPointXY(0, 0))
        
        #topXR, topYR = self.rightPictureManager.pixelToCoord([-self.rightRect.x(),self.rightRect.y()],self.Z)
        #botXR, botYR = self.rightPictureManager.pixelToCoord(endRight,self.Z)
        
        #print(topXL)
        #print(topYL)
        #print(botXL)
        #print(botYL)

        #vLayer = getVectorLayer()
        
        
        #Autant Left que Right donnent les mêmes rectangles.
        #rectR = QgsRectangle(QgsPointXY(topXR, topYR), QgsPointXY(botXR, botYR))
        #R = getRectPolygon(rectR, vLayer)
        #L = getRectPolygon(rectL, vLayer)

    def dualPixelToCoord(self, QPointLeft, QPointRight):
        pixL = (QPointLeft.x(), QPointLeft.y())
        mirrorX = self.rightPicSize[0] - QPointRight.x()
        pixR = (mirrorX, QPointRight.y())
        #print(pixL[0]) 
        #print(pixL[1])
        #print(pixR[0])
        #print(pixR[1])
        Z = self.dualManager.calculateZ(pixL, pixR)
        XL, YL = self.leftPictureManager.pixelToCoord(pixL, Z)
        XR, YR = self.rightPictureManager.pixelToCoord(pixR, Z)
        


        a = "" + str()
        print(a)

        X = (XL + XR) / 2
        Y = (YL + YR) / 2
        
        
        a = "XL : " + str(XL)
        #print(a)
        a = "XR : " + str(XR)
        #print(a)
        a = "X : " + str(X)
        #print(a)
        a = "YL : " + str(YL)
        #print(a)
        a = "YR : " + str(YR)
        #print(a)
        a = "Y : " + str(Y)
        #print(a)
        
        a = "Z : " + str(Z)
        #print(a)
        return X, Y
        #Tester quelques résultats pour voir la différence (on parle de combien de M/CM)
        #Moyenner sur les deux valeurs si différence petite sinon prendre LEFT pour commencer.

    
    #Fonction qui lance l'affichage des deux fenêtres sur les écrans Planar (choix dans l'init)
    #Création du dualManager qui utilise les pictures managers pour positionner les photos selon les régions superposées
    #Affichage de l'image complète
    #Affichage d'un curseur au centre des fenêtres  
    def loadWindows(self, value):

        self.graphWindowLeft.close()
        self.graphWindowRight.close()

        self.dualManager = dualManager(self.leftPictureManager, self.rightPictureManager, self.Z)
        self.leftRect, self.rightRect = self.dualManager.getRect()
        self.graphWindowLeft.cursorRectInit(self.screenLeft.width(), self.screenLeft.height())
        self.graphWindowRight.cursorRectInit(self.screenRight.width(), self.screenRight.height())

        r = self.dualManager.calculateZ([9357,8860], [4861,8876])
        a = self.leftPictureManager.pixelToCoord([9357,8860],self.Z)
        b = self.rightPictureManager.coordToPixel(a,self.Z)

        self.graphWindowLeft.show()
        self.graphWindowRight.show()
        self.graphWindowLeft.ui.graphicsView.fitInView(self.leftRect, Qt.KeepAspectRatio)
        self.graphWindowRight.ui.graphicsView.fitInView(self.rightRect, Qt.KeepAspectRatio)
        self.optWindow.activateWindow()
        self.optWindow.ui.panButton.setEnabled(True)
        self.enableShow = True

        if self.enableDraw :
            self.addPolygonOnScreen()

    def addPolygonOnScreen(self) :
        rectCoord = self.getShowRect()
        listGeo = list(self.vectorLayer.getFeatures(rectCoord))
            
        for item in listGeo : 
            featureGeo = item.geometry()
            
            if featureGeo.isNull() == False :

                listQgsPoint = featureGeo.asMultiPolygon()[0][0]
                polygonL = QPolygonF()
                polygonR = QPolygonF()
                for point in listQgsPoint :
                    xPixel, yPixel = self.leftPictureManager.coordToPixel((point.x() , point.y()), self.Z)     
                    polygonL.append(QPointF(xPixel, yPixel))
                    xRPixel = -xPixel + self.rightPicSize[0] + self.rightRect.x() + self.leftRect.x()
                    polygonR.append(QPointF(xRPixel, yPixel))

                m_pen = QPen(QColor(0, 255, 255),10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                leftObj = self.graphWindowLeft.ui.graphicsView.scene().addPolygon(polygonL, m_pen)
                rightObj = self.graphWindowRight.ui.graphicsView.scene().addPolygon(polygonR, m_pen)
                self.polygonOnLeftScreen.append(leftObj)
                self.polygonOnRightScreen.append(rightObj)

    #Fonction pour zoom In sur les deux photos simultannément
    def mZoomIn(self) :
        self.graphWindowLeft.ui.graphicsView.scale(1.25, 1.25)
        self.graphWindowRight.ui.graphicsView.scale(1.25, 1.25)

    #Fonction pour zoom Out sur les deux photos simultannément
    def mZoomOut(self):
        self.graphWindowLeft.ui.graphicsView.scale(0.8, 0.8)
        self.graphWindowRight.ui.graphicsView.scale(0.8, 0.8)

    #Fonction pour permettre l'imporation de l'image sur le graphicsView
    #Similaire au fichier enhanceManager, une version de basse résolution de l'image est affichée immédiatement
    #Par la suite, un un thread est lancer pour venir afficher les plus hautes résolutions
    #Le rehaussement, la rotation et l'effet miroir sont considérés
    #Les connections pour les fonctiones de navigations sont établies
    def mImportLeft(self):

        if hasattr(self, "tSeekLeft"): 
            try :
                self.tSeekLeft.newImage.disconnect(self.addLeftPixmap)
            except: 
                pass
            self.tSeekLeft.keepRunning = False

        self.optWindow.ui.importDoneLeft.setStyleSheet("image: url(:/Anaglyph/Icons/loading.png);")
        self.optWindow.ui.importButtonLeft.setEnabled(False)
        
        self.leftPic.seek(3)

        t = imageEnhancing(self.leftPic, self.listParam)
        t.start()
        r = t.join()
        enhancePic = Image.merge("RGB", (r[0],r[1],r[2]))
        
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
            #self.threadSeekLeft(pointZero, pointMax, 0.5, 1, 2)
            self.showThreadLeftInProcess = True
        else :
            self.newLeftRequest = True

        self.graphWindowLeft.ui.widget.mouseMoveEvent = self.mMoveEvent
        self.graphWindowLeft.ui.widget.mousePressEvent = self.mPressEvent
        self.graphWindowLeft.ui.widget.wheelEvent = self.wheelEvent
        self.graphWindowLeft.ui.graphicsView.show()
        self.optWindow.ui.importDoneLeft.setStyleSheet("image: url(:/Anaglyph/Icons/greenCheck.png);")
        self.optWindow.ui.importButtonLeft.setEnabled(True)
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
            #self.threadSeekRight(pointZero, pointMax, 0.5, 1, 2)
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


    #Utiliser par threadShow pour afficher une portion de l'image
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
    #Elle relance le thread avec la même résolution si une requête a été faite sinon
    #elle relance le thread avec une plus grande résolution d'image 
    def seekLeftDone(self):

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
            if self.enableDraw : 
                self.optWindow.ui.drawButton.setEnabled(True)
                self.optWindow.ui.cutButton.setEnabled(True)
        
        else : 
            self.optWindow.ui.drawButton.setEnabled(False)
            self.optWindow.ui.cutButton.setEnabled(False)
            self.graphWindowLeft.ui.widget.setMouseTracking(False)
            win32api.SetCursorPos((self.optWindow.pos().x(), self.optWindow.pos().y()))
            self.graphWindowLeft.setCursor(self.graphWindowLeft.normalCursor)

    #Désactive le cut pour activer le draw
    #Initialise les variables de dessins à un état de base (aucun polygon)
    def drawClick(self):
        self.optWindow.ui.cutButton.setChecked(False)
        self.optWindow.ui.drawButton.setChecked(True)

        self.listDrawCoord = []
        self.listLeftLineObj = []
        self.listRightLineObj = []
        self.firstDrawClick = True
        self.currentLeftLineObj = None
        self.currentRightLineObj = None

    #Désactive le draw pour activer le cut
    #Initialise les variables de dessins à un état de base (aucun polygon)
    def cutClick(self):
        self.optWindow.ui.cutButton.setChecked(True)
        self.optWindow.ui.drawButton.setChecked(False)

        self.listDrawCoord = []
        self.listLeftLineObj = []
        self.listRightLineObj = []
        self.firstDrawClick = True
        self.currentLeftLineObj = None
        self.currentRightLineObj = None
    
    #Ouverture de la fenêtre de rehaussement
    def enhanceClick(self):
        nameLeft = self.optWindow.ui.importLineLeft.text()
        nameRight = self.optWindow.ui.importLineRight.text()
        self.enhanceManager = enhanceManager(nameLeft, nameRight, self.listParam)
        self.enhanceManager.listParamSignal.connect(self.applyEnhance)

    #Permet le lancement du traitement de modification des images
    def applyEnhance(self, listParam):
        self.enhanceManager.listParamSignal.disconnect(self.applyEnhance)
        self.listParam = listParam
        self.mImportLeft()
        self.mImportRight()

    #Fonction appelée lorsque les touches respectives du clavier sont appuyées
    #Les touches sont utiles lorsque le mode pan est en cours d'utilisation
    #Possibilité d'ajouter d'autres fonctions plus tard
    def keyboardHandler(self, number):
        
        if number == "1" :
            if self.optWindow.ui.drawButton.isChecked() :
                self.optWindow.ui.drawButton.setChecked(False)
            elif self.enableDraw :
                self.drawClick()
        
        elif number == "2" :
            if self.optWindow.ui.cutButton.isChecked() :
                self.optWindow.ui.cutButton.setChecked(False)
            elif self.enableDraw :
                self.cutClick()
        
        elif number == "3" :

            if self.optWindow.ui.radioButtonMerge.isChecked():
                self.optWindow.ui.radioButtonAuto.setChecked(True)
                self.optWindow.ui.radioButtonMerge.setChecked(False)

            elif self.optWindow.ui.radioButtonAuto.isChecked() :
                self.optWindow.ui.radioButtonAuto.setChecked(False)
                self.optWindow.ui.radioButtonMerge.setChecked(True)

        elif number == "ESC":
            self.optWindow.ui.panButton.setChecked(False)
            self.panClick()
            

    #Fonction qui réalise le pan et qui permet de prévisualiser la trace à venir
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
            leftView.verticalScrollBar().setValue(leftView.verticalScrollBar().value() - self.deltaY)
            rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() + self.deltaX)
            rightView.verticalScrollBar().setValue(rightView.verticalScrollBar().value() - self.deltaY)
        
            if (self.optWindow.ui.drawButton.isChecked() or self.optWindow.ui.cutButton.isChecked()) and not self.firstDrawClick :

                
                pointL = QPoint(self.panCenterLeft[0], self.panCenterLeft[1])
                #centerX = self.rightPicSize[0] - self.panCenter[0]
                pointR = QPoint(self.panCenterRight[0], self.panCenterRight[1])
                self.endDrawPointLeft = self.graphWindowLeft.ui.graphicsView.mapToScene(pointL)
                self.endDrawPointRight = self.graphWindowRight.ui.graphicsView.mapToScene(pointR)
                lineL = QLineF(self.startDrawPointLeft, self.endDrawPointLeft)
                
                xStartPoint = -self.startDrawPointLeft.x() + self.rightPicSize[0] + self.rightRect.x() + self.leftRect.x()
                startRightPoint = QPointF(xStartPoint, self.startDrawPointLeft.y())
                
                xEndPoint = -self.endDrawPointLeft.x() + self.rightPicSize[0] + self.rightRect.x() + self.leftRect.x()
                endRightPoint = QPointF(xEndPoint, self.endDrawPointLeft.y())
                
                lineR = QLineF(startRightPoint, endRightPoint)

                m_pen = QPen(QColor(0, 255, 255),10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

                if self.currentLeftLineObj:
                    self.graphWindowLeft.ui.graphicsView.scene().removeItem(self.currentLeftLineObj)
                
                if self.currentRightLineObj:
                    self.graphWindowRight.ui.graphicsView.scene().removeItem(self.currentRightLineObj)
                    
                self.currentLeftLineObj = self.graphWindowLeft.ui.graphicsView.scene().addLine(lineL, m_pen)
                self.currentRightLineObj = self.graphWindowRight.ui.graphicsView.scene().addLine(lineR, m_pen)

    #Fonction réalisé lors du click sur l'image
    #La fonctionnalité sont possible seulement lorque le mode Pan est activé
    #En mode Draw/Cut Polygon, elle trace les lignes et les polygones sur l'image
    #Il y a une communication avec QGIS pour afficher les polygones dans le logiciel
    #Lorsque les polygones se croisent, les polygones peuvent merger ou se séparer automatiquement
    #Il est aussi possible de découper les polygones
    #Les polygones s'affichent sur les deux images
    #Le click droit permet de terminer une trace ou de quitter le pan si aucune option est sélectionné
    def mPressEvent(self, ev):

        if self.optWindow.ui.panButton.isChecked():
            
            if self.optWindow.ui.drawButton.isChecked() or self.optWindow.ui.cutButton.isChecked():

                if ev.button() == Qt.LeftButton:
                    if self.firstDrawClick :
                        pointL = QPoint(self.panCenterLeft[0], self.panCenterLeft[1])
                        pointR = QPoint(self.panCenterRight[0], self.panCenterRight[1])
                        self.startDrawPointLeft = self.graphWindowLeft.ui.graphicsView.mapToScene(pointL)
                        self.startDrawPointRight = self.graphWindowRight.ui.graphicsView.mapToScene(pointR)
                        self.firstDrawClick = False
                    else : 
                        self.startDrawPointLeft = self.endDrawPointLeft
                        self.startDrawPointRight = self.endDrawPointRight
                        self.listLeftLineObj.append(self.currentLeftLineObj)
                        self.listRightLineObj.append(self.currentRightLineObj)
                        self.currentLeftLineObj = None
                        self.currentRightLineObj = None
                    
                    #X, Y = self.leftPictureManager.pixelToCoord((self.startDrawPointLeft.x() , self.startDrawPointLeft.y()), self.Z)
                    #Replace here dualPixel to Coord
                    # rPoint = self.graphWindowRight.ui.graphicsView.mapToScene(point) -> QPointF
                    X, Y = self.dualPixelToCoord(self.startDrawPointLeft, self.startDrawPointRight)
                    #self.dualPixelToCoord(self.startDrawPointLeft, self.startDrawPointRight)
                    self.listDrawCoord.append(QgsPointXY(X,Y))

                elif ev.button() == Qt.RightButton:

                    self.firstDrawClick = True
                    if self.currentLeftLineObj :
                        self.graphWindowLeft.ui.graphicsView.scene().removeItem(self.currentLeftLineObj)
                        self.currentLeftLineObj = None

                    if self.currentRightLineObj :
                        self.graphWindowRight.ui.graphicsView.scene().removeItem(self.currentRightLineObj)
                        self.currentRightLineObj = None
                    
                    for item in self.listLeftLineObj:
                        self.graphWindowLeft.ui.graphicsView.scene().removeItem(item)
                    self.listLeftLineObj = []

                    for item in self.listRightLineObj:
                        self.graphWindowRight.ui.graphicsView.scene().removeItem(item)
                    self.listRightLineObj = []
                    
                    if self.optWindow.ui.drawButton.isChecked():
                        newGeo = QgsGeometry.fromMultiPolygonXY([[self.listDrawCoord]])
                        currentVectorLayer = self.vectorLayer
                        
                        rectCoord = self.getShowRect()
                        listGeo = list(currentVectorLayer.getFeatures(rectCoord))
                        #Gestion des plusieurs intersections à faire
                        for item in listGeo : 
                            featureGeo = item.geometry()
                            
                            if newGeo.intersects(featureGeo) :
                                if self.optWindow.ui.radioButtonMerge.isChecked() :
                                    mergePolygon(featureGeo, item.id(), newGeo, currentVectorLayer)
                                else :
                                    automaticPolygon(featureGeo, item.id(), newGeo, currentVectorLayer)
                                break
                                
                        else :
                            addPolygon(currentVectorLayer, newGeo)
                    else :
                        currentVectorLayer = self.vectorLayer    
                        cutPolygon(currentVectorLayer, self.listDrawCoord)
                    
                    self.listDrawCoord = []
                    
                    for item in self.polygonOnLeftScreen :
                        self.graphWindowLeft.ui.graphicsView.scene().removeItem(item)
                    self.polygonOnLeftScreen = []

                    for item in self.polygonOnRightScreen :
                        self.graphWindowRight.ui.graphicsView.scene().removeItem(item)
                    self.polygonOnRightScreen = []
                    
                    self.addPolygonOnScreen()
                    
            
            elif ev.button() == Qt.RightButton :
                self.optWindow.ui.panButton.setChecked(False)
                self.panClick()

    #Fonction pour zoom In/Out sur les photos avec la souris, elle zoom dans la 
    #direction de la souris 
    def wheelEvent(self, event):
        factor = 1.41 ** (event.angleDelta().y() / 240.0)
        leftView = self.graphWindowLeft.ui.graphicsView
        rightView = self.graphWindowRight.ui.graphicsView
        if self.optWindow.ctrlClick or self.graphWindowLeft.ctrlClick or self.graphWindowRight.ctrlClick :
            oldPos = self.graphWindowLeft.ui.graphicsView.mapToScene(event.pos())
            if factor > 1 : 
                self.mZoomIn()
            else :
                self.mZoomOut()

            newPos = self.graphWindowLeft.ui.graphicsView.mapToScene(event.pos())
            delta = newPos- oldPos

            self.graphWindowRight.ui.graphicsView.setTransformationAnchor(QGraphicsView.NoAnchor)
            self.graphWindowLeft.ui.graphicsView.setTransformationAnchor(QGraphicsView.NoAnchor)
            self.graphWindowRight.ui.graphicsView.translate(-delta.x(), delta.y())
            self.graphWindowLeft.ui.graphicsView.translate(delta.x(), delta.y())
            self.graphWindowRight.ui.graphicsView.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
            self.graphWindowLeft.ui.graphicsView.setTransformationAnchor(QGraphicsView.AnchorViewCenter)
            
        else : 
            if factor > 1 : 
                leftView.horizontalScrollBar().setValue(leftView.horizontalScrollBar().value() - 3)
                rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() - 3)
            else :
                leftView.horizontalScrollBar().setValue(leftView.horizontalScrollBar().value() + 3)
                rightView.horizontalScrollBar().setValue(rightView.horizontalScrollBar().value() + 3)


if __name__ == "__main__":
    app = stereoPhoto(sys.argv)
    sys.exit(app.exec_())