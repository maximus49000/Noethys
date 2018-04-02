#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-
#------------------------------------------------------------------------
# Application :    Noethys, gestion multi-activit�s
# Site internet :  www.noethys.com
# Auteur:          Ivan LUCAS
# Copyright:       (c) 2010-18 Ivan LUCAS
# Licence:         Licence GNU GPL
#------------------------------------------------------------------------


import Chemins
from Utils import UTILS_Adaptations
from Utils.UTILS_Traduction import _
import wx
from Ctrl import CTRL_Bouton_image
import os
import traceback
import GestionDB

from Ctrl import CTRL_Bandeau
from Ctrl import CTRL_Liste_inscriptions
from Ctrl import CTRL_Inscriptions_options
from Utils import UTILS_Inscriptions
from Utils import UTILS_Envoi_email


class Dialog(wx.Dialog):
    def __init__(self, parent, filtres=[]):
        wx.Dialog.__init__(self, parent, -1, style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MAXIMIZE_BOX|wx.MINIMIZE_BOX)
        self.parent = parent
        
        # Bandeau
        intro = _(u"Cochez les inscriptions � envoyer par Email puis cliquez sur le bouton 'Transf�rer vers l'�diteur d'Emails'.")
        titre = _(u"Envoi de inscriptions par Email")
        self.SetTitle(titre)
        self.ctrl_bandeau = CTRL_Bandeau.Bandeau(self, titre=titre, texte=intro, hauteurHtml=30, nomImage="Images/32x32/Emails_piece.png")
        
        # Inscriptions
        self.box_inscriptions_staticbox = wx.StaticBox(self, -1, _(u"Liste des inscriptions"))
        self.ctrl_liste_inscriptions = CTRL_Liste_inscriptions.CTRL(self, filtres=filtres)
        
        # Options
        self.box_options_staticbox = wx.StaticBox(self, -1, _(u"Options des inscriptions"))
        self.ctrl_options = CTRL_Inscriptions_options.CTRL(self)
        
        # Boutons
        self.bouton_aide = CTRL_Bouton_image.CTRL(self, texte=_(u"Aide"), cheminImage="Images/32x32/Aide.png")
        self.bouton_ok = CTRL_Bouton_image.CTRL(self, texte=_(u"Transf�rer vers l'�diteur d'Emails"), cheminImage="Images/32x32/Emails_piece.png")
        self.bouton_annuler = CTRL_Bouton_image.CTRL(self, texte=_(u"Fermer"), cheminImage="Images/32x32/Fermer.png")

        self.__set_properties()
        self.__do_layout()
        
        self.Bind(wx.EVT_CLOSE, self.OnBoutonAnnuler)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAide, self.bouton_aide)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonOk, self.bouton_ok)
        self.Bind(wx.EVT_BUTTON, self.OnBoutonAnnuler, self.bouton_annuler)
        
        # Init Contr�les
        self.ctrl_liste_inscriptions.MAJ()
                

    def __set_properties(self):
        self.bouton_aide.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour obtenir de l'aide")))
        self.bouton_ok.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour transf�rer les inscriptions vers l'�diteur d'Emails")))
        self.bouton_annuler.SetToolTip(wx.ToolTip(_(u"Cliquez ici pour annuler")))
        self.SetMinSize((850, 700))

    def __do_layout(self):
        grid_sizer_base = wx.FlexGridSizer(rows=4, cols=1, vgap=10, hgap=10)
        grid_sizer_base.Add(self.ctrl_bandeau, 0, wx.EXPAND, 0)
                
        # Factures
        box_inscriptions = wx.StaticBoxSizer(self.box_inscriptions_staticbox, wx.VERTICAL)
        box_inscriptions.Add(self.ctrl_liste_inscriptions, 1, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_inscriptions, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)

        # Options
        box_options = wx.StaticBoxSizer(self.box_options_staticbox, wx.VERTICAL)
        box_options.Add(self.ctrl_options, 0, wx.ALL|wx.EXPAND, 10)
        grid_sizer_base.Add(box_options, 1, wx.LEFT|wx.RIGHT|wx.EXPAND, 10)
        
        # Boutons
        grid_sizer_boutons = wx.FlexGridSizer(rows=1, cols=4, vgap=10, hgap=10)
        grid_sizer_boutons.Add(self.bouton_aide, 0, 0, 0)
        grid_sizer_boutons.Add((20, 20), 0, wx.EXPAND, 0)
        grid_sizer_boutons.Add(self.bouton_ok, 0, 0, 0)
        grid_sizer_boutons.Add(self.bouton_annuler, 0, 0, 0)
        grid_sizer_boutons.AddGrowableCol(1)
        grid_sizer_base.Add(grid_sizer_boutons, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 10)
        
        self.SetSizer(grid_sizer_base)
        grid_sizer_base.Fit(self)
        grid_sizer_base.AddGrowableRow(1)
        grid_sizer_base.AddGrowableCol(0)
        self.Layout()
        self.CenterOnScreen() 

    def OnBoutonAide(self, event): 
        from Utils import UTILS_Aide
        UTILS_Aide.Aide("")

    def OnBoutonAnnuler(self, event): 
        self.ctrl_options.MemoriserParametres() 
        self.EndModal(wx.ID_CANCEL)

    def OnBoutonOk(self, event): 
        """ Aper�u PDF des inscriptions """
        # Validation des donn�es saisies
        tracks = self.ctrl_liste_inscriptions.GetTracksCoches()
        if len(tracks) == 0 : 
            dlg = wx.MessageDialog(self, _(u"Vous n'avez s�lectionn� aucune inscription � envoyer par Email !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            return

        # Cr�ation des inscriptions s�lectionn�es
        listeIDinscription = []
        for track in tracks :
            listeIDinscription.append(track.IDinscription)
        inscription = UTILS_Inscriptions.Inscription()
        dictOptions = self.ctrl_options.GetOptions()
        if dictOptions == False :
            return

        resultat = inscription.Impression(listeInscriptions=listeIDinscription, nomDoc=None, afficherDoc=False, dictOptions=dictOptions, repertoire=dictOptions["repertoire"], repertoireTemp=True)
        if resultat == False : 
            return
        dictChampsFusion, dictPieces = resultat
        
        def SupprimerFichiersTemp():
            for IDinscription, fichier in dictPieces.iteritems() :
                os.remove(fichier)  

        # R�cup�ration de toutes les adresses Emails
        DB = GestionDB.DB()
        req = """SELECT IDindividu, mail, travail_mail
        FROM individus;"""
        DB.ExecuterReq(req)
        listeAdressesIndividus = DB.ResultatReq()
        DB.Close() 
        dictAdressesIndividus = {}
        for IDindividu, mail, travail_mail in listeAdressesIndividus :
            dictAdressesIndividus[IDindividu] = {"perso" : mail, "travail" : travail_mail}
                
        # R�cup�ration des donn�es adresse + champs + pi�ces
        listeDonnees = []
        listeAnomalies = []
        listeEnvoiNonDemande = []
        for track in tracks :
            adresse = UTILS_Envoi_email.GetAdresseFamille(track.IDfamille, choixMultiple=False, muet=True, nomTitulaires=track.nomTitulaires)
            
            # M�morisation des donn�es
            if adresse not in (None, "", []) : 
                if dictPieces.has_key(track.IDinscription) :
                    fichier = dictPieces[track.IDinscription]
                    champs = dictChampsFusion[track.IDinscription]
                    listeDonnees.append({"adresse" : adresse, "pieces" : [fichier,], "champs" : champs})
            else :
                listeAnomalies.append(track.nomTitulaires)
        
        # Annonce les anomalies trouv�es
        if len(listeAnomalies) > 0 :
            texte = _(u"%d des familles s�lectionn�es n'ont pas d'adresse Email.\n\n") % len(listeAnomalies)
            texte += _(u"Souhaitez-vous quand m�me continuer avec les %d autres familles ?") % len(listeDonnees)
            dlg = wx.MessageDialog(self, texte, _(u"Avertissement"), wx.YES_NO|wx.NO_DEFAULT|wx.CANCEL|wx.ICON_EXCLAMATION)
            reponse = dlg.ShowModal() 
            dlg.Destroy()
            if reponse != wx.ID_YES :
                SupprimerFichiersTemp()
                return        
        
        # Derni�re v�rification avant transfert
        if len(listeDonnees) == 0 : 
            dlg = wx.MessageDialog(self, _(u"Il ne reste finalement aucune inscription � envoyer par Email !"), _(u"Erreur"), wx.OK | wx.ICON_EXCLAMATION)
            dlg.ShowModal()
            dlg.Destroy()
            SupprimerFichiersTemp()
            return

        # Transfert des donn�es vers DLG Mailer
        import DLG_Mailer
        dlg = DLG_Mailer.Dialog(self, categorie="inscription")
        dlg.SetDonnees(listeDonnees, modificationAutorisee=False)
        dlg.ChargerModeleDefaut()
        dlg.ShowModal() 
        dlg.Destroy()

        # Suppression des PDF temporaires
        SupprimerFichiersTemp()




if __name__ == u"__main__":
    app = wx.App(0)
    #wx.InitAllImageHandlers()
    dlg = Dialog(None)
    app.SetTopWindow(dlg)
    dlg.ShowModal()
    app.MainLoop()
