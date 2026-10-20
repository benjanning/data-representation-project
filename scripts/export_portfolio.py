"""Export only approved metadata and image files after the release checks pass."""
from pathlib import Path
import os,json,hashlib,shutil,re
root=Path(__file__).resolve().parents[1]
config=json.loads((root/'portfolio/project.json').read_text(encoding='utf-8'))
sha=os.environ['GITHUB_SHA'];repo=os.environ['GITHUB_REPOSITORY'];run=int(os.environ['GITHUB_RUN_ID'])
if not re.fullmatch('[0-9a-f]{40}',sha) or repo!='benjanning/'+config['project']['repo']:raise ValueError('Release identity mismatch')
out=Path(os.environ['RUNNER_TEMP'])/'portfolio-package';(out/'assets').mkdir(parents=True,exist_ok=True)
assets=[]
for item in config['assets']:
    name=item['name'];source=(root/item['path']).resolve()
    if source.is_relative_to(root) is False or not re.fullmatch(r'[a-z0-9-]+\.(?:png|jpg|webp)',name):raise ValueError('Unsafe asset path')
    raw=source.read_bytes()
    if len(raw)>4_000_000 or not raw.startswith((b'\x89PNG\r\n\x1a\n',b'\xff\xd8\xff',b'RIFF')):raise ValueError('Unsupported image')
    (out/'assets'/name).write_bytes(raw)
    assets.append(dict(name=name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),provenance=item['provenance']))
manifest=dict(schema_version=1,source_repository=repo,source_revision=sha,verification_run=run,project=config['project'],assets=assets)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Exported verified project package:',repo,sha,len(assets),'images')
