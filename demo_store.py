"""Ephemeral synthetic records for local demonstrations. No MySQL connection."""
from copy import deepcopy
class Store:
    def __init__(self, records):
        self.records = {r['id']: deepcopy(r) for r in records}
        self.next_id = max(self.records, default=0) + 1
    def getAll(self):
        return list(self.records.values())
    def findByID(self, id):
        return self.records.get(id)
    def create(self, record):
        id = self.next_id
        self.next_id += 1
        self.records[id] = dict(record, id=id)
        return id
    def update(self, id, record):
        self.records[id] = dict(record, id=id)
    def delete(self, id):
        self.records.pop(id, None)
CarDao = Store([{'id':1,'Reg':'DEMO-001','Model':'Skoda Fabia','Price':13000},
                {'id':2,'Reg':'DEMO-002','Model':'Audi A3','Price':20000}])
class CustomerDAO(Store):
    def __init__(self):
        super().__init__([{'id':1,'Reg':'DEMO-001','Name':'Sample Customer A','Price':13000},
                          {'id':2,'Reg':'DEMO-002','Name':'Sample Customer B','Price':20000}])
