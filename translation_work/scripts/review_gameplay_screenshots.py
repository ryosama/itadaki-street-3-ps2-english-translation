"""Read-only screenshot/ELF audit; creates review files, never a game patch.

Run from project root with Python 3.12 and -X utf8. Standard library only.
Screenshot descriptions were manually reviewed, not obtained by OCR.
Exact offsets are original ELF file offsets, NOT ISO offsets.
English entries are drafts; byte fit does not establish visual fit.
"""
import csv
import hashlib
import io
import json
import re
import struct
from pathlib import Path

from build_test_patch import EXPECTED_SHA, write_new_or_identical

OUT = Path('translation_work/phase8/screenshot_review')
SNAPS = Path('translation_work/phase4/pcsx2_data/snapshots')
BASE = Path('translation_work/phase7/revision3/patched/SLPM_621.12')
PRINTF = re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[diuoxXfFeEgGcs])')
COLORS = re.compile(r'/c\d')

# timestamp: screen, interpretation, related exact offsets (comma separated)
SCREENS = {
 '170711': ('Title', 'Japanese title artwork; no text replacement established', ''),
 '170745': ('Loading', 'No actionable menu text', ''),
 '170802': ('Dialogue', 'Empty dialogue box', ''),
 '170824': ('Welcome', 'English already visible', ''),
 '170848': ('Load result', 'Historical Japanese; already covered by phase6 save UI', ''),
 '170910': ('Main menu', 'Historical English width problem; phase5 font correction exists', ''),
 '171334': ('Loading', 'No actionable menu text', ''),
 '171346': ('Loading', 'No actionable menu text', ''),
 '171525': ('Welcome', 'English already visible', ''),
 '171546': ('Load result', 'Historical Japanese; already covered by phase6 save UI', ''),
 '171604': ('Main menu', 'English already visible', ''),
 '171627': ('Free Play', 'English already visible', ''),
 '171649': ('Player count', 'Historical long heading; shortened in phase7', ''),
 '174740': ('Title', 'Japanese title artwork; no text replacement established', ''),
 '174930': ('Rules', 'Historical Japanese; phase7 Rules now translated', ''),
 '174952': ('Main menu', 'English already visible', ''),
 '175013': ('Training', 'Historical Japanese; group selector translated in phase6', ''),
 '175015': ('Training', 'Duplicate Training screen', ''),
 '180311': ('Loading', 'No actionable menu text', ''),
 '180333': ('Main menu', 'English already visible', ''),
 '180356': ('Rules intro', 'English explanation; quit instruction subsequently translated', ''),
 '180435': ('Rules shop fees', 'English explanation visible', ''),
 '180647': ('Personal records', 'Japanese labels, rank suffixes, badge name', '0x363810-0x363ae8'),
 '180659': ('Top Ten selector', 'Japanese two-column list of ten ranking categories', '0x3602d0-0x360378'),
 '180709': ('Lessons records', 'Japanese lesson scores, rank and tutor approval labels', '0x363810-0x363ae8'),
 '180756': ('Map selector GP', 'Japanese map names; Itadaki Maps English label overflows', '0x3607e8'),
 '180802': ('Map selector base', 'Japanese map names: Candyland, Mermaid City, Rainforest, etc.', ''),
 '180825': ('Game setup', 'Japanese target, bankruptcy and casino labels; map/NPC names', ''),
 '180835': ('Map advice', 'Japanese description of beginner map and bank fork', '0x36ec38'),
 '180906': ('Turn announcement', 'Japanese player turn announcement', '0x34d7e0'),
 '180913': ('In-game turn menu', 'Six Japanese commands; stocks/assets/settings in right column', '0x34d228,0x34d250'),
 '180950': ('Loading', 'No actionable menu text', ''),
 '181009': ('Opponent selector', 'Historical two-line heading fixed in revision3; NPC biography Japanese', ''),
 '181148': ('Stop confirmation', 'Japanese stop question, Yes/No and shop value/fee', '0x36c3e8,0x36c358'),
 '181153': ('Buy confirmation', 'Japanese purchase question, Yes/No, shop and cash/stocks/total labels', '0x36c520,0x36c358,0x34e970,0x34e980,0x34e9a0'),
}

# Drafts prioritize gameplay. No font/layout edits, no new ELF are produced.
DRAFTS = {
 0x34D008:'Sell stock\n', 0x34D018:'Stocks',
 0x34D028:'Buy\n', 0x34D038:'Sell\n', 0x34D048:'Players',
 0x34D058:'Goal\n', 0x34D068:'Text speed\n', 0x34D078:'Sound\n',
 0x34D088:'Trading\n', 0x34D098:'Save & quit\n', 0x34D0A8:'Relief',
 0x34D0B8:'Mono\n', 0x34D0C8:'Stereo',
 0x34D0D8:'Trading ON\n', 0x34D0E8:'Trading OFF',
 0x34D0F8:'Before rolling,\n', 0x34D110:'you cannot save.',
 0x34D128:'You have\n', 0x34D138:'no stocks.',
 0x34D148:'The die was\n', 0x34D160:'rolled.',
 0x34D170:'Cannot sell now.', 0x34D188:'Cannot trade\n', 0x34D1A0:'now.',
 0x34D1B0:'After rolling,\n', 0x34D1C8:'no relief.',
 0x34D1D8:'You have\n', 0x34D1F0:'no tradable\n', 0x34D200:'shops.',
 0x34D218:'rebuildable\n',
 0x34D228:'Roll Stk\nShop Net\nMap  Opt',
 0x34D250:'/c1Roll /c0Stk\n/c1Shop /c0Net\nMap  Opt',
 0x34D7E0:"%s's turn", 0x34D828:'%d turns left',
 0x34DBC8:'Fee', 0x34DBD8:'Payment', 0x34DBF8:'Sale total',
 0x34DC08:'How many to buy?', 0x34DC20:'How many to sell?',
 0x34DDA0:'Yes\nNo\nNever\nView data',
 0x34DE60:'Cancel\nthis trade?',
 0x34DEE8:'Sell\nNo sale\nNever', 0x34DF08:'Buy\nNo buy\nNever',
 0x34DF90:'Stock up!', 0x34DFA0:'Stock down!',
 0x34E000:'Bid price', 0x34E100:'Board the boat?',
 0x34E1C0:'Buy a 2nd shop?', 0x34E1F8:'District',
 0x34E378:'Normal camera', 0x34E390:'Top view',
 0x34E840:'Value', 0x34E850:'Invest left',
 0x34E960:'Dividends', 0x34E970:'Cash%7dG',
 0x34E980:'Stk%7dG', 0x34E990:'Shop%7dG', 0x34E9A0:'Net%7dG',
 0x34E9B0:'Shops%6d', 0x34E9C0:'Stocks%6d',
 0x36C358:'Yes\nNo', 0x36C3E8:'Stop here?',
 0x36C400:'Build what?', 0x36C418:'Invest here?',
 0x36C428:'Limit: %3dG\nInvest how much?',
 0x36C458:'Not enough cash\nor stocks\nto invest!',
 0x36C480:'Invest\nStocks\nCancel',
 0x36C4A8:'No shops\nto invest in!',
 0x36C4C8:'Buy out this shop\nfor 5x its value.',
 0x36C4F8:'Buy for %dG\nat 5x value?',
 0x36C520:'Buy this\nfor %dG?',
 0x36C660:'Still buy\nfor %dG?', 0x36C680:'Cancel buying\nthis shop?',
 0x36C760:'/c2Not enough cash!/c0',
 0x36C778:'Sell stocks\nSell shop',
 0x36C790:'Choose a shop\nto auction.',
 0x36C7B8:'Choose a shop\nto buy.',
 0x36C7D8:'Choose a shop\nto reserve.',
 0x36C800:'Choose a shop\nto sell.',
 0x36C858:'Choose a shop\nto rebuild.',
 0x36C880:'Choose\nyour shop.',
 0x36C8A0:"Choose the\nother player's shop.",
 0x36C8C0:'Choose a shop\nto invest in.',
 0x36C8E0:'Choose\na destination.',
 0x36C900:'Cancel moving?', 0x36C9F0:'Cannot invest\nany more.',
 0x36CA48:'No shops for sale.',
 0x369160:'Bank', 0x369170:'Spade', 0x369180:'Chance',
 0x369190:'Lucky', 0x3691A0:'Stock exchange', 0x3691B8:'Dice shop',
 0x3691C8:'Switch', 0x3691D8:'Stairs', 0x3691E8:'Zoo',
 0x3691F8:'Heliport', 0x369208:'Tax office', 0x369218:'Toll gate',
 0x369228:'Theme park', 0x369238:'Realty', 0x369248:'Home',
 0x3692A8:'Goal %dG\nBankrupt limit %d',
 0x3692C8:'Set the message\ndisplay speed.',
 0x3692F0:'Switch between\nstereo and mono.',
 0x369320:'Automatically refuse\ntrade offers from\ncomputer players.\n',
 0x369370:'Save your game\nand quit.',
 0x3607E8:'Ita Maps',
 0x363820:'Max rent in', 0x363830:'Max rent paid',
 0x363840:'Rent received', 0x363850:'Rent paid',
 0x363860:'Busts', 0x363870:'Busts caused',
 0x363880:'Stock gain', 0x363890:'Max value',
 0x3638A0:'Points %d.%d', 0x3638B0:'Rank %2d',
 0x3638C0:'Maharaja badges',
 0x363948:'Map', 0x363958:'From', 0x363968:'Rent in',
 0x363978:'Rent paid', 0x363988:'Maharaja', 0x363998:'Rank',
 0x363A10:'Skill rank', 0x363A50:'Female tutor', 0x363A68:'Male tutor',
 0x361CF8:'Goal        %d', 0x361D10:'Bust limit  %s',
 0x361D28:'Casino      %s',
 0x3B8A88:'Fee', 0x3B8AB8:'Base', 0x3B8AC0:'Sale',
 0x3B8AC8:'Owner', 0x3B8AD0:'Cost', 0x3B8AF8:'Cash',
 0x3B8B00:'St', 0x3B8B08:'Shop', 0x3B8B10:'Net', 0x3B8B20:'Lap%d',
 0x3B99E8:'Games', 0x3B9AA8:'Lessons', 0x3B9AB0:'Best', 0x3B9AC0:'Mean',
}

RANGES = [
 (0x34CF40,0x34D6F0,'turn menus/settings'),
 (0x34D7E0,0x34D8B0,'turn/salary'),
 (0x34DB60,0x34E450,'stock/trade/events/camera'),
 (0x34E840,0x34E9D0,'finance labels'),
 (0x36C330,0x36CB48,'property decisions'),
 (0x369160,0x369470,'square names/settings help'),
 (0x3602D0,0x360378,'ranking selector'),
 (0x363810,0x363AE8,'records/lessons'),
 (0x361CF8,0x361D50,'setup summary'),
 (0x3B8A88,0x3B8B30,'property/wealth popup'),
 (0x3B99E8,0x3B9AF0,'records units and scores'),
]

def csv_bytes(rows):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')

def main():
    source=Path('decompile/SLPM_621.12')
    original=source.read_bytes(); base=BASE.read_bytes()
    assert hashlib.sha256(original).hexdigest()==EXPECTED_SHA
    assert hashlib.sha256(base).hexdigest()=='9b297f21d71c86719ca7f2a3e37d53fff765a17103841e144e2e703404e981c1'
    inventory=[]
    for path in sorted(SNAPS.glob('*.png')):
        stamp=path.stem[-6:]
        screen,status,offsets=SCREENS.get(stamp,('Unreviewed','New screenshot requires visual review',''))
        inventory.append(dict(file=path.name,timestamp=stamp,screen=screen,observation=status,
                              related_offsets=offsets,bytes=path.stat().st_size,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    offsets={off:'English layout correction' for off in DRAFTS}
    for start,end,group in RANGES:
        for off in range(start,end):
            if original[off] and original[off-1]==0:
                raw=original[off:original.index(b'\0',off)]
                try: text=raw.decode('cp932')
                except UnicodeDecodeError: continue
                if text and all(c.isprintable() or c in '\n\u3000' for c in text) and any(ord(c)>127 for c in text):
                    offsets[off]=group
    # Search visual transcriptions exactly, not random byte-to-text decoding.
    visual_matches=[]
    for text in ['目標金額','破産人数','カジノの設定','しょうてん','買物料',
                 'おかしのくに','イタロー','あゆみ','つらら','%d周目',
                 '最高点','平均点','さからった回数','授業数','試合数']:
        needle=text.encode('cp932'); start=0; matches=[]
        while (off:=original.find(needle,start))>=0:
            matches.append(hex(off)); start=off+1
        visual_matches.append(dict(japanese=text,original_file_matches=matches,
                                   caveat='substring matches; not necessarily allocation starts or runtime consumers'))
    references={off+0xFF000:[] for off in offsets}
    for pos in range(0,len(original)-3,4):
        value=struct.unpack_from('<I',original,pos)[0]
        if value in references: references[value].append(hex(pos))
    records=[]
    for off,group in sorted(offsets.items()):
        end=original.index(b'\0',off)+1
        raw=original[off:end]; japanese=raw[:-1].decode('cp932')
        current=base[off:end].split(b'\0')[0].decode('cp932')
        english=DRAFTS.get(off,'')
        required=len(english.encode('ascii'))+1 if english else 0
        controls_ok=(PRINTF.findall(japanese)==PRINTF.findall(english)
                     and COLORS.findall(japanese)==COLORS.findall(english)) if english else None
        # Trailing newlines mark concatenated fragments; never silently remove them.
        newline_ok=(japanese.endswith('\n')==english.endswith('\n')) if english else None
        records.append(dict(offset=hex(off),virtual_address=hex(off+0xFF000),group=group,
                            japanese=japanese,current_phase7=current,english_draft=english,
                            capacity=len(raw),required_bytes=required,
                            fits_original_allocation=required<=len(raw) if english else None,
                            formatting_tokens_match=controls_ok,trailing_newline_matches=newline_ok,
                            pointer_locations=','.join(references[off+0xFF000]),
                            original_hex=raw.hex(),
                            status='draft; no patch applied; layout/context review needed' if english
                            else 'Japanese candidate; translation pending'))
    assert source.read_bytes()==original and BASE.read_bytes()==base
    write_new_or_identical(OUT/'snapshot_inventory.csv',csv_bytes(inventory))
    write_new_or_identical(OUT/'visual_string_matches.json',
                          (json.dumps(visual_matches,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    write_new_or_identical(OUT/'gameplay_text_candidates.csv',csv_bytes(records))
    write_new_or_identical(OUT/'gameplay_text_candidates.json',
                          (json.dumps(records,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    counts=dict(screenshots=len(inventory),unreviewed=sum(r['screen']=='Unreviewed' for r in inventory),
                candidates=len(records),english_drafts=sum(bool(r['english_draft']) for r in records),
                oversized_drafts=[r['offset'] for r in records if r['fits_original_allocation'] is False],
                token_mismatches=[r['offset'] for r in records if r['formatting_tokens_match'] is False],
                newline_mismatches=[r['offset'] for r in records if r['trailing_newline_matches'] is False])
    write_new_or_identical(OUT/'audit_counts.json',(json.dumps(counts,indent=2)+'\n').encode())
    print(json.dumps(counts,indent=2))

if __name__=='__main__': main()
