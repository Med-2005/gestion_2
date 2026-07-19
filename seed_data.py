from sqlalchemy.orm import Session
import models

CATEGORIES = [
    {"nom": "🥗 Entrée", "description": "Nos meilleures entrées.", "photo": "https://picsum.photos/seed/entree/600/400"},
    {"nom": "🍛 Plat principal", "description": "Plats chauds et copieux.", "photo": "https://picsum.photos/seed/plat/600/400"},
    {"nom": "🍰 Dessert", "description": "Douceurs sucrées.", "photo": "https://picsum.photos/seed/dessert/600/400"},
    {"nom": "🍹 Boisson", "description": "Boissons fraîches et chaudes.", "photo": "https://picsum.photos/seed/boisson/600/400"}
]

PRODUITS = [
    # تأكد أن اسم الفئة هنا يطابق تماماً الأسماء أعلاه
    {"libelle": "Salade verte", "prix": 5.00, "categorie": "🥗 Entrée", "description": "Salade fraîche.", "photo": "https://picsum.photos/seed/salade/500/500"},
    {"libelle": "Burger maison", "prix": 12.00, "categorie": "🍛 Plat principal", "description": "Viande fraîche.", "photo": "https://picsum.photos/seed/burger/500/500"},
    {"libelle": "Tarte au citron", "prix": 6.50, "categorie": "🍰 Dessert", "description": "Pâte sablée.", "photo": "https://picsum.photos/seed/tarte/500/500"},
    {"libelle": "Jus d'orange", "prix": 4.00, "categorie": "🍹 Boisson", "description": "Fraîchement pressé.", "photo": "https://picsum.photos/seed/jus/500/500"}
]

def seed_database(db: Session) -> None:
    # التحقق مما إذا كانت قاعدة البيانات فارغة لتجنب التكرار
    if db.query(models.Categorie).count() > 0:
        return
    
    nom_to_categorie = {}
    
    # إضافة الفئات
    for cat_data in CATEGORIES:
        categorie = models.Categorie(**cat_data)
        db.add(categorie)
        db.flush()
        # تخزين الفئة لربطها بالمنتجات لاحقاً
        nom_to_categorie[cat_data["nom"]] = categorie
        
    # إضافة المنتجات
    for prod_data in PRODUITS:
        categorie = nom_to_categorie[prod_data["categorie"]]
        db.add(models.Produit(
            libelle=prod_data["libelle"],
            prix=prod_data["prix"],
            description=prod_data["description"],
            photo=prod_data["photo"],
            id_categorie=categorie.id_categorie,
        ))
    db.commit()