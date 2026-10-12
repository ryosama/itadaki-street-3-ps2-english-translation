"""Check public files, patch/PNG hashes, README links and sensitive exclusions.

Audits Git tracked files plus nonignored publication files; excludes .git/work.
Read-only. Uses no network or third-party dependencies.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
ALLOWED={'.py','.md','.json','.csv','.png','.bps','.yml','.yaml'}
SPECIAL={'.gitignore','.gitattributes'}
PRIVATE={'.git','work','__pycache__','.venv'}

def main():
    files=[]
    for p in ROOT.rglob('*'):
        relative=p.relative_to(ROOT)
        if any(part in PRIVATE for part in relative.parts) or not p.is_file():continue
        if p.is_symlink():raise ValueError(f'public symlink: {relative}')
        files.append(p)
    cmd=['git','-c',f'safe.directory={ROOT.as_posix()}','ls-files','-z']
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,check=True)
    tracked=[ROOT/p for p in result.stdout.decode('utf-8').split('\0') if p]
    for p in set(files+tracked):
        r=p.relative_to(ROOT)
        if any(x in PRIVATE for x in r.parts):raise ValueError(f'private tracked file: {r}')
        if p.suffix.lower() not in ALLOWED and p.name not in SPECIAL:raise ValueError(f'unsupported public file: {r}')
        if p.name.lower().startswith(('apply','scph')):raise ValueError(f'private/applier file: {r}')
        if p.suffix.lower() in {'.py','.md','.json','.csv','.yml','.yaml'}:
            text=p.read_text(encoding='utf-8-sig')
            if re.search(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',text):
                raise ValueError(f'possible secret: {r}')
        if p.stat().st_size>10*1024*1024:raise ValueError(f'oversized public file: {r}')
    recipe=json.loads((ROOT/'data/v13_recipe.json').read_text(encoding='utf-8'))
    for item in recipe['title_pngs']:
        p=ROOT/item['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('title PNG mismatch')
    patch=ROOT/'patches/v13/Itadaki_Street_3_English_v13.bps'
    if hashlib.sha256(patch.read_bytes()).hexdigest()!=recipe['patch_sha256']:raise ValueError('BPS mismatch')
    for p in files:
        if p.suffix!='.md' or p.parent not in {ROOT,ROOT/'docs'}:continue
        text=p.read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if ':' in link or link.startswith('#'):continue
            target=link.split('#')[0]
            if target and not (p.parent/target).exists():raise ValueError(f'broken link: {p.name}: {link}')
    print(json.dumps(dict(status='PASS',public_files=len(files),tracked_files=len(tracked),
                          bytes=sum(p.stat().st_size for p in files),iso_bios_runtime_appliers_excluded=True),indent=2))

if __name__=='__main__':main()
