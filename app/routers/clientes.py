from fastapi import APIRouter, HTTPException
from pymysql.err import IntegrityError
from app.database import conectar
from app.schemas import ClienteCrear, ClienteRespuesta
router = APIRouter(prefix='/clientes', tags=['Clientes'])
@router.get('', response_model=list[ClienteRespuesta])
def listar():
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM clientes ORDER BY id')
            return cur.fetchall()
        
@router.get('/{cliente_id}', response_model=ClienteRespuesta)
def obtener(cliente_id: int):
    with conectar() as db:
        with db.cursor() as cur:
            cur.execute('SELECT * FROM clientes WHERE id=%s', (cliente_id,))
            cliente = cur.fetchone()
            if cliente is None:
                raise HTTPException(404, 'Cliente no encontrado')
            return cliente

@router.post('', response_model=ClienteRespuesta, status_code=201)
def crear(datos: ClienteCrear):
    try:
        with conectar() as db:
            with db.cursor() as cur:
                cur.execute(
                    'INSERT INTO clientes (nombre,correo) VALUES (%s,%s)',
                    (datos.nombre, str(datos.correo))
                )
                nuevo_id = cur.lastrowid
                cur.execute('SELECT * FROM clientes WHERE id=%s', (nuevo_id,))
                return cur.fetchone()
    except IntegrityError as exc:
        raise HTTPException(409, 'Correo ya registrado') from exc


@router.get('/{cliente_id}/pedidos')
def listar_pedidos_cliente(cliente_id: int):
    with conectar() as db:
        with db.cursor() as cur:
            #Verifica si el cliente existe
            cur.execute('SELECT id FROM clientes WHERE id = %s', (cliente_id,)) 
            if cur.fetchone() is None: 
                raise HTTPException(404, 'Cliente no encontrado') #Si el cliente no existe arroja error 404

            #Consultar los pedidos del cliente
            cur.execute('''
            SELECT id, fecha, estado, total
            FROM pedidos
            WHERE cliente_id = %s
            ORDER BY fecha DESC
            ''', (cliente_id,))
            return cur.fetchall()