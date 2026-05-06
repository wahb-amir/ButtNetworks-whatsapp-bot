import psycopg
from pgvector.psycopg import register_vector
from psycopg.rows import dict_row

from app.core.config import settings


def get_conn():
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    register_vector(conn)
    return conn