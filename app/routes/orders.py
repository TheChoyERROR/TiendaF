from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app.database.database import get_db
from app.models.models import Order, OrderItem, Cart, CartItem, Product, User, OrderStatus
from app.schemas.schemas import OrderCreate, Order as OrderSchema, OrderUpdate
from app.utils.auth import get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={404: {"description": "No encontrado"}}
)

@router.post("/", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Si no se proporciona el ID de usuario, usar el usuario actual
    user_id = order_data.user_id if hasattr(order_data, "user_id") else current_user.id
    
    # Para administradores, permitir crear órdenes para cualquier usuario
    if user_id != current_user.id:
        # Verificar si el usuario es administrador
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden crear órdenes para otros usuarios"
            )
    
    # Crear la orden
    new_order = Order(
        user_id=user_id,
        total_amount=order_data.total_amount,
        shipping_address=order_data.shipping_address,
        status=order_data.status
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Agregar los items de la orden
    for item_data in order_data.items:
        # Verificar que el producto existe y está activo
        product = db.query(Product).filter(Product.id == item_data.product_id, Product.is_active == True).first()
        if not product:
            # Rollback y eliminar la orden
            db.delete(new_order)
            db.commit()
            raise HTTPException(status_code=404, detail=f"Producto con ID {item_data.product_id} no encontrado o no disponible")
        
        # Verificar stock suficiente
        if product.stock < item_data.quantity:
            # Rollback y eliminar la orden
            db.delete(new_order)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Stock insuficiente para el producto con ID {item_data.product_id}")
        
        # Crear item de orden
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=item_data.price
        )
        db.add(order_item)
        
        # Actualizar stock del producto
        product.stock -= item_data.quantity
    
    db.commit()
    db.refresh(new_order)
    return new_order

@router.post("/checkout", response_model=OrderSchema)
def checkout(shipping_address: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Obtener el carrito del usuario
    cart = db.query(Cart).filter(Cart.user_id == current_user.id).first()
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="El carrito está vacío")
    
    # Verificar stock y calcular total
    total_amount = 0
    order_items = []
    
    for cart_item in cart.items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        
        # Verificar que el producto existe y está activo
        if not product or not product.is_active:
            raise HTTPException(
                status_code=400, 
                detail=f"El producto con ID {cart_item.product_id} ya no está disponible"
            )
        
        # Verificar stock suficiente
        if product.stock < cart_item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente para {product.name}. Disponible: {product.stock}, Solicitado: {cart_item.quantity}"
            )
        
        # Calcular subtotal y agregar al total
        item_price = product.price
        item_total = item_price * cart_item.quantity
        total_amount += item_total
        
        # Crear item de orden para agregar más tarde
        order_items.append({
            "product_id": product.id,
            "quantity": cart_item.quantity,
            "price": item_price
        })
    
    # Crear la orden
    new_order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=shipping_address,
        status=OrderStatus.PENDIENTE
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Agregar los items de la orden y actualizar stock
    for item_data in order_items:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)
        
        # Actualizar stock del producto
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock -= item_data["quantity"]
    
    # Vaciar el carrito
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    
    db.commit()
    db.refresh(new_order)
    return new_order

@router.get("/", response_model=List[OrderSchema])
def get_user_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Si es administrador, mostrar todas las órdenes con paginación
    if current_user.is_admin:
        orders = db.query(Order).offset(skip).limit(limit).all()
    else:
        # Si es un usuario regular, mostrar solo sus órdenes
        orders = db.query(Order).filter(Order.user_id == current_user.id).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Buscar la orden
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Si no es administrador, verificar que la orden pertenezca al usuario
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta orden"
        )
    
    return order

@router.put("/{order_id}", response_model=OrderSchema)
def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    # Solo administradores pueden actualizar órdenes
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Actualizar campos
    if order_update.status is not None:
        order.status = order_update.status
    
    if order_update.shipping_address:
        order.shipping_address = order_update.shipping_address
    
    db.commit()
    db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(order_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    # Buscar la orden
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    
    # Verificar permisos: solo el dueño de la orden o un administrador puede cancelarla
    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cancelar esta orden"
        )
    
    # Solo se pueden cancelar órdenes en estado PENDIENTE
    if order.status != OrderStatus.PENDIENTE:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cancelar una orden con estado {order.status.value}"
        )
    
    # Actualizar estado a CANCELADO
    order.status = OrderStatus.CANCELADO
    
    # Restaurar el stock de los productos
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
    
    db.commit()
    return None