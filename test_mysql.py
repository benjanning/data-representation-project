"""Opt-in CRUD against a disposable MySQL schema; never run against real records."""
import os,unittest,base64,importlib.util
from pathlib import Path
@unittest.skipUnless(os.getenv('RUN_MYSQL_TESTS')=='1','Disposable MySQL integration is opt-in')
class MySQLIntegration(unittest.TestCase):
    def test_both_resources_and_authentication(self):
        import mysql.connector
        config=dict(host=os.environ['DB_HOST'],port=int(os.getenv('DB_PORT','3306')),user=os.environ['DB_USER'],password=os.environ['DB_PASSWORD'],database=os.environ['DB_NAME'])
        if config['database']!='portfolio_integration':raise RuntimeError('Use the isolated portfolio_integration database only.')
        db=mysql.connector.connect(**config);cursor=db.cursor()
        try:
            for table,column in [('cars','model'),('customer','name')]:
                cursor.execute(f'CREATE TABLE IF NOT EXISTS {table}(id INT AUTO_INCREMENT PRIMARY KEY,reg VARCHAR(250),{column} VARCHAR(250),price INT)')
            db.commit()
        finally:cursor.close();db.close()
        old=os.environ.get('DEMO_MODE');os.environ['DEMO_MODE']='0'
        try:
            spec=importlib.util.spec_from_file_location('mysql_test_app',Path(__file__).with_name('CarServer.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        finally:
            if old is None:os.environ.pop('DEMO_MODE',None)
            else:os.environ['DEMO_MODE']=old
        client=module.app.test_client()
        self.assertEqual(client.get('/cars').status_code,401)
        auth=base64.b64encode((os.environ['DEMO_USERNAME']+':'+os.environ['DEMO_PASSWORD']).encode()).decode()
        headers={'Authorization':'Basic '+auth}
        for route,label in [('/cars','Model'),('/customer','Name')]:
            payload=dict(Reg='INTEGRATION',Price=43,**{label:'Synthetic integration record'})
            created=client.post(route,json=payload,headers=headers)
            self.assertEqual(created.status_code,201,created.text)
            url=route+'/'+str(created.json['id'])
            try:
                self.assertEqual(client.get(url,headers=headers).json['Price'],43)
                payload['Price']=47
                self.assertEqual(client.put(url,json=payload,headers=headers).status_code,200)
                self.assertEqual(client.get(url,headers=headers).json['Price'],47)
            finally:self.assertEqual(client.delete(url,headers=headers).status_code,200)
            self.assertEqual(client.get(url,headers=headers).status_code,404)
        self.assertEqual(client.post('/api/demo/reset',json={},headers=headers).status_code,404)
if __name__=='__main__':unittest.main()
