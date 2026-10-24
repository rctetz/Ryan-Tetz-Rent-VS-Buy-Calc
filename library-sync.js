/* Private library state stays in memory. Only signed-out work uses browser storage. */
(() => {
  'use strict';
  const state = {mode:'checking', user:null, csrf:'', items:[], revision:0, dirty:false,
    saving:false, workspaceEpoch:0, conflict:false, loaded:false, sequence:0, generation:0, workspace:null,
    defaults:null, limits:{items:100}, registration:'invite', message:'Checking your library…', kind:'', initialized:false};
  const el = id => document.getElementById(id);
  const clone = value => JSON.parse(JSON.stringify(value));
  let syncTimer, refreshing=false, channel;
  const privateMode = () => state.mode !== 'local';
  const active = () => state.mode === 'cloud';
  const usable = () => active() && state.loaded;
  function setStatus(message, kind='') { state.message=message; state.kind=kind; render(); }
  function normalize(items) {
    if (!Array.isArray(items)) throw new Error('Choose a House Alpha library JSON file.');
    if (items.length > limit()) throw new Error(`This library is limited to ${limit()} properties. Import fewer properties.`);
    const clean=items.map(sanitizePropertyHistoryEntry);
    if (clean.some(item=>!item)) throw new Error('The file contains an invalid property. Nothing was imported.');
    if (new Set(clean.map(item=>item.id)).size!==clean.length) throw new Error('The file has duplicate property IDs. Nothing was imported.');
    return clean;
  }
  function limit() { return active()?Number(state.limits.items)||100:PROPERTY_HISTORY_LIMIT; }
  async function request(path, {method='GET',body,csrf=state.csrf}={}) {
    const headers={Accept:'application/json'};
    if (body!==undefined) headers['Content-Type']='application/json';
    if (method!=='GET' && csrf) headers['X-CSRF-Token']=csrf;
    let response;
    try { response=await fetch(path,{method,headers,credentials:'same-origin',cache:'no-store',body:body===undefined?undefined:JSON.stringify(body)}); }
    catch (_) { const error=new Error('Cannot reach the server. Unsynced changes stay in this tab; export them before closing it.'); error.network=true; throw error; }
    let data; try { data=await response.json(); } catch (_) { throw new Error('The server returned an unreadable response. Your changes have not been confirmed.'); }
    if (!response.ok) { const error=new Error(typeof data.message==='string'?data.message:typeof data.error==='string'?data.error:`Request failed (${response.status}).`); error.status=response.status; error.data=data; throw error; }
    return data;
  }
  function render() {
    if (!el('libraryPanel')) return;
    const signed=active(), expired=state.mode==='expired', checking=state.mode==='checking';
    el('libraryIdentity').textContent=signed?`${state.user.username}’s library`:expired?'Library locked':'My library';
    el('librarySummary').textContent=signed?(state.dirty?'Changes waiting to sync':state.loaded?`${state.items.length} synced ${state.items.length===1?'property':'properties'}`:'Loading…'):expired?'Sign in again to continue':checking?'Connecting…':'Sign in to sync across devices';
    el('libraryStatus').textContent=state.message;
    el('libraryStatus').dataset.state=state.kind;
    el('libraryStatus').setAttribute('role',state.kind==='error'?'alert':'status');
    el('libraryAuth').hidden=signed||checking;
    el('libraryAccountActions').hidden=!signed;
    el('libraryLoginSubmit').disabled=checking||!appReady;
    el('libraryRegisterSubmit').disabled=checking||!appReady;
    el('librarySync').disabled=!usable()||state.saving||state.conflict;
    el('libraryRefresh').disabled=!usable()||state.saving;
    el('libraryRefresh').textContent=state.conflict?'Discard local edits & reload cloud':'Refresh from cloud';
    el('libraryImportDevice').disabled=!usable()||state.conflict;
    el('libraryImportFile').disabled=checking||expired||(signed&&!state.loaded)||state.conflict;
    el('libraryExport').disabled=checking||(signed&&!state.loaded);
    el('libraryLogout').disabled=state.saving;
    el('libraryConflict').hidden=!state.conflict;
    el('libraryRecovery').hidden=!expired;el('libraryRecoveryExport').hidden=!state.dirty;
    el('libraryContinueLocal').textContent=state.dirty?'Discard pending edits & continue signed out':'Continue signed out';
    el('libraryPrivacy').textContent=signed?'Saved properties, addresses, inputs, and photo thumbnails sync to your private account. Unsaved workspace edits stay in this tab.':expired?'Your account data is hidden. Any unsynced library changes remain in this tab for recovery or export.':'Signed-out saves stay only in this browser. Signing in does not upload them; import is always your choice.';
    el('propertyHistoryPrivacy').textContent=signed?'This is your private synced library, including saved addresses and photo thumbnails. Use Save to sync a property; unfinished workspace edits are not uploaded.':expired?'Sign in again to access your private library. Your signed-out device library is kept separate.':'Keep a deal library in this browser. Sign in above to sync across devices; importing these device-only saves is optional.';
    const photoNote=el('libraryPhotoPrivacy'); if(photoNote)photoNote.textContent=signed?'A small thumbnail is included when this property is saved to your private account.':'A small thumbnail stays in this browser when you save while signed out.';
  }
  function redraw() { render(); renderPropertyHistory(); if(latestResult)renderSavedComparison(latestResult,latestBreakEvenPrice); }
  function resetWorkspace() {
    state.workspaceEpoch++;state.workspace=null;suspendUpdates=false;setLookupMutationLocked(false);
    // Invalidate asynchronous lookups/location loads and remove private photos and provenance.
    locationRequestSeq++; propertyPhotoSeq++; clearPropertyLookup({hideApplied:true,status:''});
    activePropertyHistoryId=''; activePropertyBaseline=null;
    if(state.defaults)restoreScenario(clone(state.defaults),{historyId:'',status:'New workspace'});
    setPropertyPhoto(''); scenarioDirty=false; setScenarioStatus('Not saved');
    el('propertyHistoryStatus').textContent='';
  }
  function localMode(message='Signed out. Saves stay in this browser.') {
    state.generation++; state.mode='local'; state.user=null; state.csrf=''; state.items=[];
    state.revision=0; state.dirty=false; state.saving=false; state.conflict=false; state.loaded=false; state.sequence=0;
    resetWorkspace();
    const saved=readSavedScenario(); if(saved)restoreScenario(saved,{status:'Device workspace restored'});
    state.message=message; state.kind=''; redraw();
  }
  function expire(message='Your session ended. Sign in again; any unsynced library changes are retained in this tab.') {
    state.generation++; state.mode='expired'; state.csrf=''; state.saving=false;
    if(!state.dirty){state.items=[];state.loaded=false;state.revision=0;state.conflict=false;}
    resetWorkspace(); state.message=message; state.kind='error'; el('libraryPanel').open=true; redraw();
  }
  function verifyOwner(data) {
    if(data.user && String(data.user.id)!==String(state.user?.id)) { expire('The account changed in another tab. Sign in again before continuing.'); throw new Error('Account changed. No library changes were sent.'); }
  }
  async function fetchLibrary(generation=state.generation) {
    const sequence=state.sequence;
    const conditional=state.loaded&&!state.dirty&&!state.conflict;
    const data=await request('/api/library'+(conditional?'?revision='+encodeURIComponent(state.revision):''));
    if(generation!==state.generation||!active())return false;
    verifyOwner(data);
    // A save or delete made while this GET was in flight must never be overwritten.
    if(sequence!==state.sequence){setStatus('New edits kept in this tab. Sync to send them to the cloud.','warning');return false;}
    if(Number.isInteger(data.revision)&&data.revision<state.revision)return false;
    if(data.unchanged===true&&conditional&&data.revision===state.revision){setStatus(`Synced · ${state.items.length} ${state.items.length===1?'property':'properties'}`);return true;}
    if(!Number.isInteger(data.revision)||data.revision<0||!Array.isArray(data.items))throw new Error('The server returned an invalid library.');
    state.items=normalize(data.items); state.revision=data.revision; state.loaded=true; state.dirty=false; state.conflict=false;
    setStatus(`Synced · ${state.items.length} ${state.items.length===1?'property':'properties'}`); redraw(); return true;
  }
  async function activateSession(session, {recover=false}={}) {
    const sameUser=String(state.user?.id)===String(session.user?.id);
    const pending=recover&&sameUser&&state.dirty;
    state.generation++; const generation=state.generation;
    resetWorkspace(); state.mode='cloud'; state.user=session.user; state.csrf=session.csrfToken;
    state.limits=session.limits||state.limits; state.loaded=false; state.saving=false;
    if(!pending) { state.items=[]; state.revision=0; state.dirty=false; state.conflict=false; state.sequence=0; }
    redraw();
    if(pending) { state.loaded=true; setStatus('Recovered this tab’s unsynced changes. Sync now to save them, or export a copy.','warning'); redraw(); return; }
    try { await fetchLibrary(generation); }
    catch(error) { if(generation!==state.generation)return; if(error.status===401)expire(); else setStatus(error.message,'error'); }
  }
  async function checkSession({initial=false}={}) {
    if(refreshing||state.saving)return; refreshing=true; const generation=state.generation;
    try {
      const data=await request('/api/library/session');
      if(generation!==state.generation)return;
      state.limits=data.limits||state.limits; state.registration=data.registration||'invite';
      el('libraryRegisterTitle').textContent=state.registration==='open'?'Create a free account':'Create an invited account';
      el('libraryInviteField').hidden=state.registration!=='invite';el('libraryInvite').required=state.registration==='invite';
      el('libraryRegisterNote').textContent=state.registration==='closed'?'New accounts are currently closed.':state.registration==='open'?`Create a private library with up to ${state.limits.items||100} properties. Accounts are capped to stay within free hosting limits.`:'An invitation is required to create an account.';
      el('libraryRegisterDetails').hidden=data.registration==='closed';
      if(data.authenticated) {
        if(!data.user||!data.csrfToken)throw new Error('The server returned an incomplete session.');
        if(!active()||String(data.user.id)!==String(state.user?.id)) {
          if(state.dirty) { expire('The session changed. Export pending changes, then sign in again to continue.'); return; }
          await activateSession(data);
        } else { state.csrf=data.csrfToken; if(!state.dirty&&!state.conflict)await fetchLibrary(generation); }
      } else if(active()||state.mode==='expired')expire();
      else if(initial)localMode();
    } catch(error) {
      if(generation!==state.generation)return;
      if(error.status===401&&active())expire();
      else if(initial)localMode('Cloud sync is unavailable. You can use device-only saves and try signing in when connected.');
      else if(active())setStatus(error.message,'error');
    } finally { refreshing=false; }
  }
  async function authenticate(event,register=false) {
    event.preventDefault();
    const username=el(register?'libraryNewUsername':'libraryUsername').value.trim();
    const passwordInput=el(register?'libraryNewPassword':'libraryPassword');
    if(state.dirty&&state.user&&username.toLowerCase()!==state.user.username.toLowerCase()&&!confirm('This tab has unsynced changes for another account. Export them before switching, or choose OK to discard them.'))return;
    const button=el(register?'libraryRegisterSubmit':'libraryLoginSubmit'); button.disabled=true;
    setStatus(register?'Creating your account…':'Signing in…');
    try {
      const body={username,password:passwordInput.value}; if(register&&state.registration==='invite')body.invite=el('libraryInvite').value.trim();
      const data=await request(register?'/api/library/register':'/api/library/login',{method:'POST',body,csrf:''});
      passwordInput.value='';
      if(!data.user||!data.csrfToken)throw new Error('Sign-in response was incomplete. Refresh this page to check the session.');
      if(scenarioDirty&&!state.dirty&&!confirm('Sign-in succeeded. Clear the current unsaved calculator workspace to open your private library? Choose Cancel to keep working locally and sign out.')) {
        await request('/api/library/logout',{method:'POST',body:{},csrf:data.csrfToken}); setStatus('Signed out. Your current device workspace is unchanged.'); return;
      }
      if(String(state.user?.id)!==String(data.user.id)&&state.dirty){state.items=[];state.dirty=false;state.conflict=false;}
      await activateSession(data,{recover:true}); el('libraryInvite').value='';
      el('libraryPanel').open=true; channel?.postMessage('session-changed');
    } catch(error) { passwordInput.value=''; setStatus(error.message,'error'); }
    finally { button.disabled=false; render(); }
  }
  async function sync() {
    if(!usable()||!state.dirty||state.saving||state.conflict)return;
    const generation=state.generation,sequence=state.sequence,items=clone(state.items),revision=state.revision;
    state.saving=true;setStatus('Syncing changes…');
    try {
      const data=await request('/api/library',{method:'PUT',body:{revision,items}});
      if(generation!==state.generation)return; verifyOwner(data);
      if(!Number.isInteger(data.revision)||data.revision<=revision)throw new Error('Save was not confirmed by the server. Export a copy before closing this tab.');
      state.revision=data.revision; state.dirty=state.sequence!==sequence;
      setStatus(state.dirty?'More changes waiting to sync…':`Synced · ${state.items.length} ${state.items.length===1?'property':'properties'}`);
      if(!state.dirty)channel?.postMessage('library-updated');
    } catch(error) {
      if(generation!==state.generation)return;
      if(error.status===401)expire();
      else if(error.status===409) { state.conflict=true;setStatus('Another device changed this library. Your edits are preserved in this tab; export them before reloading the cloud version.','error');el('libraryPanel').open=true; }
      else if(error.status===403)expire('Your session changed or expired. Sign in again before syncing.');
      else setStatus(error.message,'error');
    } finally {
      if(generation===state.generation) { state.saving=false;render(); if(state.dirty&&!state.conflict&&state.sequence!==sequence)queueSync(); }
    }
  }
  function queueSync() { clearTimeout(syncTimer);syncTimer=setTimeout(sync,450); }
  function writeHistory(history) {
    if(!usable())throw new Error('Sign in and load your library before saving.');
    state.items=normalize(history.items);state.dirty=true;state.sequence++;
    setStatus(state.conflict?'Unsynced edits retained. Export them before resolving the conflict.':navigator.onLine?'Changes waiting to sync…':'Offline · changes are only in this tab. Export before closing.','warning'); queueSync();
  }
  async function refreshCloud() {
    if(!usable()||state.saving)return;
    if(state.dirty&&!confirm('Discard this tab’s unsynced library edits and load the latest cloud library? Export a copy first if you need to keep them. This does not replace your current calculator workspace.'))return;
    const generation=state.generation;clearTimeout(syncTimer);state.saving=true;render();
    try {
      const session=await request('/api/library/session');
      if(generation!==state.generation)return;
      if(!session.authenticated||String(session.user?.id)!==String(state.user?.id)) { expire('The session changed. Sign in again before refreshing.');return; }
      state.csrf=session.csrfToken; await fetchLibrary(generation);
    } catch(error) { if(generation!==state.generation)return;if(error.status===401)expire(); else setStatus(error.message,'error'); }
    finally{if(generation===state.generation){state.saving=false;render();if(state.dirty&&!state.conflict)queueSync();}}
  }
  function downloadExport() {
    const items=privateMode()?state.items:readLocalPropertyHistory().items;
    const payload={format:'house-alpha-library',version:1,exportedAt:new Date().toISOString(),items:clone(items)};
    const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
    const link=document.createElement('a');link.href=url;link.download=`house-alpha-library-${new Date().toISOString().slice(0,10)}.json`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
    setStatus('Export downloaded. It includes private addresses and photos; keep it somewhere safe.');
  }
  function importItems(raw) {
    if(state.mode==='expired'||state.mode==='checking'||state.conflict)throw new Error('Resolve the session or sync conflict before importing.');
    const incoming=normalize(raw),current=readPropertyHistory().items;
    const ids=new Set(current.map(item=>item.id)),keys=new Set(current.map(item=>item.dedupeKey).filter(Boolean));
    const added=incoming.filter(item=>{if(ids.has(item.id)||(item.dedupeKey&&keys.has(item.dedupeKey)))return false;ids.add(item.id);if(item.dedupeKey)keys.add(item.dedupeKey);return true;});
    if(current.length+added.length>limit())throw new Error(`This would exceed the ${limit()}-property limit. Nothing was imported.`);
    if(!added.length) { setStatus('No new properties to import. Existing saved properties were left unchanged.');return; }
    if(!confirm(`Import ${added.length} new properties${active()?' into your private cloud library':' into this browser'}? Existing properties with matching IDs or addresses will be kept.`))return;
    writePropertyHistory({version:1,items:[...added,...current]});redraw();
    if(!active())setStatus(`Imported ${added.length} properties into this browser.`);
  }
  async function importFile(event) {
    const file=event.target.files?.[0],generation=state.generation;event.target.value='';if(!file)return;
    try {
      if(file.size>24*1024*1024)throw new Error('Choose a JSON file smaller than 24 MB.');
      const data=JSON.parse(await file.text());if(generation!==state.generation)return;importItems(Array.isArray(data)?data:data.items);
    } catch(error) { setStatus(error instanceof SyntaxError?'That file is not valid JSON. Nothing was imported.':error.message,'error'); }
  }
  async function continueLocal() {
    if(state.dirty&&!confirm('Discard this tab’s unsynced library edits? Export them first if you need to keep them.'))return;
    try{const session=await request('/api/library/session');if(session.authenticated)await request('/api/library/logout',{method:'POST',body:{},csrf:session.csrfToken});localMode();channel?.postMessage('session-changed');}
    catch(error){setStatus('Could not confirm sign-out. '+error.message,'error');}
  }
  async function logout() {
    if(state.saving)return;
    if((state.dirty||scenarioDirty)&&!confirm('There are unsynced library edits or unsaved workspace changes. Export your library or save your property first. Sign out and discard this tab’s unsaved work?'))return;
    try { await request('/api/library/logout',{method:'POST',body:{}});localMode();channel?.postMessage('session-changed'); }
    catch(error) { if(error.status===401) {localMode();channel?.postMessage('session-changed');} else setStatus(`Sign-out was not completed. ${error.message}`,'error'); }
  }
  async function init() {
    if(state.initialized)return;state.initialized=true;state.defaults=clone(captureScenario());
    const legacyExport=()=>{if(location.hostname!=='mammoth-rent-vs-buy.onrender.com'){alert('Open the original House Alpha app on Render, then click this bookmark.');return;}try{const raw=JSON.parse(localStorage.getItem('house-alpha:property-history:v1')||'{"items":[]}');const url=URL.createObjectURL(new Blob([JSON.stringify({format:'house-alpha-library',version:1,exportedAt:new Date().toISOString(),items:raw.items||[]},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='house-alpha-library.json';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}catch(error){alert('The saved library could not be exported: '+error.message);}};
    el('libraryLegacyExport').href='javascript:('+legacyExport.toString()+')()';
    el('libraryLoginForm').addEventListener('submit',event=>authenticate(event));
    el('libraryRegisterForm').addEventListener('submit',event=>authenticate(event,true));
    el('librarySync').onclick=sync;el('libraryRefresh').onclick=refreshCloud;el('libraryLogout').onclick=logout;
    el('libraryExport').onclick=downloadExport;el('libraryRecoveryExport').onclick=downloadExport;el('libraryContinueLocal').onclick=continueLocal;
    el('libraryImportDevice').onclick=()=>{try{importItems(readLocalPropertyHistory().items);}catch(error){setStatus(error.message,'error');}};
    el('libraryImportFile').onclick=()=>el('libraryFile').click();el('libraryFile').onchange=importFile;
    el('libraryOpenProperties').onclick=()=>{el('propertyHistory').open=true;el('actualPropertyDisclosure').open=true;el('propertyHistory').scrollIntoView({behavior:'smooth',block:'center'});};
    const fragment=new URLSearchParams(location.hash.slice(1));
    if(fragment.has('invite')) {el('libraryInvite').value=fragment.get('invite')||'';el('libraryRegisterDetails').open=true;el('libraryPanel').open=true;fragment.delete('invite');history.replaceState(null,'',location.pathname+location.search+(fragment.size?'#'+fragment.toString():''));}
    if('BroadcastChannel' in window){channel=new BroadcastChannel('house-alpha-library-session');channel.onmessage=()=>checkSession();}
    window.addEventListener('focus',()=>checkSession());
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')checkSession();});
    window.addEventListener('online',()=>{if(state.dirty&&!state.conflict)sync();else checkSession();});
    window.addEventListener('offline',()=>{if(active())setStatus(state.dirty?'Offline · unsynced changes are only in this tab. Export before closing.':'Offline · viewing the library already loaded in this tab.','warning');});
    window.addEventListener('beforeunload',event=>{if(state.dirty||(active()&&scenarioDirty)){event.preventDefault();event.returnValue='';}});
    setInterval(()=>{if(document.visibilityState==='visible'&&active()&&!state.dirty)checkSession();},60000);
    render();await checkSession({initial:true});
  }
  window.HouseAlphaLibrary={init,privateMode,active,limit,writeHistory,workspaceEpoch:()=>state.workspaceEpoch,
    readHistory:()=>({version:1,items:usable()?clone(state.items):[]}),
    readWorkspace:()=>usable()&&state.workspace?clone(state.workspace):null,
    writeWorkspace:snapshot=>{if(!usable())throw new Error('Private library is not ready.');state.workspace=clone(snapshot);},
    clearWorkspace:()=>{state.workspace=null;},
    savedLabel:()=>active()?'Held in this tab · see library sync status':state.mode==='expired'?'Library locked':'Saved on this device',
    reset:()=>{if(confirm('Reset this workspace to default assumptions? Your saved property library will be kept.')){if(privateMode())resetWorkspace();else{localStorage.removeItem(SCENARIO_KEY);resetWorkspace();}}}
  };
})();
