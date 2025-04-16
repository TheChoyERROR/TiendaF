from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.routes import auth, users, categories, products, cart, orders
from app.database.database import engine
from app.models import models

# Cargar variables de entorno
load_dotenv()

# Crear tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

# Inicializar la aplicación
app = FastAPI(
    title="TiendaF API",
    description="API para una tienda de productos para hombres y mujeres",
    version="0.1.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de TiendaF"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)