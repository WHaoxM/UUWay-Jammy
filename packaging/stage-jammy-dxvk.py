"""Copy only two PE DLLs and their license from the matching upstream build."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'config/jammy-dxvk-bootstrap.json'
PE_FILES = ('d3d11.dll', 'dxgi.dll')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    spec = json.loads(REFERENCE.read_text(encoding='utf-8'))
    for source, expected in spec['inputs'].items():
        if digest(ROOT / source) != expected.lower():
            raise SystemExit(f'DXVK build input changed: {source}; rebuild the PE DLLs on Ubuntu 24.04')
    with tempfile.TemporaryDirectory(prefix='dxvk-jammy-') as temporary:
        work = Path(temporary)
        archive = work / 'reference.deb'
        subprocess.run(['curl', '--fail', '--location', '--proto', '=https', '--retry', '3',
                        '--max-time', '180', '-o', str(archive), spec['url']], check=True)
        if digest(archive) != spec['sha256']:
            raise SystemExit('Upstream DXVK reference package checksum mismatch')
        tree = work / 'extracted'
        subprocess.run(['dpkg-deb', '--extract', str(archive), str(tree)], check=True)
        source = tree / 'usr/lib/uuway/build/dxvk-capture/stage'
        for name in PE_FILES:
            if not (source / name).read_bytes().startswith(b'MZ'):
                raise SystemExit(f'Expected a PE DLL: {name}')
        stage = ROOT / 'build/dxvk-capture/stage'
        stage.mkdir(parents=True, exist_ok=True)
        for name in (*PE_FILES, 'DXVK_LICENSE'):
            shutil.copyfile(source / name, stage / name)


if __name__ == '__main__':
    main()
