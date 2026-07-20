#!/usr/bin/env python3
import json, os, re, threading, webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','8765'))

# Planning presets. Rent values aim to represent a current one-bedroom long-term rental.
# Sparse-market places are deliberately conservative estimates and remain editable.
LOCATIONS={
 'mammoth': {'name':'Mammoth Lakes, CA','rent':2985,'tax':1.16,'hoa':750,'insurance':175,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/mammoth-lakes-ca/','note':'Published 1BR benchmark; vacation-heavy inventory can make the sample volatile.'},
 'june-lake': {'name':'June Lake, CA','rent':2850,'tax':1.12,'hoa':700,'insurance':180,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/june-lake-ca/','note':'Sparse vacation market. Uses a planning estimate close to Mammoth rather than the distorted all-property average.'},
 'crowley-lake': {'name':'Crowley Lake, CA','rent':2250,'tax':1.12,'hoa':250,'insurance':165,'storage':325,'source':'https://www.zillow.com/rental-manager/market-trends/crowley-lake-ca/','note':'Sparse listings; planning estimate.'},
 'toms-place': {'name':"Tom's Place, CA",'rent':2050,'tax':1.12,'hoa':200,'insurance':165,'storage':300,'source':'','note':'Very sparse market; planning estimate.'},
 'lee-vining': {'name':'Lee Vining, CA','rent':1750,'tax':1.12,'hoa':100,'insurance':160,'storage':275,'source':'','note':'Sparse market; planning estimate.'},
 'bridgeport': {'name':'Bridgeport, CA','rent':1550,'tax':1.12,'hoa':100,'insurance':155,'storage':250,'source':'','note':'Sparse market; planning estimate.'},
 'benton': {'name':'Benton, CA','rent':1450,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'','note':'Very sparse market; rough planning estimate.'},
 'bishop': {'name':'Bishop, CA','rent':1950,'tax':1.12,'hoa':250,'insurance':155,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/bishop-ca/','note':'Published or saved 1BR benchmark.'},
 'big-pine': {'name':'Big Pine, CA','rent':1300,'tax':1.12,'hoa':100,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/big-pine-ca/','note':'Very small sample; rough planning benchmark.'},
 'paradise-sunny-slopes': {'name':'Paradise / Sunny Slopes, CA','rent':1800,'tax':1.12,'hoa':100,'insurance':160,'storage':250,'source':'','note':'Combined local planning estimate.'},
 'swall-meadows': {'name':'Swall Meadows, CA','rent':1900,'tax':1.12,'hoa':100,'insurance':165,'storage':275,'source':'','note':'Sparse market; planning estimate.'},
 'chalfant': {'name':'Chalfant Valley, CA','rent':1650,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'','note':'Sparse market; planning estimate.'},
 'independence': {'name':'Independence, CA','rent':1595,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/independence-ca/','note':'Extremely small sample; use caution.'},
 'lone-pine': {'name':'Lone Pine, CA','rent':1800,'tax':1.12,'hoa':100,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/lone-pine-ca/','note':'Sparse listings; planning fallback.'},
 'carson-city': {'name':'Carson City, NV','rent':1250,'tax':0.69,'hoa':300,'insurance':145,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/carson-city-nv/','note':'Published 1BR benchmark.'},
 'gardnerville': {'name':'Gardnerville, NV','rent':1300,'tax':0.65,'hoa':250,'insurance':145,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/gardnerville-nv/','note':'Published 1BR benchmark.'},
 'truckee': {'name':'Truckee, CA','rent':2000,'tax':1.10,'hoa':700,'insurance':210,'storage':400,'source':'https://www.zillow.com/rental-manager/market-trends/truckee-ca/','note':'Published 1BR benchmark; luxury and vacation inventory heavily affect overall averages.'},
 'sonora': {'name':'Sonora, CA','rent':1195,'tax':1.10,'hoa':300,'insurance':150,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/sonora-ca/','note':'Published 1BR benchmark.'},
 'south-lake-tahoe': {'name':'South Lake Tahoe, CA','rent':1595,'tax':1.10,'hoa':650,'insurance':200,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/south-lake-tahoe-ca/','note':'Published 1BR benchmark; HOA varies widely.'},
 'incline-village': {'name':'Incline Village, NV','rent':2400,'tax':0.65,'hoa':700,'insurance':185,'storage':375,'source':'https://www.zillow.com/rental-manager/market-trends/incline-village-nv/','note':'Published 1BR benchmark.'},
 'stateline': {'name':'Stateline, NV','rent':2100,'tax':0.65,'hoa':700,'insurance':185,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/stateline-nv/','note':'Small, vacation-heavy market; planning benchmark.'},
 'zephyr-cove': {'name':'Zephyr Cove, NV','rent':1950,'tax':0.65,'hoa':650,'insurance':185,'storage':350,'source':'','note':'Small sample; planning benchmark.'},
 'custom': {'name':'Custom / Anywhere','rent':2000,'tax':1.10,'hoa':300,'insurance':160,'storage':250,'source':'','note':'Enter local values manually.'},
}
MORTGAGE_URL='https://www.freddiemac.com/pmms'

def fetch(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 HouseAlpha/5.0'})
    with urlopen(req,timeout=15) as r:
        return r.read().decode('utf-8',errors='ignore')

def first_float(patterns,text):
    for p in patterns:
        m=re.search(p,text,re.I|re.S)
        if m:return float(m.group(1).replace(',',''))
    return None

def market(location='mammoth'):
    loc=LOCATIONS.get(location,LOCATIONS['mammoth']).copy()
    out={'updated_at':datetime.now(timezone.utc).isoformat(),'mortgage_rate':6.55,'location_key':location,**loc,'status':{}}
    try:
        t=fetch(MORTGAGE_URL)
        x=first_float([r'30-year fixed-rate mortgage averaged\s*([0-9.]+)%',r'30-Yr FRM[^0-9]+([0-9.]+)%'],t)
        if x:out['mortgage_rate']=x
        out['status']['mortgage']='Updated from Freddie Mac PMMS'
    except Exception:
        out['status']['mortgage']='Using saved weekly benchmark'
    try:
        if not loc.get('source'): raise ValueError('No live source')
        t=fetch(loc['source'])
        one=first_float([r'one-bedroom apartment[^$]{0,220}\$([0-9,]+)',r'one bedroom[^$]{0,220}\$([0-9,]+)'],t)
        if one: out['rent']=one
        out['status']['rent']='Updated from public rental-market page'
    except Exception:
        out['status']['rent']='Saved planning benchmark — live source unavailable'
    out['status']['hoa']='Location-specific editable condo benchmark'
    out['status']['insurance']='Editable home-insurance planning estimate'
    out['status']['storage']='Editable one-car garage / roughly 10×20 storage estimate'
    out['sources']={'mortgage':MORTGAGE_URL,'rent':loc.get('source','')}
    return out

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/market':
            q=parse_qs(u.query); location=q.get('location',['mammoth'])[0]
            data=json.dumps(market(location)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path=='/api/locations':
            data=json.dumps({k:{'name':v['name'],**v} for k,v in LOCATIONS.items()}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path=='/': self.path='/index.html'
        return super().do_GET()
    def log_message(self,fmt,*args): pass

def main():
    os.chdir(ROOT);host=os.environ.get('HOST','0.0.0.0');server=ThreadingHTTPServer((host,PORT),Handler)
    url=f'http://127.0.0.1:{PORT}';print('House Alpha running at',url)
    if os.environ.get('OPEN_BROWSER','1')=='1' and not os.environ.get('RENDER'):threading.Timer(.8,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
if __name__=='__main__':main()
