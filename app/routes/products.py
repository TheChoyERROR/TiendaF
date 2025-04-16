from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.database import get_db
from app.models.models import Product, Category, User, GenderType
from app.schemas.schemas import ProductCreate, Product as ProductSchema, ProductUpdate
from app.utils.auth import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={404: {"description": "No encontrado"}}
)

@router.get("/", response_model=List[ProductSchema])
def get_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    gender: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Consulta base
    query = db.query(Product).filter(Product.is_active == True)
    
    # Aplicar filtros si se proporcionan
    if category_id:
        query = query.join(Product.categories).filter(Category.id == category_id)
    
    if gender:
        try:
            gender_enum = GenderType(gender)
            query = query.filter(Product.gender == gender_enum)
        except ValueError:
            pass  # Ignorar valores de género inválidos
    
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    # Aplicar paginación
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None or not db_product.is_active:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return db_product

@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    # Verificar que las categorías existan
    categories = []
    for category_id in product.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail=f"Categoría con ID {category_id} no encontrada")
        categories.append(category)
    
    # Verificar si hay un SKU y es único
    if product.sku:
        existing_product = db.query(Product).filter(Product.sku == product.sku).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese SKU")
    
    # Crear producto (excluyendo category_ids)
    product_data = product.dict(exclude={"category_ids"})
    db_product = Product(**product_data)
    
    # Asignar categorías
    db_product.categories = categories
    
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Verificar si el SKU es único en caso de cambio
    if product.sku and product.sku != db_product.sku:
        existing_product = db.query(Product).filter(Product.sku == product.sku).first()
        if existing_product:
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese SKU")
    
    # Actualizar categorías si se proporcionan
    if product.category_ids:
        categories = []
        for category_id in product.category_ids:
            category = db.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise HTTPException(status_code=404, detail=f"Categoría con ID {category_id} no encontrada")
            categories.append(category)
        db_product.categories = categories
    
    # Actualizar resto de campos si están presentes
    update_data = product.dict(exclude={"category_ids"}, exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Enfoque de eliminación lógica (soft delete)
    db_product.is_active = False
    db.commit()
    return None