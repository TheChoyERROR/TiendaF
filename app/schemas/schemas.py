from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import re

# Función para validar formato de email
def validate_email(email: str) -> str:
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(pattern, email):
        raise ValueError('Email inválido')
    return email

# Enum para el género
class GenderType(str, Enum):
    HOMBRE = "hombre"
    MUJER = "mujer"
    UNISEX = "unisex"

# Enum para el estado de las órdenes
class OrderStatus(str, Enum):
    PENDIENTE = "pendiente"
    PAGADO = "pagado"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

# Esquemas para Categoría
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None

class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para Producto
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    image_url: Optional[str] = None
    gender: GenderType
    is_active: bool = True
    sku: Optional[str] = None

class ProductCreate(ProductBase):
    category_ids: List[int]

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    image_url: Optional[str] = None
    gender: Optional[GenderType] = None
    is_active: Optional[bool] = None
    sku: Optional[str] = None
    category_ids: Optional[List[int]] = None

class Product(ProductBase):
    id: int
    categories: List[Category]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para Usuario
class UserBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    
    # Validador de email
    @validator('email')
    def email_must_be_valid(cls, v):
        return validate_email(v)

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    
    # Validador de email
    @validator('email')
    def email_must_be_valid(cls, v):
        if v is None:
            return v
        return validate_email(v)

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para Dirección
class AddressBase(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    is_default: bool = False

class AddressCreate(AddressBase):
    pass

class AddressUpdate(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_default: Optional[bool] = None

class Address(AddressBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para Ítem de Carrito
class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)

class CartItemCreate(CartItemBase):
    pass

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=1)

class CartItem(CartItemBase):
    id: int
    cart_id: int
    created_at: datetime
    updated_at: datetime
    product: Product

    class Config:
        orm_mode = True

# Esquemas para Carrito
class CartBase(BaseModel):
    pass

class CartCreate(CartBase):
    user_id: int

class Cart(CartBase):
    id: int
    user_id: int
    items: List[CartItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para Ítem de Orden
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime
    product: Product

    class Config:
        orm_mode = True

# Esquemas para Orden
class OrderBase(BaseModel):
    shipping_address: str
    status: OrderStatus = OrderStatus.PENDIENTE

class OrderCreate(OrderBase):
    user_id: int
    items: List[OrderItemCreate]
    total_amount: float = Field(gt=0)

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    shipping_address: Optional[str] = None

class Order(OrderBase):
    id: int
    user_id: int
    total_amount: float
    items: List[OrderItem] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Esquemas para autenticación
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class Login(BaseModel):
    email: str
    password: str
    
    # Validador de email
    @validator('email')
    def email_must_be_valid(cls, v):
        return validate_email(v)