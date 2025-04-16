# TiendaF - API para Tienda de Productos

Este proyecto implementa una API RESTful para gestionar una tienda online de productos para hombres y mujeres, utilizando FastAPI y SQLite/PostgreSQL.

## Configuración e Instalación

### Requisitos previos
- Python 3.8+
- SQLite (incluido) o PostgreSQL (opcional)

### Pasos de instalación

1. Clonar el repositorio:
   ```
   git clone <url-del-repositorio>
   cd TiendaF
   ```

2. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno (editar archivo `.env`):
   ```
   # SQLite (predeterminado)
   DATABASE_URL=sqlite:///./tienda.db
   
   # PostgreSQL (opcional)
   # DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/tienda_db
   
   SECRET_KEY=tu_clave_secreta_muy_segura
   ```

4. Inicializar la base de datos:
   ```
   alembic upgrade head
   python init_data.py
   ```

5. Ejecutar el servidor:
   ```
   uvicorn main:app --reload
   ```

6. Acceder a la documentación API:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Estructura del Proyecto

- `app/`: Código principal de la aplicación
  - `database/`: Configuración de la base de datos
  - `models/`: Modelos SQLAlchemy
  - `routes/`: Rutas de la API
  - `schemas/`: Esquemas Pydantic
  - `utils/`: Utilidades (autenticación, etc.)
- `migrations/`: Migraciones de Alembic
- `tests/`: Tests automatizados

## Endpoints Principales

### Autenticación
- `POST /auth/login`: Iniciar sesión y obtener token JWT

### Usuarios
- `POST /users/`: Crear nuevo usuario
- `GET /users/me`: Obtener información del usuario actual
- `GET /users/`: Listar usuarios (solo admin)

### Productos
- `GET /products/`: Listar productos (con filtros)
- `POST /products/`: Crear producto (solo admin)
- `GET /products/{id}`: Obtener detalles de un producto

### Categorías
- `GET /categories/`: Listar categorías
- `POST /categories/`: Crear categoría (solo admin)

### Carrito de Compras
- `GET /cart/`: Ver carrito actual
- `POST /cart/items`: Añadir producto al carrito
- `DELETE /cart/items/{id}`: Eliminar producto del carrito

### Órdenes
- `POST /orders/checkout`: Convertir carrito en orden
- `GET /orders/`: Listar órdenes del usuario
- `GET /orders/{id}`: Ver detalles de una orden

## Datos de Prueba

El script `init_data.py` crea:
- Usuario admin: admin@tiendaf.com / admin123
- Categorías: Camisetas, Pantalones, Zapatillas, Accesorios, Sombreros
- Varios productos de ejemplo

## Licencia

[Incluir información de licencia]

