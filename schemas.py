"""
schemas.py
----------
Schémas Pydantic utilisés pour valider les requêtes entrantes et sérialiser
les réponses de l'API. Séparés des modèles SQLAlchemy (models.py).
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# CATEGORIE
# ---------------------------------------------------------------------------
class CategorieOut(BaseModel):
    id_categorie: int
    nom: str
    description: Optional[str] = None
    photo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# PRODUIT
# ---------------------------------------------------------------------------
class ProduitOut(BaseModel):
    id_produit: int
    libelle: str
    prix: float
    description: Optional[str] = None
    photo: Optional[str] = None
    id_categorie: int
    categorie: Optional[CategorieOut] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# CLIENT
# ---------------------------------------------------------------------------
# UPDATE THIS SCHEMA:
class ClientCreate(BaseModel):
    nom: str
    prenom: str
    tel: Optional[str] = None
    email: str # Made email required for login
    mot_de_passe: str

# ADD THIS NEW SCHEMA:
class ClientLogin(BaseModel):
    email: str
    mot_de_passe: str

class ClientOut(BaseModel):
    id_client: int
    nom: str
    prenom: str
    tel: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# LIGNE_COMMANDE
# ---------------------------------------------------------------------------
class LigneCommandeCreate(BaseModel):
    id_produit: int
    quantite_cmd: int = Field(gt=0, description="Doit être strictement positif")


class LigneCommandeOut(BaseModel):
    id_produit: int
    quantite_cmd: int
    produit: ProduitOut

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# COMMANDE
# ---------------------------------------------------------------------------
class CommandeCreate(BaseModel):
    # Le client peut être identifié par son id existant...
    id_client: Optional[int] = None
    # ...ou créé à la volée à partir de ses informations
    client: Optional[ClientCreate] = None
    mode_paiement: str
    lignes: List[LigneCommandeCreate]


class CommandeOut(BaseModel):
    id_commande: int
    statut: str
    numero_cmd: str
    date_cmd: datetime
    num_ticket: str
    mode_paiement: str
    id_client: int
    client: ClientOut
    lignes: List[LigneCommandeOut]
    total: float

    model_config = ConfigDict(from_attributes=True)

class ProduitCreate(BaseModel):
    libelle: str
    prix: float
    description: Optional[str] = None
    photo: Optional[str] = None
    id_categorie: int

# Ajoutez ceci juste en dessous de ProduitCreate
class ProduitUpdate(BaseModel):
    libelle: Optional[str] = None
    prix: Optional[float] = None
    description: Optional[str] = None
    photo: Optional[str] = None
    id_categorie: Optional[int] = None