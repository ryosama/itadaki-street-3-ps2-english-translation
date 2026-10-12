"""Read-only linkage of 31 manually inspected screenshots to CP932 ELF text."""
import hashlib
import json
from pathlib import Path
from build_test_patch import EXPECTED_SHA, encode_json, write_new_or_identical

OUT=Path('translation_work/phase9/analysis')
QUERIES=[
 ('182339','Tutor player selection','だれが 遊びますか'),
 ('182420','Setup; Settings overflow','カジノの設定'),
 ('182428','Candyland advice','シンプルな入門用マップ'),
 ('182500','Male tutor introduction','やあ はじめまして'),
 ('182527','Board overview; no dialogue',''),
 ('182606','Tutor: roll and move','まずはサイコロを振って'),
 ('182617','Tutor: inspect map','ここでは このマップ全体を'),
 ('182621','Tutor: plan before rolling','サイコロを振る前に'),
 ('182626','Bank square help','マークを集めて来ると'),
 ('182638','Shop name and type','マフィン観光'),
 ('182641','Club square help','クローバーマークを'),
 ('182647','Chance square help','チャンスカードを'),
 ('182700','Shop menu auction/exchange/rebuild','競売'),
 ('182712','Tutor: negotiate buying a shop','ほかの人が持ってるお店を'),
 ('182716','Tutor: offer price','買いたいお店を指定して'),
 ('182727','District stock table and tutor','ここでは みんながどの株を'),
 ('182748','Asset menu and Players overflow','資産表'),
 ('182753','Tutor: own asset table; values overflow','この表では キミの現在の'),
 ('182757','Tutor: check assets periodically','自分のおかれた状況を'),
 ('182806','All-player assets and tutor','ここでは 全員の資産表を'),
 ('182814','Settings submenu overflows; tutor label','家庭教師設定'),
 ('182819','Tutor: check victory conditions','このコマンドを選ぶと'),
 ('182828','Tutor settings description','家庭教師の おしえかたを'),
 ('182836','Tutor: start playing','いよいよ勝負開始だね'),
 ('182840','Tutor: die maximum depends on board','ちなみに マップしだいで'),
 ('182851','Tutor: first suit','よーし マーク1つゲット'),
 ('182904','Tutor: surprise card result','引いた結果'),
 ('182911','Tutor: card effects vary','チャンスカードをひくと'),
 ('182920','Tutor: buy stocks with card 67','高くっても'),
 ('182941','Stock-price rise; district name and stock count','ストロベリタウン'),
 ('182947','Tutor: profit','今回 多少は'),
]
EXTRA=['雷門ひかる','家庭教師','ストロベリタウン','チェリーレイク','ノースメロン',
       'サウスオレンジ','ろてん','ぞうしあまり','おみせかかく','かいものりょう',
       'ねだん','けっか','おかしのくに']

def main():
 source=Path('decompile/SLPM_621.12'); b=source.read_bytes()
 assert hashlib.sha256(b).hexdigest()==EXPECTED_SHA
 records=[]; texts={q for _,_,q in QUERIES if q}|set(EXTRA)
 for query in sorted(texts):
  raw=query.encode('cp932'); pos=0; matches=[]
  while (off:=b.find(raw,pos))>=0:
   start=b.rfind(b'\0',0,off)+1; end=b.index(b'\0',off)
   try: text=b[start:end].decode('cp932')
   except UnicodeDecodeError: text=None
   matches.append(dict(match_offset=off,match_offset_hex=hex(off),start=start,
                       start_hex=hex(start),capacity=end-start+1,text=text))
   pos=off+1
  records.append(dict(query=query,matches=matches))
 shots=[]
 for path in sorted(Path('translation_work/phase9/screenshots_before_translation').glob('*.png')):
  stamp=path.stem[-6:]; row=next((r for r in QUERIES if r[0]==stamp),None)
  assert row, 'new screenshot needs review'
  shots.append(dict(file=path.name,screen=row[1],query=row[2],sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 assert len(shots)==31
 write_new_or_identical(OUT/'screenshot_inventory.json',encode_json(shots))
 write_new_or_identical(OUT/'visual_matches.json',encode_json(records))
 for r in records:
  print(repr(r['query']),[(m['start_hex'],m['text']) for m in r['matches'][:5]])

if __name__=='__main__': main()
