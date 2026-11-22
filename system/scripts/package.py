from pathlib import Path
import zipfile
import hashlib

root=Path(__file__).resolve().parents[1]
release=root/'release'
release.mkdir(exist_ok=True)
archive=release/'InstrumentHub-1.0.0.zip'
included=['backend/src','frontend/src','frontend/e2e','frontend/dist','miniprogram','scripts','docs']
files=['README.md','compose.yml','.env.example','.gitignore','.editorconfig','.gitattributes','maven-settings.xml',
       'backend/pom.xml','backend/Dockerfile','backend/.dockerignore',
       'frontend/package.json','frontend/package-lock.json','frontend/index.html','frontend/vite.config.js','frontend/playwright.config.js','frontend/nginx.conf','frontend/Dockerfile','frontend/.dockerignore','frontend/.env.example']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for folder in included:
        for f in sorted((root/folder).rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:
                z.write(f,'InstrumentHub/'+f.relative_to(root).as_posix())
    for name in files:
        z.write(root/name,'InstrumentHub/'+name)
    jar=root/'backend/target/instrumenthub-1.0.0.jar'
    z.write(jar,'InstrumentHub/backend/target/instrumenthub-1.0.0.jar')
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
(release/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n',encoding='utf-8')
print(f'{archive} ({archive.stat().st_size:,} bytes)\nSHA256 {digest}')
