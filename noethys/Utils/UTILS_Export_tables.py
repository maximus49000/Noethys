#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:           Ivan LUCAS
# Copyright:       (c) 2010-12 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import shelve
import os
import cStringIO
import GestionDB

def InfosFichier(fichier=""):
    """ R�cup�re les infos principales sur un fichier """
    if os.path.isfile(fichier) == False :
        print "Pas de fichier a cet emplacement !"
        return None
    dictInfos = {}
    fichier = shelve.open(fichier.encode("iso-8859-15"), "r")
    for key, valeur in fichier.iteritems() :
        dictInfos[key] = valeur
    fichier.close()
    return dictInfos



class Exporter():
    def __init__(self, categorie="activite"):
        self.categorie = categorie
        self.contenu = []
        
    def Ajouter(self, ID=None, nom=""):
        self.listeTables = []
        self.DB = GestionDB.DB()
        self.dictID = {}
        self.correspondances_speciales = []
        self.Exporter(ID)
        self.contenu.append({
            "nom" : nom,
            "tables" : self.listeTables,
            "correspondances_speciales" : self.correspondances_speciales,
            })
        self.DB.Close()
                
    def GetListeChamps(self, nomTable=''):
        """ R�cup�ration des champs de la table """
        listeColonnes = self.DB.GetListeChamps2(nomTable)
        listeChamps = []
        for nomChamp, typeChamp in listeColonnes :
            listeChamps.append(nomChamp) 
        return listeChamps, listeColonnes
    
    def FormateCondition(self, nomChamp="", listeID=[]):
        if len(listeID) == 0 : sql = "%s IN ()" % nomChamp
        elif len(listeID) == 1 : sql = "%s=%d" % (nomChamp, listeID[0])
        else : sql = "%s IN %s" % (nomChamp, str(tuple(listeID)))
        return sql
        
    def Exporter(self, ID=None):
        """ Fonction � surcharger """
        self.ExporterTable("activites", "IDactivite=%d" % ID)
        self.ExporterTable("groupes", "IDactivite=%d" % ID)
        self.ExporterTable("agrements", "IDactivite=%d" % ID)
        # Unit�s
        self.ExporterTable("unites", "IDactivite=%d" % ID)
        self.ExporterTable("unites_groupes", self.FormateCondition("IDunite", self.dictID["unites"]))
        self.ExporterTable("unites_incompat", self.FormateCondition("IDunite", self.dictID["unites"]))
        # Unit�s de remplissage
        self.ExporterTable("unites_remplissage", "IDactivite=%d" % ID)
        self.ExporterTable("unites_remplissage_unites", self.FormateCondition("IDunite_remplissage", self.dictID["unites_remplissage"]))
        # Calendrier
        self.ExporterTable("ouvertures", "IDactivite=%d" % ID)
        self.ExporterTable("remplissage", "IDactivite=%d" % ID)
        # Tarifs
        self.ExporterTable("categories_tarifs", "IDactivite=%d" % ID)
        self.ExporterTable("noms_tarifs", "IDactivite=%d" % ID)
        self.ExporterTable("tarifs", "IDactivite=%d" % ID, [
                                                                                ("categories_tarifs", "IDcategorie_tarif", ";"),
                                                                                ("groupes", "IDgroupe", ";"),
                                                                                ("cotisations", None, ";"),
                                                                                ("caisses", None, ";"),
                                                                                ])
        self.ExporterTable("combi_tarifs", self.FormateCondition("IDtarif", self.dictID["tarifs"]))
        self.ExporterTable("combi_tarifs_unites", self.FormateCondition("IDtarif", self.dictID["tarifs"]))
        self.ExporterTable("tarifs_lignes", "IDactivite=%d" % ID)

        # Correspondances sp�ciales
        self.correspondances_speciales.append({"table" : "etiquettes", "champ" : "parent", "champ_reference" : "IDetiquette"})
        self.correspondances_speciales.append({"table" : "activites", "champ" : "psu_unite_prevision", "champ_reference" : "IDunite"})
        self.correspondances_speciales.append({"table" : "activites", "champ" : "psu_unite_presence", "champ_reference" : "IDunite"})
        self.correspondances_speciales.append({"table" : "activites", "champ" : "psu_tarif_forfait", "champ_reference" : "IDtarif"})
        self.correspondances_speciales.append({"table" : "activites", "champ" : "psu_etiquette_rtt", "champ_reference" : "IDetiquette"})


    def ExporterTable(self, nomTable="", condition="", chainesListes=[], remplacement=None):
        """ Exporter une table donn�e """
        listeChamps, listeColonnes = self.GetListeChamps(nomTable) 
        champCle = listeChamps[0]
        
        req = """SELECT %s
        FROM %s
        WHERE %s
        ;""" % (", ".join(listeChamps), nomTable, condition)
        self.DB.ExecuterReq(req)
        listeDonnees = self.DB.ResultatReq()
        
        listeID = []
        listeLignes = []
        for donnees in listeDonnees :
            indexColonne = 0
            dictLigne = {} 
            for donnee in donnees :
                nomChamp = listeColonnes[indexColonne][0]
                typeChamp = listeColonnes[indexColonne][1]
                
                # M�morisation de l'ID de la ligne
                if nomChamp == champCle :
                    listeID.append(donnee)
                
                # Pour les champs BLOB
                if (typeChamp == "BLOB" or typeChamp == "LONGBLOB") and donnee != None :
                    buffer = cStringIO.StringIO(donnee)
                    donnee = buffer.read()
                
                # Remplacement
                if remplacement != None :
                    if remplacement[0] == nomChamp :
                        donnee = remplacement[1]
                    
                dictLigne[nomChamp] = donnee
                indexColonne += 1
            listeLignes.append(dictLigne)
            
        self.listeTables.append((nomTable, listeLignes, chainesListes))
        self.dictID[nomTable] = listeID
    
    def Enregistrer(self, fichier=""):
        # Enregistrement dans un fichier Shelve
        fichier = shelve.open(fichier.encode("iso-8859-15"), "n")
        fichier["categorie"] = self.categorie
        fichier["contenu"] = self.contenu
        fichier.close()
    
    def GetContenu(self):
        return self.contenu
    
# -----------------------------------------------------------------------------------------------------

class Importer():
    def __init__(self, fichier=None, contenu=None):
        self.fichier = fichier
        
        # Get Donn�es
        if fichier != None :
            dictInfos = InfosFichier(self.fichier)
            self.categorie = dictInfos["categorie"]
            self.contenu = dictInfos["contenu"]
        else :
            self.categorie = ""
            self.contenu = contenu
    
    def DemandeChoix(self):
        listeContenu = self.GetNomContenu() 
        dlg = wx.MultiChoiceDialog(None, _(u"S�lectionnez le contenu � importer :"), _(u"Importation"), listeContenu)
        dlg.SetSelections(range(0, len(listeContenu)))
        if dlg.ShowModal() == wx.ID_OK :
            selections = dlg.GetSelections()
        else :
            selections = []
        dlg.Destroy()
        for index in selections :
            self.Ajouter(index, len(selections))
        return len(selections)

    def GetNomContenu(self):
        listeNoms = []
        for importation in self.contenu :
            listeNoms.append(importation["nom"])
        return listeNoms
    
    def Ajouter(self, index=0, nbre=0, dictID={}):
        dlgAttente = wx.BusyInfo(_(u"Merci de patienter..."), None)
        # Importation
        self.dictID = dictID
        self.DB = GestionDB.DB()
        importation = self.contenu[index]
        nom = importation["nom"]  
        listeTables = importation["tables"]
        if importation.has_key("correspondances_speciales") :
            correspondances_speciales = importation["correspondances_speciales"]
        else :
            correspondances_speciales = []
        self.Importer(listeTables, correspondances_speciales)
        self.DB.Close()
        del dlgAttente

    def GetTypesChamps(self, nomTable=''):
        """ R�cup�ration des types de champs de la table """
        listeColonnes = self.DB.GetListeChamps2(nomTable)
        dictChamps = {}
        for nomChamp, typeChamp in listeColonnes :
            dictChamps[nomChamp] = typeChamp
        champCle = listeColonnes[0][0]
        return dictChamps, champCle

    def Importer(self, listeTables=[], correspondances_speciales=[]):
        """ Proc�dure d'importation """
        # Importation des tables
        for nomTable, listeLignes, chainesListes in listeTables:
            self.ImporterTable(nomTable, listeLignes, chainesListes)

        # MAJ des correspondances sp�ciales
        for dictCorr in correspondances_speciales :
            table = dictCorr["table"]
            champ = dictCorr["champ"]
            champ_reference = dictCorr["champ_reference"]

            # Recherche les enregistrements de la table
            for nomTable, listeLignes, chainesListes in listeTables:
                if nomTable == table :
                    dictTypesChamps, champCle = self.GetTypesChamps(nomTable)

                    # Lignes
                    for ligne in listeLignes :

                        newIDligne = None
                        valeur_remplacement = None

                        # Colonnes
                        for nomChamp, valeur in ligne.iteritems() :

                            # Get newID de la ligne
                            if nomChamp == champCle :
                                newIDligne = self.dictID[champCle][valeur]

                            # recherche le champ � remplacer
                            if nomChamp == champ and valeur != None :
                                if self.dictID[champ_reference].has_key(valeur) :
                                    valeur_remplacement = self.dictID[champ_reference][valeur]
                                else :
                                    print "valeur non trouvee =", champ_reference, "avec la valeur", valeur

                        # Remplacement de la valeur
                        if newIDligne != None and valeur_remplacement != None :
                            self.DB.ReqMAJ(table, [(champ, valeur_remplacement),], champCle, newIDligne)


    def ImporterTable(self, nomTable="", listeLignes=[], chainesListes=[]):
        if len(listeLignes) == 0 : return
        
        # R�cup�re les types de champs
        dictTypesChamps, champCle = self.GetTypesChamps(nomTable)

        # Recherche le prochain ID
        prochainID = self.DB.GetProchainID(nomTable)

        # Duplique les lignes
        index_ligne = 0
        liste_ajouts = []
        liste_champs = []
        listeBlobs = []

        for ligne in listeLignes :

            # R�cup�ration des valeurs
            dictDonnees = {}
            ancienID = None
            newID = prochainID

            for nomChamp, valeur in ligne.iteritems() :
                
                if dictTypesChamps.has_key(nomChamp) :

                    if nomChamp == champCle :
                        ancienID = valeur
                    
                    # Blob
                    if "BLOB" in dictTypesChamps[nomChamp] and valeur != None :
                        listeBlobs.append({"table":nomTable, "champCle":champCle, "newID":newID, "valeur":valeur, "nomChamp":nomChamp})
                        valeur = None
                    
                    # Remplacement des ID avec le dict des correspondances
                    if self.dictID.has_key(nomChamp) :
                        if self.dictID[nomChamp].has_key(valeur) :
                            valeur = self.dictID[nomChamp][valeur]

                    # Remplacement d'un champ 'parent' (Pr�vu pour les �tiquettes dans les activit�s)
                    #if nomChamp == "parent" and valeur != None :
                    #    if self.dictID.has_key(champCle) :
                    #        if self.dictID[champCle].has_key(valeur) :
                    #            valeur = self.dictID[champCle][valeur]

                    # Cha�ne de liste
                    for nomChampChaine, champRemplacement, separateur in chainesListes :
                        if nomChamp == nomChampChaine :
                            if valeur == None or champRemplacement == None :
                                valeur = None
                            else :
                                listeTemp = []
                                for chaine in valeur.split(separateur) :
                                    donnee = int(chaine)
                                    if self.dictID.has_key(champRemplacement) :
                                        if self.dictID[champRemplacement].has_key(donnee) :
                                            donnee = self.dictID[champRemplacement][donnee]
                                    listeTemp.append(str(donnee))
                                valeur = separateur.join(listeTemp)
                            
                    # M�morisation des valeurs
                    if nomChamp != champCle :
                        dictDonnees[nomChamp] = valeur
                        if nomChamp not in liste_champs :
                            liste_champs.append(nomChamp)

            # Formatage des donn�es pour executermany
            listeDonnees = []
            for nomChamp in liste_champs :
                if dictDonnees.has_key(nomChamp) :
                    listeDonnees.append(dictDonnees[nomChamp])

            # Enregistrement
            liste_ajouts.append(listeDonnees)

            # M�morisation de L'ID dans la table des correspondances
            if self.dictID.has_key(champCle) == False :
                self.dictID[champCle] = {}
            self.dictID[champCle][ancienID] = newID

            prochainID += 1
            index_ligne += 1

        # Executermany sur toute la table � importer
        texteChampsTemp = ", ".join(liste_champs)
        listeInterrogations = []
        for champ in liste_champs :
            listeInterrogations.append("?")
        texteInterrogations = ", ".join(listeInterrogations)
        self.DB.Executermany("INSERT INTO %s (%s) VALUES (%s)" % (nomTable, texteChampsTemp, texteInterrogations), liste_ajouts, commit=True)

        # Enregistrement des blobs � part
        for dictblob in listeBlobs :
            self.DB.MAJimage(table=dictblob["table"], key=dictblob["champCle"], IDkey=dictblob["newID"], blobImage=dictblob["valeur"], nomChampBlob=dictblob["nomChamp"])

        return newID

    def ImporterTable_methodelente(self, nomTable="", listeLignes=[], chainesListes=[]):
        if len(listeLignes) == 0 : return

        # R�cup�re les types de champs
        dictTypesChamps, champCle = self.GetTypesChamps(nomTable)

        # Duplique les lignes
        index_ligne = 0
        for ligne in listeLignes :

            # R�cup�ration des valeurs
            listeDonnees = []
            dictBlobs = {}
            ancienID = None
            for nomChamp, valeur in ligne.iteritems() :

                if dictTypesChamps.has_key(nomChamp) :

                    if nomChamp == champCle :
                        ancienID = valeur

                    # Blob
                    if "BLOB" in dictTypesChamps[nomChamp] and valeur != None :
                        dictBlobs[nomChamp] = valeur
                        valeur = None

                    # Remplacement des ID avec le dict des correspondances
                    if self.dictID.has_key(nomChamp) :
                        if self.dictID[nomChamp].has_key(valeur) :
                            valeur = self.dictID[nomChamp][valeur]

                    # Remplacement d'un champ 'parent' (Pr�vu pour les �tiquettes dans les activit�s)
                    # if nomChamp == "parent" and valeur != None :
                    #     if self.dictID.has_key(champCle) :
                    #         if self.dictID[champCle].has_key(valeur) :
                    #             valeur = self.dictID[champCle][valeur]

                    # Cha�ne de liste
                    for nomChampChaine, champRemplacement, separateur in chainesListes :
                        if nomChamp == nomChampChaine :
                            if valeur == None or champRemplacement == None :
                                valeur = None
                            else :
                                listeTemp = []
                                for chaine in valeur.split(separateur) :
                                    donnee = int(chaine)
                                    if self.dictID.has_key(champRemplacement) :
                                        if self.dictID[champRemplacement].has_key(donnee) :
                                            donnee = self.dictID[champRemplacement][donnee]
                                    listeTemp.append(str(donnee))
                                valeur = separateur.join(listeTemp)

                    # M�morisation des valeurs
                    if nomChamp != champCle :
                        listeDonnees.append((nomChamp, valeur))

            # Enregistrement
            newID = self.DB.ReqInsert(nomTable, listeDonnees)

            # Enregistrement des blobs � part
            for nomChampBlob, blob in dictBlobs.iteritems() :
                self.DB.MAJimage(table=nomTable, key=champCle, IDkey=newID, blobImage=blob, nomChampBlob=nomChampBlob)

            # M�morisation de L'ID dans la table des correspondances
            if self.dictID.has_key(champCle) == False :
                self.dictID[champCle] = {}
            self.dictID[champCle][ancienID] = newID

            index_ligne += 1

        return newID

    def GetNewID(self, champCle="", ancienID=None):
        try :
            return self.dictID[champCle][ancienID]
        except :
            pass
        

if __name__ == "__main__":
    app = wx.App(0)
    
##    print "Exportation..."
##    exportation = Exporter(categorie="activite")
##    exportation.Ajouter(ID=2, nom=_(u"Activit�1"))
##    exportation.Enregistrer(fichier="Temp/test.npa")
    
##    print "Importation..."
##    importation = Importer(fichier="Temp/test.npa")
##    importation.DemandeChoix() 
##    #importation.Ajouter(index=0)
##    print "Fin."
    
    