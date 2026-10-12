"""Create and independently verify cumulative v12 BPS (both title textures)."""
from pathlib import Path
from release_phase9 import main

if __name__=='__main__':
 main(build=Path('translation_work/phase12/revision1'),out=Path('translation_work/release/english_v12'),
      manifest_name='phase12_manifest.json',
      base_path=Path('translation_work/phase11/revision1/patched/SLPM_621.12'))
