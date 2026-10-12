"""Create a deterministic, patch-only release ZIP and SHA256SUMS under work/."""
import hashlib
import io
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'translation_work/scripts'))
from build_test_patch import write_new_or_identical

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    patch_name='Itadaki_Street_3_English_v13.bps'
    files={patch_name:(ROOT/'patches/v13'/patch_name).read_bytes(),
           'README.md':(ROOT/'docs/RELEASE_v13.md').read_bytes(),
           'release_manifest.json':(ROOT/'patches/v13/release_manifest.json').read_bytes()}
    if sha(files[patch_name])!='f485955a9257b69fa9e303787227b443bc0773aeb046662298836bfdeb1d442d':
        raise ValueError('unexpected v13 patch')
    sums=''.join(f'{sha(raw)}  {name}\n' for name,raw in sorted(files.items()))
    files['SHA256SUMS.txt']=sums.encode('ascii')
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,raw in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,12,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
            archive.writestr(info,raw)
    out=ROOT/'work/release';bundle='Itadaki_Street_3_English_v13.zip'
    raw=buffer.getvalue();write_new_or_identical(out/bundle,raw)
    public_sums=f'{sha(files[patch_name])}  {patch_name}\n{sha(raw)}  {bundle}\n'
    write_new_or_identical(out/'SHA256SUMS.txt',public_sums.encode('ascii'))
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if set(archive.namelist())!=set(files):raise ValueError('unexpected release ZIP member')
        for name,payload in files.items():
            if archive.read(name)!=payload:raise ValueError('ZIP roundtrip failed')
    print(public_sums,end='');print('Release ZIP contains only BPS, README, manifest and checksums.')

if __name__=='__main__':main()
