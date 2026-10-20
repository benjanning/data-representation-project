const {test}=require('node:test'),assert=require('node:assert/strict'),{validate}=require('../static/rules');
test('normalizes storage-compatible records',()=>assert.deepEqual(validate({Reg:' demo-9 ',Model:' Sample ',Price:'45'},'Model'),{Reg:'DEMO-9',Model:'Sample',Price:45}));
test('rejects invalid rate and reference domains',()=>{for(let Price of [true,null,'1.2','1e2',-1,Infinity,1000000001])assert.throws(()=>validate({Reg:'R',Model:'M',Price},'Model'));assert.throws(()=>validate({Reg:'<x>',Model:'M',Price:1},'Model'));});
