'use strict';
const $ = id => document.getElementById(id);
let current=null, lastSelected=null, initialized=false, busy=false, configSig='';
function notice(message){ $('status').textContent=String(message || '就绪'); }
async function call(name,...args){
  try { return await window.pywebview.api[name](...args); }
  catch(err){ notice((err && (err.message || err.toString())) || '操作失败'); throw err; }
}
function button(text,action,disabled=false){const b=document.createElement('button');b.textContent=text;b.disabled=disabled;b.addEventListener('click',action);return b}
function renderDevices(state){
  const box=$('devices');box.replaceChildren();$('count').textContent=state.devices.length ? `${state.devices.length} 台设备` : '未发现设备';
  if(!state.devices.length){const empty=document.createElement('div');empty.className='empty';empty.textContent='连接手机并允许 USB 调试后，设备会自动出现。';box.append(empty)}
  for(const d of state.devices){
    const item=document.createElement('button');item.className='device-item'+(d.id===state.selected?' selected':'');
    const icon=document.createElement('span');icon.className='device-icon';icon.textContent='▯';
    const info=document.createElement('span');info.className='device-info';const name=document.createElement('strong');name.textContent=d.name;const model=document.createElement('small');model.textContent=d.model;info.append(name,model);
    const status=document.createElement('span');status.className='device-state'+(d.state==='device'?'':' offline');status.textContent=d.state==='device'?'已连接':'未授权';
    item.append(icon,info,status);item.addEventListener('click',()=>call('select_device',d.id).then(poll).catch(()=>{}));item.addEventListener('dblclick',()=>{if(d.state!=='device')return;call(d.running?'show_mirror':'toggle_mirror').then(poll).catch(()=>{})});box.append(item);
  }
  const selected=state.devices.find(d=>d.id===state.selected), online=selected?.state==='device';
  $('selectedName').textContent=selected?selected.name:'尚未选择设备';$('selectedModel').textContent=selected?selected.model+' · USB':'连接手机并允许 USB 调试';
  $('connectionText').textContent=selected?(online?'USB 已连接':'未授权或离线'):'未连接';$('connection').classList.toggle('online',!!online);
  $('connectBtn').disabled=!online;$('renameBtn').disabled=!online;$('connectBtn').classList.toggle('running',!!selected?.running);$('connectIcon').textContent=selected?.running?'■':'▶';$('connectText').textContent=selected?.running?'停止投屏':'一键 USB 连接';
  if(lastSelected!==state.selected){$('rename').value=selected?selected.name:'';lastSelected=state.selected}
  if(document.activeElement!==$('rename') && selected && $('rename').value!==selected.name) $('rename').value=selected.name;
}
function renderSettings(state){
  const s=state.settings, simple=s.simple_mode!==false;$('simpleMode').checked=simple;$('advancedPanel').hidden=simple;$('layout').classList.toggle('expanded',!simple);
  for(const key of ['size','fps','bitrate','directory']){const el=$(key);if(document.activeElement!==el && el.value!==String(s[key]??''))el.value=String(s[key]??'')}
  document.querySelectorAll('[data-flag]').forEach(el=>{el.checked=!!s[el.dataset.flag]});
}
function renderTasks(state){
  const box=$('tasks');const sig=JSON.stringify(state.tasks);if(box.dataset.signature===sig)return;box.dataset.signature=sig;box.replaceChildren();
  if(!state.tasks.length){const e=document.createElement('div');e.className='empty small-empty';e.textContent='暂无传输任务';box.append(e);return}
  for(const task of state.tasks){
    const item=document.createElement('div');item.className='task';const top=document.createElement('div');top.className='task-top';
    const name=document.createElement('span');name.className='task-name';name.textContent=task.name;name.title=task.name;
    const status=document.createElement('span');status.className='task-state';const pct=task.total?Math.min(100,Math.floor(task.done*100/task.total)):task.state==='已完成'?100:0;status.textContent=task.state+' · '+pct+'%';top.append(name,status);
    const progress=document.createElement('div');progress.className='progress';const bar=document.createElement('span');bar.style.width=pct+'%';progress.append(bar);
    const actions=document.createElement('div');actions.className='task-actions';const ended=task.state==='已完成'||task.state==='已取消'||task.state.startsWith('失败');
    for(const [label,kind] of [['暂停','pause'],['继续','resume'],['取消','cancel']])actions.append(button(label,()=>call('task_action',kind,task.id).then(poll).catch(()=>{}),ended));
    item.append(top,progress,actions);box.append(item);
  }
}
async function poll(){
  if(busy || !window.pywebview?.api)return;busy=true;
  try{const state=await call('state');current=state;renderDevices(state);renderSettings(state);renderTasks(state);notice(state.status);initialized=true}
  catch(e){console.error(e)}finally{busy=false}
}
async function setting(data){try{await call('settings',data);await poll()}catch(e){if(current)renderSettings(current)}}
async function setMode(simple){try{await call('set_mode',simple);await poll()}catch(e){if(current)renderSettings(current)}}
window.addEventListener('pywebviewready',()=>{
  $('refreshBtn').onclick=()=>call('refresh').then(()=>notice('正在刷新设备…')).catch(()=>{});
  $('connectBtn').onclick=()=>call('toggle_mirror').then(poll).catch(()=>{});
  $('renameBtn').onclick=()=>call('rename',$('rename').value).then(poll).catch(()=>{});
  $('rename').onkeydown=e=>{if(e.key==='Enter')$('renameBtn').click()};
  $('simpleMode').onchange=e=>setMode(e.target.checked);$('advancedBtn').onclick=()=>setMode(false);$('backSimple').onclick=()=>setMode(true);
  for(const key of ['size','fps','bitrate'])$(key).onchange=e=>setting({[key]:Number(e.target.value)});
  document.querySelectorAll('[data-flag]').forEach(el=>el.onchange=()=>setting({[el.dataset.flag]:el.checked}));
  $('directory').onchange=e=>setting({directory:e.target.value});
  const choose=async()=>{try{await call('settings',{directory:$('directory').value});await call('choose_files');await poll()}catch(e){}};
  $('chooseBtn').onclick=choose;$('dropzone').onclick=choose;$('dropzone').onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose()}};
  $('dropzone').addEventListener('dragenter',e=>{e.preventDefault();$('dropzone').classList.add('drag')});$('dropzone').addEventListener('dragleave',()=>$('dropzone').classList.remove('drag'));$('dropzone').addEventListener('drop',()=>{ $('dropzone').classList.remove('drag');setTimeout(poll,500)});
  $('showBtn').onclick=()=>call('show_mirror').catch(()=>{});$('reconnectBtn').onclick=()=>call('reconnect').then(poll).catch(()=>{});$('logsBtn').onclick=()=>call('open_logs').catch(()=>{});$('clearBtn').onclick=()=>call('clear_tasks').then(poll).catch(()=>{});
  poll();setInterval(poll,1000);
});
