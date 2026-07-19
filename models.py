"""
models.py
---------
Modèles SQLAlchemy correspondant strictement au Modèle Logique de Données (MLD).
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Client(Base):
    __tablename__ = "client"
    id_client = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    tel = Column(String(20), nullable=True)
    email = Column(String(150), nullable=True, unique=True, index=True)
    mot_de_passe = Column(String(255), nullable=True)

    # Un client peut passer plusieurs commandes
    commandes = relationship(
        "Commande", back_populates="client", cascade="all, delete-orphan"
    )

class Categorie(Base):
    __tablename__ = "categorie"
    id_categorie = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nom = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    photo = Column(String(500), nullable=True)

    # Une catégorie regroupe plusieurs produits
    produits = relationship(
        "Produit", back_populates="categorie", cascade="all, delete-orphan"
    )

class Produit(Base):
    __tablename__ = "produit"
    id_produit = Column(Integer, primary_key=True, index=True, autoincrement=True)
    libelle = Column(String(150), nullable=False)
    prix = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    photo = Column(String(500), nullable=True)
    id_categorie = Column(Integer, ForeignKey("categorie.id_categorie"), nullable=False)

    categorie = relationship("Categorie", back_populates="produits")
    # Un produit peut apparaître dans plusieurs lignes de commande
    lignes_commande = relationship("LigneCommande", back_populates="produit")

class Commande(Base):
    __tablename__ = "commande"
    id_commande = Column(Integer, primary_key=True, index=True, autoincrement=True)
    statut = Column(String(30), nullable=False, default="En attente")
    numero_cmd = Column(String(50), unique=True, nullable=False)
    date_cmd = Column(DateTime, default=datetime.utcnow, nullable=False)
    num_ticket = Column(String(50), unique=True, nullable=False)
    mode_paiement = Column(String(30), nullable=False)
    id_client = Column(Integer, ForeignKey("client.id_client"), nullable=False)

    client = relationship("Client", back_populates="commandes")
    # Une commande contient plusieurs lignes (association vers PRODUIT)
    lignes = relationship(
        "LigneCommande", back_populates="commande", cascade="all, delete-orphan"
    )

    @property
    def total(self) -> float:
        """Montant total de la commande, calculé à partir des lignes."""
        return round(sum(l.quantite_cmd * l.produit.prix for l in self.lignes), 2)

class LigneCommande(Base):
    """
    Table d'association COMMANDE <-> PRODUIT.
    Clé primaire composite (id_commande, id_produit) + attribut quantite_cmd.
    """
    __tablename__ = "ligne_commande"
    id_commande = Column(Integer, ForeignKey("commande.id_commande"), primary_key=True)
    id_produit = Column(Integer, ForeignKey("produit.id_produit"), primary_key=True)
    quantite_cmd = Column(Integer, nullable=False, default=1)

    commande = relationship("Commande", back_populates="lignes")
    produit = relationship("Produit", back_populates="lignes_commande")