#!/usr/bin/env python3
import json, os, re, threading, webbrowser
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs

ROOT=Path(__file__).resolve().parent
PORT=int(os.environ.get('PORT','8765'))

LOCATIONS={
 'mammoth': {'name':'Mammoth Lakes, CA','slug':'mammoth-lakes-ca','rent':2985,'overall':4000,'tax':1.16,'hoa':900,'insurance':125,'source':'https://www.zillow.com/rental-manager/market-trends/mammoth-lakes-ca/','note':'1-bedroom benchmark; small mountain-market samples can be volatile.'},
 'bishop': {'name':'Bishop, CA','slug':'bishop-ca','rent':1950,'overall':2100,'tax':1.12,'hoa':0,'insurance':145,'source':'https://www.zillow.com/rental-manager/market-trends/bishop-ca/','note':'1-bedroom benchmark.'},
 'big-pine': {'name':'Big Pine, CA','slug':'big-pine-ca','rent':1300,'overall':1300,'tax':1.12,'hoa':0,'insurance':145,'source':'https://www.zillow.com/rental-manager/market-trends/big-pine-ca/','note':'Very small rental sample; treat as a rough benchmark.'},
 'crowley-lake': {'name':'Crowley Lake, CA','slug':'crowley-lake-ca','rent':2250,'overall':3750,'tax':1.12,'hoa':0,'insurance':145,'source':'https://www.zillow.com/rental-manager/market-trends/crowley-lake-ca/','note':'Very small rental sample; treat as a rough benchmark.'},
 'lone-pine': {'name':'Lone Pine, CA','slug':'lone-pine-ca','rent':1800,'overall':2100,'tax':1.12,'hoa':0,'insurance':145,'source':'https://www.zillow.com/rental-manager/market-trends/lone-pine-ca/','note':'Sparse listings; the app uses the published planning fallback when bedroom data are unavailable.'},
 'independence': {'name':'Independence, CA','slug':'independence-ca','rent':1595,'overall':1595,'tax':1.12,'hoa':0,'insurance':145,'source':'https://www.zillow.com/rental-manager/market-trends/independence-ca/','note':'Extremely small rental sample; use caution.'},
 'south-lake-tahoe': {'name':'South Lake Tahoe, CA','slug':'south-lake-tahoe-ca','rent':1575,'overall':3000,'tax':1.10,'hoa':650,'insurance':175,'source':'https://www.zillow.com/rental-manager/market-trends/south-lake-tahoe-ca/','note':'1-bedroom benchmark; HOA varies widely by property.'},
 'incline-village': {'name':'Incline Village, NV','slug':'incline-village-nv','rent':2400,'overall':4000,'tax':0.65,'hoa':700,'insurance':160,'source':'https://www.zillow.com/rental-manager/market-trends/incline-village-nv/','note':'1-bedroom benchmark; Nevada taxes and HOA structures differ by property.'},
 'stateline': {'name':'Stateline, NV','slug':'stateline-nv','rent':2133,'overall':4500,'tax':0.65,'hoa':700,'insurance':160,'source':'https://www.zillow.com/rental-manager/market-trends/stateline-nv/','note':'1-bedroom benchmark; small and vacation-heavy market.'},
 'zephyr-cove': {'name':'Zephyr Cove, NV','slug':'zephyr-cove-nv','rent':1900,'overall':1900,'tax':0.65,'hoa':650,'insurance':160,'source':'https://www.zillow.com/rental-manager/market-trends/zephyr-cove-nv/','note':'Small sample; treat as a planning benchmark.'},
}

MORTGAGE_URL='https://www.freddiemac.com/pmms'

def fetch(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 HouseAlpha/3.0'})
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
        t=fetch(loc['source'])
        one=first_float([r'one-bedroom apartment[^$]{0,180}\$([0-9,]+)',r'one bedroom[^$]{0,180}\$([0-9,]+)'],t)
        overall=first_float([r'average rent(?: for all bedrooms and all property types)?[^$]{0,180}\$([0-9,]+)'],t)
        if one:out['rent']=one
        if overall:out['overall']=overall
        out['status']['rent']='Updated from public rental-market page'
    except Exception:
        out['status']['rent']='Saved benchmark — live source unavailable'
    out['status']['hoa']='Editable planning benchmark; no complete live HOA census'
    out['status']['insurance']='Editable home-insurance planning estimate'
    out['sources']={'mortgage':MORTGAGE_URL,'rent':loc['source']}
    return out

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/market':
            q=parse_qs(u.query); location=q.get('location',['mammoth'])[0]
            data=json.dumps(market(location)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path=='/api/locations':
            data=json.dumps({k:{'name':v['name']} for k,v in LOCATIONS.items()}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if self.path=='/':self.path='/index.html'
        return super().do_GET()
    def log_message(self,fmt,*args):pass

def main():
    os.chdir(ROOT);host=os.environ.get('HOST','0.0.0.0');server=ThreadingHTTPServer((host,PORT),Handler)
    url=f'http://127.0.0.1:{PORT}';print('House Alpha running at',url)
    if os.environ.get('OPEN_BROWSER','1')=='1' and not os.environ.get('RENDER'):threading.Timer(.8,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
if __name__=='__main__':main()
