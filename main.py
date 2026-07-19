"""
main.py
-------
Application FastAPI : sert le frontend et expose l'API REST de la boutique
« Le Comptoir » (produits, catégories, clients, commandes).
"""
from fastapi.security import OAuth2PasswordBearer
import random
import jwt
import bcrypt
from fastapi.responses import HTMLResponse
import string
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

import models
import schemas
from database import Base, engine, SessionLocal, get_db
from seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crée les tables si elles n'existent pas, puis peuple la base si besoin
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Le Comptoir — API Boutique", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# SECURITY CONFIGURATION
SECRET_KEY = "mon_code_secret_tres_securise" # In production, keep this hidden!
ALGORITHM = "HS256"

def verify_password(plain_password, hashed_password):
    # نستخدم bcrypt مباشرة للتحقق
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    # نستخدم bcrypt مباشرة للتشفير
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """تتأكد من أن المستخدم الحالي هو المدير فقط"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id = payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Non autorisé")
    
    client = db.query(models.Client).filter(models.Client.id_client == client_id).first()
    
    # نتحقق أن البريد هو بريد المدير
    if not client or client.email != "admin@test.com":
        raise HTTPException(status_code=403, detail="Accès refusé (Admin uniquement)")
    return client

# ---------------------------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------------------------
@app.get("/")
def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# ---------------------------------------------------------------------------
# CATEGORIES
# ---------------------------------------------------------------------------
@app.get("/api/categories", response_model=List[schemas.CategorieOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Categorie).order_by(models.Categorie.nom).all()


# ---------------------------------------------------------------------------
# PRODUITS
# ---------------------------------------------------------------------------
@app.get("/api/produits", response_model=List[schemas.ProduitOut])
def get_produits(
    id_categorie: Optional[int] = Query(None, description="Filtrer par catégorie"),
    db: Session = Depends(get_db),
):
    """Retourne tous les produits, avec le détail de leur catégorie."""
    query = db.query(models.Produit).options(joinedload(models.Produit.categorie))
    if id_categorie is not None:
        query = query.filter(models.Produit.id_categorie == id_categorie)
    return query.order_by(models.Produit.libelle).all()


@app.get("/api/produits/{id_produit}", response_model=schemas.ProduitOut)
def get_produit(id_produit: int, db: Session = Depends(get_db)):
    produit = (
        db.query(models.Produit)
        .options(joinedload(models.Produit.categorie))
        .filter(models.Produit.id_produit == id_produit)
        .first()
    )
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable.")
    return produit


@app.get("/admin", response_class=HTMLResponse)
def serve_admin(request: Request):
    """سيرفر واجهة لوحة التحكم للمدير"""
    return templates.TemplateResponse(request=request, name="admin.html")

@app.post("/api/produits", response_model=schemas.ProduitOut)
def create_produit(produit: schemas.ProduitCreate, admin: models.Client = Depends(get_current_admin), db: Session = Depends(get_db)):
    """إضافة منتج (للمدير فقط)"""
    db_produit = models.Produit(**produit.model_dump())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

@app.delete("/api/produits/{id_produit}")
def delete_produit(id_produit: int, admin: models.Client = Depends(get_current_admin), db: Session = Depends(get_db)):
    """حذف منتج (للمدير فقط)"""
    produit = db.query(models.Produit).filter(models.Produit.id_produit == id_produit).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    db.delete(produit)
    db.commit()
    return {"detail": "Produit supprimé"}
@app.put("/api/produits/{id_produit}", response_model=schemas.ProduitOut)
def update_produit(id_produit: int, produit_update: schemas.ProduitUpdate, admin: models.Client = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Modifier un produit (Admin uniquement)"""
    db_produit = db.query(models.Produit).filter(models.Produit.id_produit == id_produit).first()
    if not db_produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    
    # Mettre à jour uniquement les champs fournis
    update_data = produit_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_produit, key, value)
        
    db.commit()
    db.refresh(db_produit)
    return db_produit
# ---------------------------------------------------------------------------
# CLIENTS
# ---------------------------------------------------------------------------
@app.get("/login", response_class=HTMLResponse)
def serve_login(request: Request):
    """Sert la page HTML de connexion."""
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/api/clients", response_model=schemas.ClientOut, status_code=201)
def create_client(payload: schemas.ClientCreate, db: Session = Depends(get_db)):
    """Crée un compte avec un mot de passe sécurisé."""
    # Check if email already exists
    existing_client = db.query(models.Client).filter(models.Client.email == payload.email).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")
    
    # Hash password and save
    client_data = payload.model_dump()
    client_data["mot_de_passe"] = get_password_hash(client_data.pop("mot_de_passe"))
    
    client = models.Client(**client_data)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client

@app.post("/api/login")
def login(payload: schemas.ClientLogin, db: Session = Depends(get_db)):
    """Vérifie les identifiants et retourne un token."""
    client = db.query(models.Client).filter(models.Client.email == payload.email).first()
    if not client or not client.mot_de_passe:
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    
    if not verify_password(payload.mot_de_passe, client.mot_de_passe):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect.")
    
    # Generate Token
    token_data = {"sub": str(client.id_client), "name": client.prenom}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    return {
            "access_token": token, 
            "token_type": "bearer", 
            "client": {
                "id_client": client.id_client, 
                "prenom": client.prenom,
                "email": client.email  # <--- هذا هو السطر الناقص!
            }
    }            
# ---------------------------------------------------------------------------
# COMMANDES
# ---------------------------------------------------------------------------
def _generate_numero_cmd(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.query(models.Commande).count() + 1
    return f"CMD-{today}-{count:04d}"


def _generate_num_ticket() -> str:
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"TCK-{suffix}"


@app.post("/api/commandes", response_model=schemas.CommandeOut, status_code=201)
def create_commande(payload: schemas.CommandeCreate, db: Session = Depends(get_db)):
    """
    Crée une COMMANDE et ses LIGNE_COMMANDE associées.
    Le client peut être identifié par id_client (existant) ou créé à la volée
    à partir des champs `client`.
    """
    if not payload.lignes:
        raise HTTPException(
            status_code=400, detail="La commande doit contenir au moins un produit."
        )

    # --- Résolution du client --------------------------------------------
    client = None
    if payload.id_client is not None:
        client = db.query(models.Client).filter(
            models.Client.id_client == payload.id_client
        ).first()
        if not client:
            raise HTTPException(
                status_code=404, detail="Aucun client ne correspond à cet identifiant."
            )
    elif payload.client is not None:
        # Réutilise un client existant si l'email correspond déjà, sinon le crée
        if payload.client.email:
            client = db.query(models.Client).filter(
                models.Client.email == payload.client.email
            ).first()
        if not client:
            client = models.Client(**payload.client.model_dump())
            db.add(client)
            db.flush()  # obtient id_client sans committer
    else:
        raise HTTPException(
            status_code=400,
            detail="Fournir soit id_client, soit les informations du client.",
        )

    # --- Vérification des produits commandés ------------------------------
    lignes_a_creer = []
    for ligne in payload.lignes:
        produit = db.query(models.Produit).filter(
            models.Produit.id_produit == ligne.id_produit
        ).first()
        if not produit:
            raise HTTPException(
                status_code=404, detail=f"Produit id={ligne.id_produit} introuvable."
            )
        lignes_a_creer.append((produit, ligne.quantite_cmd))

    # --- Création de la commande -------------------------------------------
    commande = models.Commande(
        statut="En attente",
        numero_cmd=_generate_numero_cmd(db),
        date_cmd=datetime.utcnow(),
        num_ticket=_generate_num_ticket(),
        mode_paiement=payload.mode_paiement,
        client=client,
    )
    db.add(commande)
    db.flush()  # obtient id_commande

    for produit, quantite in lignes_a_creer:
        db.add(models.LigneCommande(
            id_commande=commande.id_commande,
            id_produit=produit.id_produit,
            quantite_cmd=quantite,
        ))

    db.commit()
    db.refresh(commande)
    return commande


@app.get("/api/commandes/{id_commande}", response_model=schemas.CommandeOut)
def get_commande(id_commande: int, db: Session = Depends(get_db)):
    commande = (
        db.query(models.Commande)
        .options(
            joinedload(models.Commande.client),
            joinedload(models.Commande.lignes)
            .joinedload(models.LigneCommande.produit)
            .joinedload(models.Produit.categorie),
        )
        .filter(models.Commande.id_commande == id_commande)
        .first()
    )
    if not commande:
        raise HTTPException(status_code=404, detail="Commande introuvable.")
    return commande


# أضف هذه الأسطر في ملف main.py تحت قسم # PRODUITS

@app.post("/api/produits", response_model=schemas.ProduitOut)
def create_produit(produit: schemas.ProduitCreate, db: Session = Depends(get_db)):
    """إضافة منتج جديد"""
    db_produit = models.Produit(**produit.model_dump())
    db.add(db_produit)
    db.commit()
    db.refresh(db_produit)
    return db_produit

@app.delete("/api/produits/{id_produit}")
def delete_produit(id_produit: int, db: Session = Depends(get_db)):
    """حذف منتج موجود"""
    produit = db.query(models.Produit).filter(models.Produit.id_produit == id_produit).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    db.delete(produit)
    db.commit()
    return {"message": "Produit supprimé"}