"""Build the public demo from the same frontend Flask serves."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
out=root/'docs';out.mkdir(exist_ok=True)
for name in ['index.html','app.css','app.js','rules.js','demo-data.json','rental-rules.js','reservations-ui.js','reservation-seed.json','reservations.css']:
    shutil.copy2(root/'static'/name,out/name)
(out/'.nojekyll').touch()
print('Static demonstration built from shared frontend assets.')
