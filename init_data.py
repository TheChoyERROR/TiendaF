import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Añadir la ruta del proyecto al path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# Importar modelos y configuración de base de datos
from app.models.models import User, Category, Product, GenderType
from app.database.database import SessionLocal, engine

# Cargar variables de entorno
load_dotenv()

# Configurar encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_initial_data():
    db = SessionLocal()
    try:
        # Verificar si ya existen datos para evitar duplicados
        user_count = db.query(User).count()
        category_count = db.query(Category).count()
        
        if user_count == 0:
            print("Creando usuario administrador...")
            admin_user = User(
                email="admin@tiendaf.com",
                password=pwd_context.hash("admin123"),
                first_name="Admin",
                last_name="Usuario",
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
            print("Usuario administrador creado exitosamente.")
        else:
            print("Ya existe al menos un usuario en la base de datos.")
            
        if category_count == 0:
            print("Creando categorías iniciales...")
            # Crear categorías
            categories = [
                Category(name="Camisetas", description="Camisetas para hombres y mujeres"),
                Category(name="Pantalones", description="Pantalones y jeans"),
                Category(name="Zapatillas", description="Calzado deportivo"),
                Category(name="Accesorios", description="Complementos como relojes, pulseras, etc."),
                Category(name="Sombreros", description="Gorras, sombreros y complementos para la cabeza")
            ]
            db.add_all(categories)
            db.commit()
            
            # Obtener las categorías creadas para asignarlas a productos
            camisetas = db.query(Category).filter(Category.name == "Camisetas").first()
            pantalones = db.query(Category).filter(Category.name == "Pantalones").first()
            zapatillas = db.query(Category).filter(Category.name == "Zapatillas").first()
            accesorios = db.query(Category).filter(Category.name == "Accesorios").first()
            
            # Crear productos iniciales
            products = [
                Product(
                    name="Camiseta Básica Negra", 
                    description="Camiseta básica de algodón en color negro",
                    price=19.99,
                    stock=100,
                    image_url="https://example.com/camiseta-negra.jpg",
                    gender=GenderType.UNISEX,
                    is_active=True,
                    sku="CAM-001",
                    categories=[camisetas]
                ),
                Product(
                    name="Jeans Ajustados", 
                    description="Pantalón vaquero ajustado para hombre",
                    price=49.99,
                    stock=50,
                    image_url="https://example.com/jeans-hombre.jpg",
                    gender=GenderType.HOMBRE,
                    is_active=True,
                    sku="PAN-001",
                    categories=[pantalones]
                ),
                Product(
                    name="Zapatillas Running", 
                    description="Zapatillas de running con amortiguación",
                    price=89.99,
                    stock=30,
                    image_url="https://example.com/zapatillas-running.jpg",
                    gender=GenderType.UNISEX,
                    is_active=True,
                    sku="ZAP-001",
                    categories=[zapatillas]
                ),
                Product(
                    name="Reloj Minimalista", 
                    description="Reloj de pulsera con diseño elegante y minimalista",
                    price=59.99,
                    stock=20,
                    image_url="https://example.com/reloj.jpg",
                    gender=GenderType.UNISEX,
                    is_active=True,
                    sku="ACC-001",
                    categories=[accesorios]
                ),
                Product(
                    name="Vestido Casual", 
                    description="Vestido casual para primavera-verano",
                    price=39.99,
                    stock=40,
                    image_url="https://example.com/vestido.jpg",
                    gender=GenderType.MUJER,
                    is_active=True,
                    sku="VES-001",
                    categories=[camisetas]
                )
            ]
            db.add_all(products)
            db.commit()
            print("Categorías y productos iniciales creados exitosamente.")
        else:
            print("Ya existen categorías en la base de datos.")
        
    except Exception as e:
        db.rollback()
        print(f"Error al crear datos iniciales: {e}")
    finally:
        db.close()
        
if __name__ == "__main__":
    create_initial_data()
    print("Proceso de inicialización completado.")