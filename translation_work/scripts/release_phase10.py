"""Package and independently verify the v10 cumulative ISO patch."""
from pathlib import Path
from release_phase9 import main

if __name__=='__main__':
 main(build=Path('translation_work/phase10/revision2'),out=Path('translation_work/release/english_v10'),
      manifest_name='phase10_manifest.json',
      base_path=Path('translation_work/phase9/revision1/patched/SLPM_621.12'))
