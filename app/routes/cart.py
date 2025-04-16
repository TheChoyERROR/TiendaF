from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.models import Cart, CartItem, Product, User
from app.schemas.schemas import CartItem as CartItemSchema, CartItemCreate, CartItemUpdate, Cart as CartSchema
from app.utils.auth import get_current_active_user

router = APIRouter(
    prefix="/cart",
    tags=["cart"],
    responses={404: {"description": "No encontrado"}}
)

@router.get("/", response_model=CartSchema)
def get_user_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        # Si el usuario no tiene carrito, crear uno nuevo
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

@router.post("/items", response_model=CartItemSchema, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(item: CartItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Obtener o crear el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    
    # Verificar que el producto existe y está activo
    product = db.query(Product).filter(Product.id == item.product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado o no disponible")
    
    # Verificar stock suficiente
    if product.stock < item.quantity:
        raise HTTPException(status_code=400, detail="Stock insuficiente")
    
    # Verificar si el producto ya está en el carrito
    cart_item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == item.product_id).first()
    if cart_item:
        # Actualizar cantidad si ya existe
        cart_item.quantity += item.quantity
        db.commit()
        db.refresh(cart_item)
        return cart_item
    
    # Crear nuevo item en el carrito
    new_item = CartItem(
        cart_id=cart.id,
        product_id=item.product_id,
        quantity=item.quantity
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

@router.put("/items/{item_id}", response_model=CartItemSchema)
def update_cart_item(item_id: int, item_update: CartItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Obtener el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    
    # Buscar el item en el carrito
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")
    
    # Verificar stock suficiente si se actualiza la cantidad
    if item_update.quantity:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if product.stock < item_update.quantity:
            raise HTTPException(status_code=400, detail="Stock insuficiente")
        cart_item.quantity = item_update.quantity
    
    db.commit()
    db.refresh(cart_item)
    return cart_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Obtener el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    
    # Buscar el item en el carrito
    cart_item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item no encontrado en el carrito")
    
    # Eliminar el item del carrito
    db.delete(cart_item)
    db.commit()
    return None

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Obtener el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Carrito no encontrado")
    
    # Eliminar todos los items del carrito
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return None