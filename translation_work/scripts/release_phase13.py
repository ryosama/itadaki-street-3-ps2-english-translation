"""Create and independently verify the cumulative v13 ISO BPS."""
from pathlib import Path
from release_phase9 import main

if __name__ == '__main__':
    main(build=Path('translation_work/phase13/revision3'),out=Path('translation_work/release/english_v13'),
         manifest_name='phase13_manifest.json',
         base_path=Path('translation_work/phase12/revision1/patched/SLPM_621.12'))
