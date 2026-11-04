"""Build v1.1 from the supplied v1.0 archive; Python 3 + Pillow + FFmpeg + texlua."""
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, ImageOps
import argparse, json, zipfile, shutil, re, subprocess, hashlib

p=argparse.ArgumentParser(); p.add_argument('v10_zip'); args=p.parse_args()
REPO=Path(__file__).resolve().parents[1]; ROOT=REPO/'package'; ROOT.mkdir(exist_ok=True)
for d in ['Templates','Assets','Preview','Docs','Source']: (ROOT/d).mkdir(exist_ok=True)
REF=REPO.parent/'zbm_reference_review'; REF.mkdir(exist_ok=True)
with zipfile.ZipFile(args.v10_zip) as z:
 for name in z.namelist(): assert (REF/name).resolve().is_relative_to(REF.resolve())
 z.extractall(REF)
W,H=3840,2160
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
CFG={
 'COMPARISON':dict(panel=(.06,.20,.94,.85),slots=[(.085,.31,.48,.81),(.52,.31,.915,.81)],texts=[('LeftLabel','改修前',(.2825,.255),.019),('RightLabel','改修後',(.7175,.255),.019)]),
 'REFERENCE':dict(panel=(.08,.20,.92,.85),slots=[(.105,.31,.50,.81)],texts=[('Description','形状のバランスを確認\n\n肩と胴体のつながりを見ながら、\n少しずつ形を整えます。',(.715,.59),.018),('Credit','出典：ここに記入（任意）',(.715,.265),.012)]),
 'DETAIL':dict(panel=(.14,.20,.86,.85),slots=[(.165,.31,.835,.81)],texts=[('Caption','表面の質感とエッジの仕上げ',(.50,.255),.018)])}
def box(b,w=W,h=H):
 x0,y0,x1,y1=b; return tuple(round(v) for v in (x0*w,(1-y1)*h,x1*w,(1-y0)*h))
for kind,c in CFG.items():
 im=Image.new('RGBA',(W,H)); d=ImageDraw.Draw(im)
 d.rectangle(box(c['panel']),fill=(30,44,46,245))
 x0,y0,x1,y1=c['panel']; d.rectangle(box((x0+.015,y1-.005,x1-.015,y1-.003)),fill=(121,174,179,210))
 if kind in ('COMPARISON','REFERENCE'):
  x=.5 if kind=='COMPARISON' else .525; d.rectangle(box((x-.0005,.31,x+.0005,.805)),fill=(94,142,146,180))
 for slot in c['slots']: d.rectangle(box(slot),fill=(43,63,66,255))
 im.save(ROOT/'Assets'/f'{kind}_UI.png')
for name,src,b in [('sample_left.png','COMPARISON_STILL.jpg',(102,180,470,377)),('sample_right.png','COMPARISON_STILL.jpg',(491,180,874,377)),('sample_detail.png','DETAIL_STILL.jpg',(170,179,788,388))]:
 im=Image.open(REF/'Preview'/src).crop(b).convert('RGB')
 ImageOps.pad(im,(1600,1000),color='#2B3F42').save(ROOT/'Assets'/name)
q=lambda x:json.dumps(x,ensure_ascii=False)
def val(x):
 if isinstance(x,str): return q(x)
 if isinstance(x,(tuple,list)): return '{ '+', '.join(map(val,x))+' }'
 return str(x)
class Expr(str): pass
class Link(str): pass
def inp(x):
 if isinstance(x,Expr): return 'Input { Expression = '+q(str(x))+', }'
 if isinstance(x,Link): return 'Input { SourceOp = '+q(str(x))+', Source = "Output", }'
 return 'Input { Value = '+val(x)+', }'
def make(kind):
 nodes={};pub=[]
 def node(name,typ,ins=None,extra=''): nodes[name]=(typ,ins or {},extra)
 def expose(name,src,label,page='Controls',port=''):
  pub.append(f'{name} = InstanceInput {{ SourceOp = {q(src)}, Source = {q(port or name)}, Name = {q(label)}, Page = {q(page)}, }},')
 def progress(delay,duration):
  a=f'math.max(0,math.min(1,((time-comp.RenderStart)/Controls.NumberIn1-{delay})/{duration}))'
  b='math.max(0,math.min(1,(comp.RenderEnd-time)/Controls.NumberIn1/0.18))'
  return Expr(f'({a})*({b})')
 node('Controls','CustomTool',{'NumberIn1':30},'UserControls = ordered() { NumberIn1 = { LINKS_Name = "Timeline FPS", LINKID_DataType = "Number", INPID_InputControl = "SliderControl", INP_Default = 30, INP_MinScale = 23.976, INP_MaxScale = 60, ICS_ControlPage = "Controls", }, },')
 expose('FPS','Controls','タイムラインFPS（必ず一致）',port='NumberIn1')
 node('Canvas','Background',{'UseFrameFormatSettings':0,'Width':W,'Height':H,'TopLeftAlpha':0})
 def loader(name,filename):
  node(name,'Loader',{'GlobalIn':0,'GlobalOut':100000,'Loop':1},f'Clips = {{ Clip {{ ID = "Clip1", Filename = {q(filename)}, FormatID = "PNGFormat", StartFrame = -1, Length = 1, LengthSetManually = true, TrimIn = 0, TrimOut = 0, ExtendFirst = 0, ExtendLast = 100000, Loop = 1, GlobalStart = 0, GlobalEnd = 100000, }}, }},')
 def mask(name,b,p):
  x0,y0,x1,y1=b
  node(name,'RectangleMask',{'Width':Expr(f'{x1-x0}*({p})'),'Height':y1-y0,'Center':Expr(f'Point({x0}+{(x1-x0)/2}*({p}),{(y0+y1)/2})'),'SoftEdge':0})
 def merge(name,bg,fg,maskname=None,**kw):
  ins={'Background':Link(bg),'Foreground':Link(fg),**kw}
  if maskname: ins['EffectMask']=Link(maskname)
  node(name,'Merge',ins); return name
 loader('Artwork',f'__ZBM_ASSET_ROOT__/{kind}_UI.png')
 mask('PanelReveal',CFG[kind]['panel'],progress(0,.20))
 last=merge('Panel','Canvas','Artwork','PanelReveal')
 for i,b in enumerate(CFG[kind]['slots']):
  nm='Image'+str(i+1)
  sample='sample_detail.png' if kind=='DETAIL' else ('sample_left.png' if i==0 else 'sample_right.png')
  loader(nm,f'__ZBM_ASSET_ROOT__/{sample}')
  expose('File'+str(i+1),nm,f'画像{i+1}を選択（静止画）','Images','Clip')
  mask(nm+'Reveal',b,progress(.12+i*.06,.26))
  x0,y0,x1,y1=b; last=merge(nm+'Place',last,nm,nm+'Reveal',Center=((x0+x1)/2,(y0+y1)/2),Size=1)
  expose('Position'+str(i+1),last,f'画像{i+1}の位置','Images','Center')
  expose('Zoom'+str(i+1),last,f'画像{i+1}の倍率','Images','Size')
 for nm,txt,pos,size in CFG[kind]['texts']:
  node(nm,'TextPlus',{'UseFrameFormatSettings':0,'Width':W,'Height':H,'StyledText':txt,'Font':'Yu Gothic','Style':'Regular','Size':size,'Center':pos,'Red1':220/255,'Green1':231/255,'Blue1':230/255,'Alpha1':progress(.31,.19),'HorizontalJustificationNew':3,'VerticalJustificationNew':3})
  for port,label in [('StyledText','文字'),('Size','文字サイズ'),('Font','フォント')]: expose(nm+port,nm,nm+' / '+label,'Text',port)
  last=merge(nm+'Composite',last,nm)
 node('UI_Position','Transform',{'Input':Link(last),'Center':(.5,.5),'Size':1})
 expose('UIPosition','UI_Position','UI全体の位置','Layout','Center'); expose('UIScale','UI_Position','UI全体の倍率','Layout','Size')
 blocks=[]
 for i,(name,(typ,ins,extra)) in enumerate(nodes.items()):
  items=[]
  for k,v in ins.items():
   s=inp(v)
   if k=='EffectMask': s=s.replace('Source = "Output"','Source = "Mask"')
   items.append(k+' = '+s+',')
  blocks.append(f'{name} = {typ} {{ Inputs = {{ '+'\n'.join(items)+f' }}, {extra} ViewInfo = OperatorInfo {{ Pos = {{ {(i%5)*180}, {(i//5)*110} }} }}, }},')
 s='{ Tools = ordered() { ZBM_'+kind+'_v11 = MacroOperator {\nInputs = ordered() {\n'+'\n'.join(pub)+'\n}, Outputs = { MainOutput1 = InstanceOutput { SourceOp = "UI_Position", Source = "Output", }, },\nViewInfo = GroupInfo { Pos = { 0, 0 } },\nTools = ordered() {\n'+'\n'.join(blocks)+'\n}, }, }, ActiveTool = "ZBM_'+kind+'_v11", }\n'
 (ROOT/'Templates'/f'ZBM_{kind}_v11.setting').write_text(s,encoding='utf-8')
 return dict(Counter(v[0] for v in nodes.values()))
counts={kind:make(kind) for kind in CFG}
(ROOT/'Source'/'layout.json').write_text(json.dumps(CFG,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'Source'/'node_counts.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
def prog(t,delay,duration,end=4):return max(0,min(1,(t-delay)/duration))*max(0,min(1,(end-t)/.18))
# Preload static images rather than decoding 4K PNGs for every preview frame.
ui_cache={k:Image.open(ROOT/'Assets'/f'{k}_UI.png').resize((960,540)) for k in CFG}
photo_cache={p.name:Image.open(p).convert('RGB') for p in (ROOT/'Assets').glob('sample_*.png')}
def frame(kind,t):
 w,h=960,540; im=Image.new('RGB',(w,h),'#161E20');ui=ui_cache[kind]
 p=prog(t,0,.20);b=CFG[kind]['panel'];bb=box((b[0],b[1],b[0]+(b[2]-b[0])*p,b[3]),w,h)
 if bb[2]>bb[0]:im.paste(ui.crop(bb),bb[:2],ui.crop(bb))
 for i,slot in enumerate(CFG[kind]['slots']):
  image='sample_detail.png' if kind=='DETAIL' else ('sample_left.png' if i==0 else 'sample_right.png')
  b=box(slot,w,h);sample=ImageOps.fit(photo_cache[image],(b[2]-b[0],b[3]-b[1]));ww=int(sample.width*prog(t,.12+i*.06,.26))
  if ww:im.paste(sample.crop((0,0,ww,sample.height)),b[:2])
 d=ImageDraw.Draw(im)
 for nm,txt,pos,size in CFG[kind]['texts']:
  alpha=prog(t,.31,.19)
  if alpha:d.multiline_text((pos[0]*w,(1-pos[1])*h),txt,font=ImageFont.truetype(FONT,round(size*w*1.3)),fill=tuple(int(v*alpha) for v in (220,231,230)),anchor='mm',align='center',spacing=8)
 d.text((20,18),'ZBM v1.1 / '+kind+' / CONCEPT SIMULATION',font=ImageFont.truetype(FONT,14),fill='#AFC2C3')
 d.text((20,510),'字幕用余白 / Resolveでのレンダリングではありません',font=ImageFont.truetype(FONT,14),fill='#AFC2C3')
 return im
for kind in CFG:frame(kind,1).save(ROOT/'Preview'/f'{kind}.png')
proc=subprocess.Popen(['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size','960x540','-framerate','30','-i','-','-an','-c:v','libx264','-crf','19','-pix_fmt','yuv420p',str(ROOT/'Preview'/'ZBM_v11_CONCEPT.mp4')],stdin=subprocess.PIPE)
for kind in CFG:
 for n in range(121):proc.stdin.write(frame(kind,n/30).tobytes())
proc.stdin.close();assert proc.wait()==0
print('Generated',ROOT,json.dumps(counts))
