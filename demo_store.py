"""Thread-safe, disposable synthetic store. Never connects to MySQL."""
from copy import deepcopy
from pathlib import Path
import json
from threading import RLock
SEED = json.loads((Path(__file__).parent/'static/demo-data.json').read_text())
class Store:
    def __init__(self, records):
        self.lock = RLock()
        self.reset(records)
    def reset(self, records):
        with self.lock:
            self.records = {r['id']:deepcopy(r) for r in records}
            self.next_id = max(self.records,default=0)+1
    def getAll(self):
        with self.lock:return deepcopy(list(self.records.values()))
    def findByID(self,id):
        with self.lock:return deepcopy(self.records.get(id))
    def create(self,record):
        with self.lock:
            id=self.next_id;self.next_id+=1
            self.records[id]=dict(record,id=id)
            return id
    def update(self,id,record):
        with self.lock:self.records[id]=dict(record,id=id)
    def delete(self,id):
        with self.lock:self.records.pop(id,None)
CarDao=Store(SEED['cars'])
class CustomerDAO(Store):
    def __init__(self):super().__init__(SEED['customers'])
