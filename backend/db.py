from contextlib import contextmanager

from mysql.connector import pooling

from config import DB_CONFIG

_pool = None


def get_conn():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(pool_name="hms", pool_size=8, **DB_CONFIG)
    return _pool.get_connection()


def query(sql, params=None, one=False):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        rows = cur.fetchall()
        return (rows[0] if rows else None) if one else rows
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid, cur.rowcount
    finally:
        conn.close()


@contextmanager
def transaction():
    """with db.transaction() as cur: ...  -> commit on success, rollback on any exception."""
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        conn.start_transaction()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
