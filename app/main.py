from fastapi import FastAPI
from app.routers import clientes, productos, pedidos

app = FastAPI(
 title='Taller 3 ADSO - Tienda', 
 version='3.0', 
 description='API relacional: clientes, productos, pedidos y detalles'
)

app.include_router(clientes.router)
app.include_router(productos.router)
app.include_router(pedidos.router)
@app.get('/', tags=['Inicio'])
def inicio():
 return {'mensaje': 'API tienda ADSO', 'documentacion': '/docs'}