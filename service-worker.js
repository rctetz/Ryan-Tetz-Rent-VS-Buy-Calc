const SHELL_CACHE='house-alpha-shell-v33';
const DATA_CACHE='house-alpha-data-v33';
const SHELL=['/','/index.html','/manifest.webmanifest','/social-card.png','/icons/icon-192.png','/icons/icon-512.png'];

self.addEventListener('install',event=>event.waitUntil(
  caches.open(SHELL_CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())
));

self.addEventListener('activate',event=>event.waitUntil(
  caches.keys()
    .then(keys=>Promise.all(keys.filter(key=>key.startsWith('house-alpha-')&&![SHELL_CACHE,DATA_CACHE].includes(key)).map(key=>caches.delete(key))))
    .then(()=>self.clients.claim())
));

function normalizedApiRequest(request){
  const url=new URL(request.url);url.searchParams.delete('x');return new Request(url.toString(),{method:'GET',headers:{Accept:'application/json'}})
}

async function offlineMarketFallback(request){
  const url=new URL(request.url),location=url.searchParams.get('location')||'mammoth';
  const cachedLocations=await caches.match('/api/locations');if(!cachedLocations)return null;
  try{
    const all=await cachedLocations.json(),saved=all[location];if(!saved)return null;
    return new Response(JSON.stringify({...saved,location_key:location,offline:true,status:{mortgage:'Offline saved benchmark',rent:'Offline saved benchmark',home_value:'Offline saved benchmark'},sources:{mortgage:'https://www.freddiemac.com/pmms',rent:saved.source||'',home:saved.home_source||''}}),{status:200,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}})
  }catch(error){return null}
}

self.addEventListener('fetch',event=>{
  const request=event.request,url=new URL(request.url);if(request.method!=='GET'||url.origin!==self.location.origin)return;

  if(url.pathname.startsWith('/api/')){
    event.respondWith((async()=>{
      const cacheKey=normalizedApiRequest(request);
      try{
        const response=await fetch(request);if(!response.ok)throw new Error(`HTTP ${response.status}`);
        const cache=await caches.open(DATA_CACHE);await cache.put(cacheKey,response.clone());return response
      }catch(error){
        const cached=await caches.match(cacheKey);if(cached)return cached;
        if(url.pathname==='/api/market'){const fallback=await offlineMarketFallback(request);if(fallback)return fallback}
        return new Response(JSON.stringify({error:'offline',message:'Reconnect once to refresh House Alpha market data.'}),{status:503,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}})
      }
    })());return
  }

  event.respondWith((async()=>{
    try{
      const response=await fetch(request);if(response.ok){const cache=await caches.open(SHELL_CACHE);await cache.put(request,response.clone())}return response
    }catch(error){
      const cached=await caches.match(request);if(cached)return cached;
      if(request.mode==='navigate')return caches.match('/index.html');
      return new Response('Offline',{status:503,headers:{'Content-Type':'text/plain'}})
    }
  })())
});
