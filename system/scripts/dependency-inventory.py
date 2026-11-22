from pathlib import Path
import json, zipfile, io
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
rows=[]
lock=json.loads((root/'frontend/package-lock.json').read_text(encoding='utf-8'))
for location,entry in lock['packages'].items():
    if not location: continue
    metadata=root/'frontend'/location/'package.json'
    if metadata.exists():
        p=json.loads(metadata.read_text(encoding='utf-8'))
        rows.append(('npm',p.get('name',location),p.get('version',''),str(p.get('license','见包内LICENSE/NOTICE'))))
with zipfile.ZipFile(root/'backend/target/instrumenthub-1.0.0.jar') as app:
    for name in app.namelist():
        if not name.startswith('BOOT-INF/lib/') or not name.endswith('.jar'):continue
        license_names=[]
        with zipfile.ZipFile(io.BytesIO(app.read(name))) as lib:
            for pom in lib.namelist():
                if pom.startswith('META-INF/maven/') and pom.endswith('/pom.xml'):
                    try:
                        tree=ET.fromstring(lib.read(pom))
                        license_names += [n.text or '' for n in tree.findall('{*}licenses/{*}license/{*}name')]
                    except ET.ParseError: pass
        rows.append(('JVM',Path(name).name,'包含在JAR文件名中','；'.join(sorted(set(license_names))) or '见库内LICENSE/NOTICE和上游POM'))
lines=['# 第三方依赖清单','', '本清单从本次安装的npm包元数据与可运行JAR中的Maven元数据生成。许可证名称按上游元数据列示；完整条款以随库LICENSE/NOTICE和发行版声明为准。Docker镜像的发行条款须另行核对，本清单不替代部署方的许可证审查。','', '| 生态 | 包 | 版本 | 声明的许可证 |','|---|---|---|---|']
for row in sorted(set(rows)):lines.append('| '+' | '.join(v.replace('|','/') for v in row)+' |')
(root/'docs/DEPENDENCIES.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(f'{len(rows)} dependency entries recorded')
