"""Regression checks for reset, duplicates, normalization and safe failures."""
import os
os.environ['DEMO_MODE']='1'
import unittest
from unittest.mock import patch
from CarServer import app,CarDao

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.client=app.test_client()
        self.client.post('/api/demo/reset',json={})
    def test_reset_restores_seed_and_identifiers(self):
        self.client.delete('/cars/1')
        self.client.post('/api/demo/reset',json={})
        self.assertEqual(len(self.client.get('/cars').json),8)
        self.assertEqual(len(self.client.get('/customer').json),6)
        self.assertEqual(self.client.get('/cars/1').json['Price'],39)
    def test_duplicate_vehicle_and_customer_are_conflicts(self):
        for route,label,value in [('/cars','Model','Toyota Yaris'),('/customer','Name','Alex Sample')]:
            self.assertEqual(self.client.post(route,json={'Reg':'demo-001',label:value,'Price':39}).status_code,409)
    def test_trimmed_fields_are_saved_consistently(self):
        r=self.client.post('/cars',json={'Reg':' qa-9 ','Model':' Example ','Price':'45'})
        self.assertEqual(r.status_code,201)
        self.assertEqual(r.json,dict(Reg='QA-9',Model='Example',Price=45,id=9))
    def test_invalid_shape_and_unsupported_method(self):
        self.assertEqual(self.client.post('/cars',data='not-json',content_type='text/plain').status_code,415)
        self.assertEqual(self.client.patch('/cars/1',json={}).status_code,405)
        for value in [None,{},[],1.0,'1e2',' 4','1.5',True]:
            self.assertEqual(self.client.post('/cars',json={'Reg':'QA','Model':'Example','Price':value}).status_code,400)
    def test_cross_origin_changes_are_rejected(self):
        r=self.client.delete('/cars/1',headers={'Origin':'https://unrelated.example'})
        self.assertEqual(r.status_code,403)
        self.assertEqual(self.client.get('/cars/1').status_code,200)
    def test_catalog_errors_are_safe_json(self):
        with patch.object(CarDao,'getAll',side_effect=RuntimeError('private diagnostic')):
            r=self.client.get('/cars')
        self.assertEqual(r.status_code,503)
        self.assertNotIn('private diagnostic',r.text)
        self.assertIn('unavailable',r.json['error'])
    def test_html_modes_and_security_headers(self):
        response=self.client.get('/')
        self.assertIn('data-mode="server"',response.text)
        self.assertIn("frame-ancestors 'none'",response.headers['Content-Security-Policy'])
        self.assertEqual(self.client.get('/api/mode').json['mode'],'synthetic Flask')
        self.assertEqual(self.client.get('/cars').headers['Cache-Control'],'no-store')

if __name__=='__main__':unittest.main()
