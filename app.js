const $=id=>document.getElementById(id);
const ENGINE_URL='https://haven-engine.onrender.com';
const REQUEST_TIMEOUT_MS=12000;
let files={},lastJob=null,connecting=false;

function setStatus(text,online=false,waking=false){
  const el=$('connection'); el.textContent='● '+text; el.classList.toggle('online',online); el.classList.toggle('waking',waking);
}
function add(text,kind){const d=document.createElement('div');d.className='msg '+kind;d.textContent=text;$('messages').appendChild(d);$('messages').scrollTop=$('messages').scrollHeight}
async function fetchWithTimeout(resource, options={}){
  const c=new AbortController(), t=setTimeout(()=>c.abort(),REQUEST_TIMEOUT_MS);
  try{return await fetch(resource,{...options,signal:c.signal,cache:'no-store',mode:'cors'})}
  finally{clearTimeout(t)}
}
async function api(path,opts={}){
  try{
    const r=await fetchWithTimeout(ENGINE_URL+path,opts);
    if(!r.ok) throw new Error((await r.text()).slice(0,500)||`HTTP ${r.status}`);
    return r;
  }catch(e){
    if(e.name==='AbortError') throw new Error('The engine is waking up. Render Free services can sleep after inactivity and may take about a minute to wake.');
    throw new Error('The browser could not reach the Render engine. Check that the backend deploy is live and CORS allows this GitHub Pages origin.');
  }
}

async function connect({silent=false,announce=false}={}){
  if(connecting)return null; connecting=true;
  setStatus('Checking engine…',false,true);
  try{
    const r=await api('/health'); const j=await r.json();
    setStatus('Connected',true,false);
    if(announce)add('The Haven Engine is online and ready.','system');
    return j;
  }catch(e){
    setStatus('Engine asleep / waking',false,true);
    if(announce)add(e.message,'system');
    return null;
  }finally{connecting=false}
}

$('send').onclick=async()=>{const text=$('prompt').value.trim();if(!text)return;add(text,'user');$('prompt').value='';try{const r=await api('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,files:Object.keys(files)})});const j=await r.json();add(j.reply,'assistant')}catch(e){add('The Haven Engine: '+e.message,'system')}};
$('prompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();$('send').click()}});
$('retry').onclick=()=>connect({announce:true});
$('build').onclick=async()=>{const text=$('prompt').value.trim();if(!text){add('Describe what you want to build first.','system');return}try{const r=await api('/projects/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:'haven-project',kind:'auto',request:text,files})});lastJob=await r.json();files=lastJob.files||{};renderFiles();$('download').disabled=false;add(`Build complete: ${Object.keys(files).length} files created.`,'assistant')}catch(e){add('Build failed: '+e.message,'system')}};
$('download').onclick=async()=>{if(!lastJob)return;try{const r=await api('/projects/'+encodeURIComponent(lastJob.project_id)+'/download');const blob=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='The-Haven-Project.zip';document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),3000)}catch(e){add('Download failed: '+e.message,'system')}};
$('uploadBtn').onclick=()=>$('files').click();
$('files').onchange=async()=>{for(const f of $('files').files){files[f.name]=await f.text().catch(()=> '[binary file uploaded; stored by engine]')}renderFiles();try{const fd=new FormData();for(const f of $('files').files)fd.append('files',f);await api('/uploads',{method:'POST',body:fd});add(`${$('files').files.length} file(s) uploaded to the Haven workspace.`,'assistant')}catch(e){add('Upload failed: '+e.message,'system')}};
function renderFiles(){$('filesList').innerHTML=Object.keys(files).length?Object.keys(files).map(x=>'<div>📄 '+x+'</div>').join(''):'No files yet.'}

// Never block the UI on the backend. GitHub Pages loads immediately; the engine connects in the background.
renderFiles();
setStatus('Starting locally',false,false);
connect({silent:true});
setInterval(()=>{if(!document.hidden&&!$('connection').classList.contains('online'))connect({silent:true})},30000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden&&!$('connection').classList.contains('online'))connect({silent:true})});
