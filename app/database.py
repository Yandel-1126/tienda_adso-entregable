import os
from contextlib import contextmanager
import pymysql
from dotenv import load_dotenv
load_dotenv()
@contextmanager
def conectar():
    conexion = pymysql.connect(
        host=os.getenv('DB_HOST','localhost'),
        port=int(os.getenv('DB_PORT','3306')),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.getenv('DB_NAME','tienda_adso'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
        connect_timeout=10,
    )
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise 
    finally: conexion.close()