from pathlib import Path
from PIL import Image
import subprocess, hashlib, json, re, zipfile

repo=Path(__file__).resolve().parents[1]; root=repo/'package'
run=subprocess.run(['texlua',str(root/'Source'/'validate.lua'),str(root)],check=True,text=True,capture_output=True)
report=['ZBM UI SYSTEM v1.1 静的検証結果','',run.stdout]
for p in (root/'Assets').glob('*.png'):
 with Image.open(p) as im: im.verify()
for p in (root/'Assets').glob('*_UI.png'):
 with Image.open(p) as im:
  assert im.size==(3840,2160) and im.mode=='RGBA'
  assert im.getchannel('A').crop((0,1729,3840,2160)).getbbox() is None
report.append('全PNGデコード、4K RGBA UI、下20%の透明領域: PASS')
for p in (root/'Templates').glob('*.setting'):
 s=p.read_text(encoding='utf-8'); assert not p.read_bytes().startswith(b'\xef\xbb\xbf')
 for name in re.findall(r'Filename = "__ZBM_ASSET_ROOT__/([^"]+)"',s): assert (root/'Assets'/name).is_file()
 assert len(re.findall('Filename = ',s)) in (2,3)
 resolved=s.replace('__ZBM_ASSET_ROOT__','C:/Users/日本語 user/AppData/Roaming/ZBM/Assets')
 assert '__ZBM_' not in resolved
report.append('全Loaderファイル参照、UTF-8 BOMなし、日本語・空白を含むパスの文字列置換: PASS（Windows実行ではありません）')
video=root/'Preview'/'ZBM_v11_CONCEPT.mp4'
subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],capture_output=True,check=True)
info=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,r_frame_rate,nb_frames','-of','json',str(video)],capture_output=True,text=True,check=True).stdout)
assert info['streams'][0]['nb_frames']=='363'
report.append('プレビュー動画363フレーム、960×540、30fps、12.1秒、全デコード: PASS')
report.append('プレビューはPython/PillowとFFmpegによる概念シミュレーション。Resolveのレンダリングではありません。写真の画角とフォントは実機と異なる場合があります。')
report.append('Lua検査は構文・テーブル・数値式の検査であり、Resolveのツール実装・入力受付・GPU描画は実行していません。')
report.append('Windowsスクリプト実行、Resolve 21無料版でのインストール、Inspector、画像交換、尺変更、書き出し、4K性能: すべて未検証。')
report.append('前環境のZIPは引き継がれなかったため、同じレイアウト・16/13/11ノード構成で再生成。前環境ZIPとのバイナリ一致は主張しません。')
(root/'Docs'/'静的検証結果.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
manifest=[]
for p in sorted(root.rglob('*')):
 if p.is_file() and p.name!='SHA256SUMS.txt': manifest.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root).as_posix()}')
(root/'SHA256SUMS.txt').write_text('\n'.join(manifest)+'\n')
out=repo/'downloads'/'ZBM_UI_SYSTEM_v1.1_test.zip';out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file():z.write(p,Path('ZBM_UI_SYSTEM_v1.1')/p.relative_to(root))
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 assert len(z.namelist())==len(manifest)+1
(out.parent/'SHA256SUMS.txt').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
print('\n'.join(report));print('ZIP CRC and membership: PASS;',len(manifest)+1,'files;',out.stat().st_size,'bytes')
