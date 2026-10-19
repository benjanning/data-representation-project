import os, unittest
os.environ['DEMO_MODE'] = '1'
from CarServer import app
class ApiTests(unittest.TestCase):
    def setUp(self): self.client = app.test_client()
    def test_home_case_sensitive(self):
        with self.client.get('/') as response:
            self.assertEqual(response.status_code, 200)
    def test_missing_record_is_404(self):
        for route in ['/cars/999999','/customer/999999']:
            self.assertEqual(self.client.get(route).status_code, 404)
    def test_invalid_records(self):
        for payload in [{}, {'Reg':'R','Model':'M','Price':-1}, []]:
            self.assertEqual(self.client.post('/cars',json=payload).status_code,400)
    def test_price_domain_and_missing_deletes(self):
        for price in [True, 1.5, float('inf'), 1000000001]:
            self.assertEqual(self.client.post('/cars',json=dict(Reg='TEST',Model='Demo',Price=price)).status_code,400)
        for route in ['/cars/999999','/customer/999999']:
            self.assertEqual(self.client.delete(route).status_code,404)
    def test_crud(self):
        for route, payload in [('/cars',dict(Reg='TEST',Model='Demo',Price=25)),('/customer',dict(Reg='TEST',Name='Sample',Price=25))]:
            created = self.client.post(route,json=payload)
            self.assertEqual(created.status_code,201)
            url = route + '/' + str(created.json['id'])
            self.assertEqual(self.client.get(url).json['Reg'],'TEST')
            payload['Price']=50
            self.assertEqual(self.client.put(url,json=payload).status_code,200)
            self.assertEqual(self.client.get(url).json['Price'],50)
            self.assertEqual(self.client.delete(url).status_code,200)
            self.assertEqual(self.client.get(url).status_code,404)
if __name__ == '__main__': unittest.main()
