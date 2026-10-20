"""Storage-compatible rules; Price is a whole-euro daily example rate."""
import re
def validate_record(value,label):
    if not isinstance(value,dict):raise ValueError('Provide a JSON object.')
    reg=value.get('Reg');name=value.get(label)
    if not isinstance(reg,str) or not re.fullmatch(r'[A-Za-z0-9 -]{1,20}',reg.strip()):
        raise ValueError('Vehicle reference must contain 1–20 letters, numbers, spaces or hyphens.')
    if not isinstance(name,str) or not 1<=len(name.strip())<=250:
        raise ValueError(f'{label} must contain 1–250 characters.')
    price=value.get('Price')
    if isinstance(price,bool) or not re.fullmatch(r'[0-9]+',str(price)) or not 0<=int(price)<=1000000000:
        raise ValueError('Daily rate must be a whole euro amount between 0 and 1,000,000,000.')
    return {'Reg':reg.strip().upper(),label:name.strip(),'Price':int(price)}
