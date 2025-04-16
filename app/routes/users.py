from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database.database import get_db
from app.models.models import User, Cart
from app.schemas.schemas import UserCreate, User as UserSchema, UserUpdate
from app.utils.auth import get_password_hash, get_current_active_user, get_current_admin_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "No encontrado"}}
)

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Crear el usuario con contraseña hasheada
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        password=hashed_password,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Crear un carrito vacío para el usuario
    cart = Cart(user_id=db_user.id)
    db.add(cart)
    db.commit()
    
    return db_user

@router.get("/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

@router.put("/me", response_model=UserSchema)
def update_user_me(user: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if user.email and user.email != current_user.email:
        # Verificar que el nuevo email no esté en uso
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Actualizar campos si están presentes
    if user.email:
        current_user.email = user.email
    if user.first_name:
        current_user.first_name = user.first_name
    if user.last_name:
        current_user.last_name = user.last_name
    if user.password:
        current_user.password = get_password_hash(user.password)
    if user.is_active is not None:
        # Solo los administradores pueden cambiar el estado activo
        admin_user = db.query(User).filter(User.id == current_user.id, User.is_admin == True).first()
        if admin_user:
            current_user.is_active = user.is_active
    
    db.commit()
    db.refresh(current_user)
    return current_user

# Rutas administrativas
@router.get("/", response_model=List[UserSchema])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db_user

@router.put("/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Verificar que el nuevo email no esté en uso
    if user.email and user.email != db_user.email:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    # Actualizar campos si están presentes
    if user.email:
        db_user.email = user.email
    if user.first_name:
        db_user.first_name = user.first_name
    if user.last_name:
        db_user.last_name = user.last_name
    if user.is_active is not None:
        db_user.is_active = user.is_active
    if user.is_admin is not None:
        db_user.is_admin = user.is_admin
    if user.password:
        db_user.password = get_password_hash(user.password)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir eliminar al usuario actual
    if db_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    db.delete(db_user)
    db.commit()
    return None