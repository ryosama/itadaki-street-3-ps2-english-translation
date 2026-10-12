"""Read-only exact matching of manually reviewed phase10 screenshot text."""
from pathlib import Path
import json
from build_test_patch import digest,EXPECTED_SHA,encode_json,write_new_or_identical

OUT=Path('translation_work/phase10/analysis')
QUERIES={
 '190016':'', '190058':'マーメイドシティ', '190102':'ムーンライトクルーズ',
 '190132':'ひとり', '190154':'進む方向を決めるときは', '190158':'4つのマークを そろえて',
 '190202':'最初のうちは', '190218':'シャーベット工房',
 '190234':'いよいよ 出発ね', '190238':'ちなみに はじめのうちは',
 '190242':'わたしがオススメする', '190254':'そこって',
 '190301':'色が ついてないお店は', '190305':'お金があれば そこを',
 '190309':'たくさん お店があると', '190318':'あいてて よかった',
 '190402':'このマップは 一方通行で', '190405':'必要なことは そのつど',
 '190436':'しゅうかい', '190450':'メッセージの 表示の速さを',
 '190456':'最初は 遅めにして', '190509':'ステレオと モノラルとを',
 '190512':'あなたのテレビにあわせて', '190518':'交換とか 買い取りとか',
 '190523':'ちなみに わたしは', '190542':'ここは【ラッキー】と',
 '190545':'みなさん どんどん', '190551':'ラッキーチャンス!!'
}
def main():
 b=Path('decompile/SLPM_621.12').read_bytes(); assert digest(b)==EXPECTED_SHA
 tables=json.loads(Path('translation_work/phase9/revision1/tutor_table_inventory.json').read_text(encoding='utf-8'))
 result=[]; events=set()
 for path in sorted(Path('translation_work/phase10/screenshots_before_translation').glob('*.png')):
  stamp=path.stem[-6:]; query=QUERIES[stamp]; matches=[]
  if query:
   raw=query.encode('cp932'); pos=0
   while (off:=b.find(raw,pos))>=0:
    start=b.rfind(b'\0',0,off)+1; end=b.index(b'\0',off)
    try: text=b[start:end].decode('cp932')
    except UnicodeDecodeError: text=None
    linked=[r for r in tables if r['text_offset']==start]
    for r in linked: events.add(r['event'])
    matches.append(dict(offset=start,offset_hex=hex(start),japanese=text,
                        tutor_events=[dict(gender=r['gender'],event=r['event'],page=r['page']) for r in linked]))
    pos=off+1
  result.append(dict(file=path.name,sha256=digest(path.read_bytes()),query=query,matches=matches))
  print(stamp,repr(query),[(r['offset_hex'],r['japanese']) for r in matches[:5]])
 selected=[r for r in tables if r['event'] in events]
 write_new_or_identical(OUT/'screenshot_matches.json',encode_json(result))
 write_new_or_identical(OUT/'paired_tutor_pages.json',encode_json(selected))
 for r in selected: print(r['gender'],r['event'],hex(r['text_offset']),repr(r['japanese']))
 # Literal map names are in an ELF data region, distinct from MAP names.
 for start,stop in [(0x1c6ee0,0x1c7110),(0x3b8620,0x3b8740),(0x3b8978,0x3b89e0)]:
  print('DATA',hex(start))
  for o in range(start,stop):
   if b[o] and b[o-1]==0:
    try:s=b[o:b.index(b'\0',o)].decode('cp932')
    except UnicodeDecodeError:continue
    if all(c.isprintable() or c in '\n\u3000' for c in s):print(hex(o),repr(s))

if __name__=='__main__':main()
