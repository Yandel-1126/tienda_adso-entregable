from decimal import Decimal
from fastapi import APIRouter, HTTPException
from app.database import conectar
from app.schemas import PedidoCrear

router = APIRouter(prefix='/pedidos', tags=['Pedidos'])

@router.post('', status_code=201)
def crear(datos: PedidoCrear):
    if len({i.producto_id for i in datos.items}) != len(datos.items):
        raise HTTPException(422, 'No repita el mismo producto en un pedido')
    
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT id FROM clientes WHERE id=%s', (datos.cliente_id,))
            if cur.fetchone() is None:
                raise HTTPException(404, 'Cliente no encontrado')
            
            items = sorted(datos.items, key=lambda x: x.producto_id)
            detalles = []
            total = Decimal('0.00')
            
            for item in items:
                cur.execute('SELECT id, precio, stock FROM productos WHERE id=%s FOR UPDATE', (item.producto_id,))
                p = cur.fetchone()
                if p is None:
                    raise HTTPException(404, f'Producto {item.producto_id} no encontrado')
                if p['stock'] < item.cantidad:
                    raise HTTPException(409, f'Stock insuficiente del producto {item.producto_id}')
                
                subtotal = p['precio'] * item.cantidad
                total += subtotal
                detalles.append((item.producto_id, item.cantidad, p['precio'], subtotal))
            
            cur.execute('INSERT INTO pedidos (cliente_id, total) VALUES (%s, %s)', (datos.cliente_id, total))
            pedido_id = cur.lastrowid
            
            for producto_id, cantidad, precio, subtotal in detalles:
                cur.execute(
                    'INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)', 
                    (pedido_id, producto_id, cantidad, precio, subtotal)
                )
                cur.execute('UPDATE productos SET stock = stock - %s WHERE id = %s', (cantidad, producto_id))
            
            db.commit() # Asegúrate de hacer commit si tu gestor de conexiones lo requiere
            
            return {
                'id': pedido_id, 
                'cliente_id': datos.cliente_id, 
                'estado': 'confirmado', 
                'total': str(total), 
                'items': len(detalles)
            }

@router.get('')
def listar():
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('''
                SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente
                FROM pedidos p 
                JOIN clientes c ON c.id = p.cliente_id 
                ORDER BY p.id DESC
            ''')
            return cur.fetchall()

@router.get('/{pedido_id}')
def detalle(pedido_id: int):
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('''
                SELECT p.id, p.fecha, p.estado, p.total, c.nombre AS cliente
                FROM pedidos p 
                JOIN clientes c ON c.id = p.cliente_id 
                WHERE p.id = %s
            ''', (pedido_id,))
            
            pedido = cur.fetchone()
            if pedido is None:
                raise HTTPException(404, 'Pedido no encontrado')
            
            cur.execute('''
                SELECT d.producto_id, pr.nombre AS producto, d.cantidad, d.precio_unitario, d.subtotal
                FROM detalle_pedidos d 
                JOIN productos pr ON pr.id = d.producto_id
                WHERE d.pedido_id = %s 
                ORDER BY d.id
            ''', (pedido_id,))
            
            pedido['items'] = cur.fetchall()
            return pedido