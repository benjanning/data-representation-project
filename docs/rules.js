(function(root){
  'use strict';
  function validate(value,label){
    if(!value||typeof value!=='object'||Array.isArray(value))throw Error('Provide a record.');
    if(typeof value.Reg!=='string'||!/^[A-Za-z0-9 -]{1,20}$/.test(value.Reg.trim()))throw Error('Vehicle reference must contain 1–20 letters, numbers, spaces or hyphens.');
    if(typeof value[label]!=='string'||value[label].trim().length<1||value[label].trim().length>250)throw Error(label+' must contain 1–250 characters.');
    if(typeof value.Price==='boolean'||!/^[0-9]+$/.test(String(value.Price))||Number(value.Price)>1000000000)throw Error('Daily rate must be a whole euro amount between 0 and 1,000,000,000.');
    return {Reg:value.Reg.trim().toUpperCase(),[label]:value[label].trim(),Price:Number(value.Price)};
  }
  const rules={validate};
  if(typeof module!=='undefined')module.exports=rules;
  else root.FleetRules=rules;
})(typeof window!=='undefined'?window:globalThis);
