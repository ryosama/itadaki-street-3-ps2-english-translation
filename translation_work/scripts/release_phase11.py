"""Create and independently verify the cumulative v11 BPS (ELF, MAPs, title)."""
from pathlib import Path
from release_phase9 import main

if __name__=='__main__':
 main(build=Path('translation_work/phase11/revision1'),out=Path('translation_work/release/english_v11'),
      manifest_name='phase11_manifest.json',
      base_path=Path('translation_work/phase10/revision2/patched/SLPM_621.12'))
