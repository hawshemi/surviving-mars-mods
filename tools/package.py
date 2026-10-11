from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lupa import LuaRuntime
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root / 'tools/check.py')], check=True)
lua = LuaRuntime()
lua.execute('''
function PlaceObj(class, values)
 local obj={class=class}
 for i=1,#values,2 do obj[values[i]]=values[i+1] end
 return obj
end
''')
destination = root / 'dist'
destination.mkdir(exist_ok=True)
for project in sorted((root / 'mods').iterdir()):
    mod = project / 'mod'
    metadata = lua.execute((mod / 'metadata.lua').read_text(encoding='utf-8'))
    version = f"{metadata['version_major']}.{metadata['version_minor']:02d}-{metadata['version']:03d}"
    archive_path = destination / f"{metadata['id']}-{version}.zip"
    files = sorted(path for path in mod.rglob('*') if path.is_file())
    with ZipFile(archive_path, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, metadata['id'] + '/' + path.relative_to(mod).as_posix())
    with ZipFile(archive_path) as archive:
        assert archive.testzip() is None
        assert len(archive.namelist()) == len(files)
        for path in files:
            assert archive.read(metadata['id'] + '/' + path.relative_to(mod).as_posix()) == path.read_bytes()
    print(archive_path.name)
