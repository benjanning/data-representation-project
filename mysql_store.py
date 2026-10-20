"""Bounded pooled connections; parameterized queries and guaranteed cleanup."""
import dbconfig as cfg
from mysql.connector.pooling import MySQLConnectionPool
class MySQLStore:
    def __init__(self,table,label):
        if (table,label) not in [('cars','Model'),('customer','Name')]:raise ValueError('Unsupported table')
        self.table=table;self.label=label;self.pool=None
    def query(self,sql,args=(),write=False,one=False):
        if self.pool is None:
            self.pool=MySQLConnectionPool(pool_name='portfolio_'+self.table,pool_size=3,connection_timeout=5,**cfg.mysql)
        connection=self.pool.get_connection();cursor=None
        try:
            cursor=connection.cursor();cursor.execute(sql,args)
            if write:connection.commit();return cursor.lastrowid
            rows=cursor.fetchone() if one else cursor.fetchall()
            convert=lambda row:dict(zip(['id','Reg',self.label,'Price'],row))
            return convert(rows) if one and rows else (None if one else [convert(row) for row in rows])
        except Exception:
            if write:connection.rollback()
            raise
        finally:
            if cursor:cursor.close()
            connection.close()
    def getAll(self):return self.query(f'SELECT id,reg,{self.label.lower()},price FROM {self.table} ORDER BY id')
    def findByID(self,id):return self.query(f'SELECT id,reg,{self.label.lower()},price FROM {self.table} WHERE id=%s',(id,),one=True)
    def create(self,record):return self.query(f'INSERT INTO {self.table} (reg,{self.label.lower()},price) VALUES (%s,%s,%s)',(record['Reg'],record[self.label],record['Price']),write=True)
    def update(self,id,record):return self.query(f'UPDATE {self.table} SET reg=%s,{self.label.lower()}=%s,price=%s WHERE id=%s',(record['Reg'],record[self.label],record['Price'],id),write=True)
    def delete(self,id):return self.query(f'DELETE FROM {self.table} WHERE id=%s',(id,),write=True)
