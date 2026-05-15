
from joueur import Joueur
from plateau import Plateau
from ressource import Ressource
from couleur import Couleur
from pion import Pion
from pileChance import PileChance
from des import Des 
from carteBonusConstructeur import CarteBonusConstructeur
from casePropriete import CasePropriete
import random
from os import system 
import pygame as pg
from fenetre import Fenetre
from fenetreCreationJoueurs import FenetreCreationJoueurs
from popup import Popup 
from ecranFin import EcranFin
from database import Database
class Jeu:
    #QUI   : Théo Verhaeghe et Victor Van Goethem
    #QUOI  : Le jeu
    #QUAND : 10/12/25
    def __init__(self):
        self.__joueurs:list = []
        # QUOI : joueurs qui vont jouer durant le jeu
        self.__pions:list = []
        # QUOI : pions qui vont être utilisés durant le jeu
        self.__plateau:Plateau = None
        # QUOI : Le plateau de jeu
        self.__couleurs:list = []
        # QUOI : liste de toutes lescouleurs du jeu
        self.__pileChance:PileChance = None
        # QUOI : pile de cartes chances du jeu

    #GETTERSx
    @property
    def joueurs(self):
        return self.__joueurs
    
    @property
    def pions(self):
        return self.__pions
    
    @property
    def pileChance(self):
        return self.__pileChance
    
    @property
    def plateau(self):
        return self.__plateau

    @property
    def ressource(self):
        return self.__ressource

    @property
    def ressources(self):
        return self.__ressources

    @property
    def couleurs(self):
        return self.__couleurs
     
    #SETTERS
    @joueurs.setter
    def joueurs(self, para_joueurs):
        if not isinstance(para_joueurs, list):
            raise TypeError("Classe : Jeu | Métode: joueurs.setter | paramètre : para_joueur | Type attendu : liste")
        
        self.__joueurs = para_joueurs

    @pions.setter
    def pions(self, para_pions):
        if not isinstance(para_pions, list):
            raise TypeError("Classe : Jeu | Métode: pions.setter | paramètre : para_pions | Type attendu : liste")
        
        self.__joueurs = para_pions

    @pileChance.setter
    def pileChance(self, para_pileChance):
        if not isinstance(para_pileChance, PileChance):
            raise TypeError("Classe : Jeu | Métode: pileChance.setter | paramètre : para_pileChance | Type attendu : PileChance")
        
        self.__pileChance = para_pileChance

    @plateau.setter
    def plateau(self, para_plateau):
        if not isinstance(para_plateau, Plateau):
            raise TypeError("Classe : Jeu | Métode: plateau.setter | paramètre : para_plateau | Type attendu : Plateau")
        
        self.__plateau = para_plateau

    @ressource.setter
    def ressource(self, para_ressource):
        if not isinstance(para_ressource, Ressource):
            raise TypeError("Classe : Jeu | Métode: ressource.setter | paramètre : para_ressource | Type attendu : Ressource")
        
        self.__ressource = para_ressource

    @ressources.setter
    def ressources(self, para_ressources):
        if not isinstance(para_ressources, list):
            raise TypeError("Classe : Jeu | Métode: ressources.setter | paramètre : para_ressources | Type attendu : list")
        
        self.__ressources = para_ressources

    @couleurs.setter
    def couleurs(self, para_couleurs):
        if not isinstance(para_couleurs, list):
            raise TypeError("Classe : Jeu | Métode: couleurs.setter | paramètre : para_couleurs | Type attendu : list")
        
        self.__couleurs = para_couleurs

    def creerPlateau(self):
        self.__plateau = Plateau()
        self.__plateau.creerChemin(self.pileChance,self.joueurs)
        self.__plateau.creerVille() 

    def creerPions(self)->None:
        for i in range(4):
            self.pions.append(Pion())

    def creerPileChance(self)->None:
        self.pileChance = PileChance() 
        self.pileChance.remplirPile()
                        

    def creerJoueurs(self) -> None:
        f = FenetreCreationJoueurs()
        lcl_pseudos = f.creerJoueurs()
        for pseudo in lcl_pseudos:
            self.joueurs.append(Joueur(pseudo,1000,Pion(),None))
        self.determinerRessources()
        f.actualiserFenetreRessources(self.joueurs)

    def determinerRessources(self):
        lcl_ressources:list = ["camion-benne","bateau","excavatrice","grue"]
        lcl_images:list = ["pion_rouge","pion_jaune", "pion_vert", "pion_mauve"]
        for j in self.joueurs:
            lcl_ressource_random = random.choice(lcl_ressources)
            j.ressource = Ressource(lcl_ressource_random)
            lcl_index = lcl_ressources.index(lcl_ressource_random)
            lcl_ressources.remove(lcl_ressource_random)
            j.pion.pathImage = f"{lcl_images[lcl_index]}.png"
            lcl_images.remove(lcl_images[lcl_index])
            j.pion.associerImage()

    def conditionsDeFinDePartie(self)->bool:
        lcl_nbr_joueurs_restants:int = 0
        for j in self.joueurs:
            if not(j.estElimine):
                lcl_nbr_joueurs_restants += 1
        if lcl_nbr_joueurs_restants <= 1:
            return True 
        
        if self.plateau.ville.penthouseEstConstruit:
            return True 
        
    def determinerGagnant(self):
        carteBonus:CarteBonusConstructeur = CarteBonusConstructeur(5,5)
        joueurGagnant:Joueur = self.joueurs[0]

        self.plateau.ville.calculerPointsVilles()
        self.plateau.chemin.calculerPointsFamilles()
        carteBonus.bonusConstruction(self.joueurs, self.plateau.ville)
        carteBonus.bonusRichesse(self.joueurs)

        for i in self.joueurs:
            if i.point > joueurGagnant.point:
                joueurGagnant = i
        lcl_joueurs_gagnants = [joueurGagnant]
        for i in self.joueurs:
            if i.point == joueurGagnant.point:
                lcl_joueurs_gagnants.append(i)
        if len(lcl_joueurs_gagnants) > 1:
            lcl_capitals = []
            for i in lcl_joueurs_gagnants:
                lcl_capitals.append(self.calculerHypotheque(i) + i.argent)
                        
            joueurGagnant = lcl_joueurs_gagnants[0]            
            for i in range(len(lcl_joueurs_gagnants)):
                if lcl_capitals[i] > lcl_capitals[lcl_joueurs_gagnants.index(joueurGagnant)]:
                    joueurGagnant = lcl_joueurs_gagnants[i]

            print(f"La partie est finie, {joueurGagnant.pseudo} remporte la partie !")
            ecran_fin = EcranFin(joueurGagnant)
            ecran_fin.afficher()

                        
        else:
            print(f"La partie est finie, {joueurGagnant.pseudo} remporte la partie !")
            ecran_fin = EcranFin(joueurGagnant)
            ecran_fin.afficher()

    def calculerHypotheque(self,joueur)->int:
        lcl_valeur:int = 0
        for lcl_case in self.plateau.chemin.cases:
            if isinstance(lcl_case,CasePropriete):
                if lcl_case.proprietaire == joueur:
                    lcl_valeur += lcl_case.prix
        return lcl_valeur

    def jouerTourDeJeu(self,fenetre:Fenetre,popup:Popup):
        lcl_des = Des()
        for joueur in self.joueurs:
            system("cls")
            if not(joueur.estElimine):
                lcl_events = pg.event.get()
                fenetre.actualiser(joueur,lcl_events)
                lcl_aLanceDes = False 
                pg.display.flip()
                
                lcl_resultat_des = popup.popupLancerDes(joueur,lcl_des)
                fenetre.dernierResultatDes = lcl_resultat_des
                self.plateau.chemin.revenusProprietes(lcl_resultat_des)
                joueur.ressourceRevenus(self.joueurs,lcl_resultat_des,popup)
                fenetre.etapeActuelle = "Effet de la case"
                joueur.deplacerPion(self.plateau.chemin,lcl_resultat_des,popup)

                fenetre.etapeActuelle = "Actions libres"    
                joueur.echangerRessource(self.joueurs,popup)
                joueur.echangerAvecLaBanque(popup)
                joueur.construire(self.plateau,popup)


    def jouerPartie(self):
        lcl_jeu_continue:bool = True
        self.creerJoueurs()
        self.creerPileChance()
        self.creerPlateau()
        lcl_fenetre = Fenetre(810,870,self.plateau,self.joueurs)
        lcl_popup = Popup(lcl_fenetre,self.sauvegarder)
        
        # self.joueurs[0].ajouterRessource("camion-benne",8)
        # self.joueurs[1].ajouterRessource("grue",8)
        while lcl_jeu_continue:
            self.jouerTourDeJeu(lcl_fenetre,lcl_popup)
            if self.conditionsDeFinDePartie():
                lcl_jeu_continue = False

        self.determinerGagnant()

    def sauvegarder(self):
        print("Partie sauvegardée !")
        for j in self.joueurs:
            print(f"{j.pseudo} : {j.argent}€")

        db = Database()
        lcl_stmt = db.db.cursor()

        lcl_stmt.execute(f"SELECT * FROM jeu;")
        lcl_resultatJeux:list = lcl_stmt.fetchall()
        lcl_nouvelID:int = lcl_resultatJeux[-1][0] + 1
        lcl_stmt.execute(f"INSERT INTO jeu(ID_jeu) VALUES({lcl_nouvelID});")
        lcl_stmt.execute(f"INSERT INTO plateau(ID_plateau,ID_jeu) VALUES({lcl_nouvelID},{lcl_nouvelID});")
        lcl_stmt.execute(f"INSERT INTO chemin(ID_chemin,ID_plateau) VALUES({lcl_nouvelID},{lcl_nouvelID});")
        lcl_stmt.execute(f"INSERT INTO ville(ID_ville,ID_plateau) VALUES({lcl_nouvelID},{lcl_nouvelID});") 

        ##Sauvegarde des joueurs
        for j in self.joueurs:
            lcl_stmt.execute(f"INSERT INTO joueurs(pseudo,ressource,argent,camion_benne,bateau,excavatrice,grue,estEnPrison,estElimine,positionPion,ID_jeu) VALUES('{j.pseudo}','{j.ressource.nom}',{j.argent},{j.compterRessource('camion-benne')},{j.compterRessource('bateau')},{j.compterRessource('excavatrice')},{j.compterRessource('grue')},{j.estEnPrison},{j.estElimine},{j.pion.position},{lcl_nouvelID});")

        ##Sauvegarde des terrains
        lcl_stmt.execute(f"SELECT * FROM joueurs WHERE ID_jeu = {lcl_nouvelID};")
        lcl_resultatJoueurs = lcl_stmt.fetchall()
        for y in range(len(self.plateau.ville.terrains)):
            for x in range(len(self.plateau.ville.terrains[0])):
                lcl_terrain = self.plateau.ville.terrains[y][x]
                if lcl_terrain.proprietaire != None:
                    lcl_IDJoueur = lcl_resultatJoueurs[0][0] + self.joueurs.index(lcl_terrain.proprietaire)
                    lcl_stmt.execute(f"INSERT INTO terrain(etages,positionX,positionY,ID_joueur,ID_ville) VALUES({lcl_terrain.etages},{x},{y},{lcl_IDJoueur},{lcl_nouvelID});")
                else:
                    lcl_stmt.execute(f"INSERT INTO terrain(etages,positionX,positionY,ID_joueur,ID_ville) VALUES({lcl_terrain.etages},{x},{y},NULL,{lcl_nouvelID});")

        ##Sauvegarde des cases

        #Cases propriété
        lcl_proprietes:list = []
        for case in self.plateau.chemin.cases:
            if isinstance(case,CasePropriete):
                lcl_proprietes.append(case)

        for propriete in lcl_proprietes:
            lcl_indexPropriete = self.plateau.chemin.cases.index(propriete)
            if propriete.proprietaire != None:
                lcl_IDJoueur = lcl_resultatJoueurs[0][0] + self.joueurs.index(propriete.proprietaire)
                #VIC : METTRE GUILLEMETS SIMPLES AUTOUR DE STR PARA
                lcl_stmt.execute(f"INSERT INTO casepropriete(prix,loyer,loyerAvecCouleur,numeroActivation,typeRessource,nom,`index`,ID_chemin,ID_joueur,couleur) VALUES({propriete.prix},{propriete.loyer},{propriete.loyerAvecCouleur},{propriete.numeroActivation},{propriete.typeRessource.nom},{propriete.nom},{lcl_indexPropriete},{lcl_nouvelID},{lcl_IDJoueur},{propriete.couleur.nom});")
            else:
                lcl_stmt.execute(f"INSERT INTO casepropriete(prix,loyer,loyerAvecCouleur,numeroActivation,typeRessource,nom,`index`,ID_chemin,ID_joueur,couleur) VALUES({propriete.prix},{propriete.loyer},{propriete.loyerAvecCouleur},{propriete.numeroActivation},{propriete.typeRessource.nom},{propriete.nom},{lcl_indexPropriete},{lcl_nouvelID},NULL,{propriete.couleur.nom});")
        
                    
        db.db.commit()

if __name__ == "__main__":
    system("cls")
    nvJeu = Jeu()
    nvJeu.jouerPartie()