import os, json, uuid, zipfile, shutil, re
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

DATA = Path(os.getenv('DATA_DIR', './data'))
PROJECTS = DATA / 'projects'; UPLOADS = DATA / 'uploads';
PROJECTS.mkdir(parents=True, exist_ok=True); UPLOADS.mkdir(parents=True, exist_ok=True)
MEMORY = DATA / 'memory.json'
if not MEMORY.exists(): MEMORY.write_text(json.dumps({'messages': [], 'facts': [], 'projects': []}, indent=2), encoding='utf-8')

FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'https://zayaiken21.github.io')
CORS_ORIGINS = [x.strip() for x in os.getenv('CORS_ORIGINS', FRONTEND_ORIGIN).split(',') if x.strip()]
if '*' in CORS_ORIGINS: CORS_ORIGINS = ['*']

app = FastAPI(title='The Haven Engine', version='4.0.0', description='Deterministic engineering, project-generation and build orchestration API.')
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=False, allow_methods=['*'], allow_headers=['*'])

class Chat(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
    files: list[str] = []

class Build(BaseModel):
    name: str = 'haven-project'
    kind: str = 'auto'
    request: str = Field(min_length=1, max_length=50000)
    files: dict[str, str] = {}

class DesignRequest(BaseModel):
    name: str = 'Haven Project'
    platform: str = 'web'
    genre: str = 'general'
    style: str = 'premium'
    request: str = Field(min_length=1, max_length=20000)

LANG = {
 'html':['html','htm'],'css':['css'],'javascript':['js','mjs','cjs'],'typescript':['ts','tsx'],
 'python':['py'],'java':['java'],'c':['c','h'],'cpp':['cpp','cc','cxx','hpp'],'csharp':['cs'],
 'rust':['rs'],'go':['go'],'php':['php'],'ruby':['rb'],'swift':['swift'],'kotlin':['kt','kts'],
 'sql':['sql'],'json':['json'],'yaml':['yml','yaml'],'markdown':['md']}

CAPABILITIES = {
 'engineering': ['project architecture','code generation templates','file inspection','language classification','validation','build manifests','reproducible ZIP exports'],
 'games': ['2D canvas scaffolds','3D WebGL/Three.js project scaffolds','game-loop templates','input/UI scaffolds','scene/entity manifests'],
 'apps': ['responsive web apps','PWA scaffolds','API client scaffolds','dashboard/UI component scaffolds'],
 'ux_ui': ['design tokens','responsive layout specs','accessibility checklist','interaction states','component manifests'],
 'quality': ['path safety','manifest generation','basic static validation','health checks','project packaging','ephemeral-workspace safety'],
 'languages': sorted(LANG.keys()),
 'design': ['UX flows','UI component states','responsive layout','accessibility','home screens','navigation','menus','design tokens','game HUDs','game menus','2D/3D interaction patterns']
}

KNOWLEDGE = {
 'github': 'GitHub is the source-control and deployment source. It is not unlimited runtime storage; large generated binaries and user uploads belong in persistent/object storage.',
 'render': 'Render runs The Haven Engine. On the free plan, the filesystem is intentionally ephemeral: generated workspaces, uploads and memory can disappear when Render restarts or spins the service down. Keep important source in GitHub or another durable datastore.',
 'storage': 'Free operation uses the service filesystem only as temporary workspace storage. For durable production data, use a database for metadata and object storage for generated files.',
 'root': 'The root URL is a service information endpoint. Use /health for health checks, /capabilities for supported modules, /chat for questions, /projects/build for builds, and /projects/{id}/download for ZIP exports.',
 'limitations': 'The core engine is a deterministic engineering system, not a general-purpose generative model. It supports many languages and structured web, app, game and UX/UI scaffolds. A server-side model adapter can be enabled later with a provider key stored only in Render environment variables.'
}

def now(): return datetime.now(timezone.utc).isoformat()
def readmem():
    try: return json.loads(MEMORY.read_text(encoding='utf-8'))
    except Exception: return {'messages': [], 'facts': [], 'projects': []}
def writemem(x): MEMORY.write_text(json.dumps(x, indent=2, ensure_ascii=False), encoding='utf-8')
def remember(role, text):
    m=readmem(); m['messages'].append({'time':now(),'role':role,'text':text}); m['messages']=m['messages'][-3000:]; writemem(m)
def extlang(path):
    ext=Path(path).suffix.lower().lstrip('.')
    for lang, exts in LANG.items():
        if ext in exts: return lang
    return 'unknown'
def safe_path(name):
    p=Path(name.replace('\\','/'))
    return not p.is_absolute() and '..' not in p.parts

def tree(files):
    return '\n'.join('  '*max(0,len(Path(n).parts)-1)+'└─ '+Path(n).name+' ['+extlang(n)+']' for n in sorted(files))

def validate_files(files):
    errors=[]
    for n,v in files.items():
        if not safe_path(n): errors.append(f'Unsafe path rejected: {n}')
        if len(n)>240: errors.append(f'Path too long: {n}')
        if not isinstance(v,str): errors.append(f'Non-text content requires upload endpoint: {n}')
    return errors

def design_spec(d):
    return {
      'name': d.name, 'platform': d.platform, 'genre': d.genre, 'style': d.style,
      'brief': d.request,
      'design_tokens': {'radius':'14px','spacing':'8px grid','motion':'150-250ms','contrast':'WCAG-aware','layout':'responsive'},
      'screens':['home','workspace','project/build status','settings'],
      'states':['idle','hover','focus','pressed','loading','success','error','empty','offline'],
      'accessibility':['keyboard navigation','visible focus','reduced-motion support','semantic labels','touch targets >= 44px'],
      'responsive':['mobile portrait','tablet','desktop'],
      'ux_principles':['clear primary action','progress feedback','recoverable errors','no destructive action without confirmation']
    }

def generate(kind, request):
    r=request.lower()
    if kind=='auto':
        if any(x in r for x in ['3d','three.js','webgl']): kind='3d-game'
        elif any(x in r for x in ['game','racing','player','enemy','score','joystick','2d']): kind='game'
        elif any(x in r for x in ['app','dashboard','pwa','mobile']): kind='app'
        else: kind='web'
    if kind in ('game','web','static','app','3d-game'):
        game=kind in ('game','3d-game')
        three = kind=='3d-game'
        index='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1220"><title>The Haven Project</title><link rel="stylesheet" href="styles.css"></head><body><main><header><h1>The Haven Project</h1><p id="description"></p></header>'''
        if three: index += '<canvas id="game" aria-label="3D game canvas"></canvas>'
        elif game: index += '<canvas id="game" width="900" height="500" aria-label="Game canvas"></canvas>'
        else: index += '<section id="app" class="card"></section>'
        index += '<footer>Generated and packaged by The Haven Engine.</footer></main><script src="app.js"></script></body></html>'
        css='''body{margin:0;background:#07101d;color:#eef4ff;font-family:Inter,system-ui,sans-serif}main{width:min(1100px,92%);margin:32px auto}header{text-align:center;margin-bottom:20px}.card,canvas{width:100%;min-height:420px;background:#0c1728;border:1px solid #29405f;border-radius:16px;box-shadow:0 20px 60px #0005}button{min-height:44px}footer{text-align:center;color:#91a4bf;margin:20px}'''
        if three:
            js='''const c=document.querySelector('#game');const ctx=c.getContext('2d');function fit(){c.width=c.clientWidth*devicePixelRatio;c.height=Math.max(420,c.clientHeight)*devicePixelRatio}addEventListener('resize',fit);fit();ctx.fillStyle='#0b1220';ctx.fillRect(0,0,c.width,c.height);ctx.fillStyle='#7dd3fc';ctx.font=`${32*devicePixelRatio}px system-ui`;ctx.fillText('3D WebGL-ready Haven scaffold',30*devicePixelRatio,70*devicePixelRatio);'''
        elif game:
            js='''const c=document.querySelector('#game'),x=c.getContext('2d');let p={x:80,y:220},k={};addEventListener('keydown',e=>k[e.key.toLowerCase()]=1);addEventListener('keyup',e=>k[e.key.toLowerCase()]=0);function loop(){p.x+=((k.d||k.arrowright)?4:0)-((k.a||k.arrowleft)?4:0);p.y+=((k.s||k.arrowdown)?4:0)-((k.w||k.arrowup)?4:0);p.x=Math.max(0,Math.min(c.width-30,p.x));p.y=Math.max(0,Math.min(c.height-30,p.y));x.clearRect(0,0,c.width,c.height);x.fillStyle='#60a5fa';x.fillRect(p.x,p.y,30,30);requestAnimationFrame(loop)}loop();'''
        else:
            js="document.querySelector('#description').textContent="+json.dumps(request)+";document.querySelector('#app').innerHTML='<h2>Project workspace</h2><p>Responsive application scaffold generated by The Haven.</p>';"
        return {'index.html':index,'styles.css':css,'app.js':js,'HAVEN-DESIGN.json':json.dumps({'request':request,'kind':kind},indent=2)}
    if kind=='node': return {'package.json':json.dumps({'name':'haven-project','version':'1.0.0','private':True,'scripts':{'start':'node src/index.js'}},indent=2),'src/index.js':'console.log('+json.dumps(request)+');'}
    if kind=='python': return {'app.py':'print('+repr(request)+')','requirements.txt':'# Add third-party packages here as needed.\n'}
    return {'README.md':'# The Haven project\n\n'+request+'\n'}

@app.get('/')
def root():
    return {'service':'The Haven Engine','status':'online','version':'4.0.0','frontend':'https://zayaiken21.github.io/The-Haven/','health':'/health','capabilities':'/capabilities','message':'The engine is running. This endpoint intentionally returns JSON instead of 404.'}

@app.get('/health')
def health(): return {'ok':True,'service':'the-haven-engine','version':'4.0.0','time':now(),'data_dir':str(DATA),'data_dir_exists':DATA.exists()}

@app.get('/capabilities')
def capabilities(): return {'ok':True,'capabilities':CAPABILITIES,'endpoints':['/','/health','/capabilities','/chat','/design/spec','/projects/build','/projects/{id}/download','/uploads']}

@app.post('/chat')
def chat(c:Chat):
    remember('user',c.message); q=c.message.lower()
    if 'github' in q: reply=KNOWLEDGE['github']
    elif 'render' in q or 'persistent' in q or 'disk' in q: reply=KNOWLEDGE['render']
    elif 'storage' in q or 'memory' in q: reply=KNOWLEDGE['storage']
    elif 'capabil' in q or 'what can' in q: reply='The Haven supports engineering scaffolds, 2D/3D game scaffolds, responsive apps, UX/UI design specifications, file inspection, validation, manifests and ZIP builds. See /capabilities for the API capability map.'
    elif 'ai' in q or 'generative' in q: reply=KNOWLEDGE['limitations']
    elif 'root' in q or 'not found' in q or '404' in q: reply=KNOWLEDGE['root']
    elif 'file' in q or 'folder' in q: reply='I can inspect supplied project filenames, classify languages, validate safe paths, and build a deterministic project tree. Current files: '+(', '.join(c.files) if c.files else 'none.')
    else: reply='The Haven Engine is online. I can answer supported engineering questions, produce deterministic project scaffolds, generate UX/UI specifications, validate project files, and package builds. For unconstrained novel code generation, connect a server-side model adapter; do not put provider keys in the browser.'
    remember('assistant',reply); return {'reply':reply,'engine':'The Haven Engine','version':'4.0.0'}

@app.post('/design/spec')
def design(d:DesignRequest): return {'ok':True,'spec':design_spec(d)}

@app.post('/projects/build')
def build(b:Build):
    pid=str(uuid.uuid4()); p=PROJECTS/pid; p.mkdir()
    generated=generate(b.kind,b.request)
    for n,v in b.files.items():
        n=n.replace('\\','/')
        if not safe_path(n): continue
        if n not in generated: generated[n]=v if isinstance(v,str) else str(v)
    errors=validate_files(generated)
    if errors: raise HTTPException(400,detail={'errors':errors})
    manifest={'project_id':pid,'name':b.name,'request':b.request,'kind':b.kind,'created_at':now(),'files':sorted(generated),'tree':tree(generated),'capabilities':['generation','validation','packaging']}
    (p/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    (p/'files.json').write_text(json.dumps(generated,indent=2,ensure_ascii=False),encoding='utf-8')
    m=readmem();m['projects'].append({'id':pid,'name':b.name,'created_at':manifest['created_at']});m['projects']=m['projects'][-500:];writemem(m)
    return {'project_id':pid,'files':generated,'manifest':manifest}

@app.get('/projects/{pid}/download')
def download(pid:str):
    p=PROJECTS/pid
    if not p.exists(): raise HTTPException(404,'Project not found')
    data=json.loads((p/'files.json').read_text(encoding='utf-8')); z=p/'The-Haven-Project.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as out:
        for n,v in data.items(): out.writestr(n,v)
        out.writestr('HAVEN-MANIFEST.json',(p/'manifest.json').read_text(encoding='utf-8'))
    return FileResponse(z,media_type='application/zip',filename='The-Haven-Project.zip')

@app.post('/uploads')
async def uploads(files:list[UploadFile]=File(...)):
    saved=[]
    for f in files:
        uid=str(uuid.uuid4()); safe=Path(f.filename or 'upload.bin').name; dest=UPLOADS/(uid+'-'+safe)
        with dest.open('wb') as out: shutil.copyfileobj(f.file,out)
        saved.append({'id':uid,'name':safe,'size':dest.stat().st_size})
    return {'saved':saved}
