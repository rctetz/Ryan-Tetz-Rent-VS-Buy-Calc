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
 'mammoth': {'name':'Mammoth Lakes, CA','rent':2985,'tax':1.16,'hoa':750,'insurance':175,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/mammoth-lakes-ca/','note':'Published 1BR benchmark; vacation-heavy inventory can make the sample volatile.','home_value':825455,'home_source':'https://www.zillow.com/home-values/35858/mammoth-lakes-ca/','renter_storage_default':True},
 'june-lake': {'name':'June Lake, CA','rent':2850,'tax':1.12,'hoa':700,'insurance':180,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/june-lake-ca/','note':'Sparse vacation market. Uses a planning estimate close to Mammoth rather than the distorted all-property average.','home_value':750000,'home_source':'','renter_storage_default':True},
 'crowley-lake': {'name':'Crowley Lake, CA','rent':2250,'tax':1.12,'hoa':250,'insurance':165,'storage':325,'source':'https://www.zillow.com/rental-manager/market-trends/crowley-lake-ca/','note':'Sparse listings; planning estimate.','home_value':700000,'home_source':'','renter_storage_default':True},
 'toms-place': {'name':"Tom's Place, CA",'rent':2050,'tax':1.12,'hoa':200,'insurance':165,'storage':300,'source':'','note':'Very sparse market; planning estimate.','home_value':625000,'home_source':'','renter_storage_default':True},
 'lee-vining': {'name':'Lee Vining, CA','rent':1750,'tax':1.12,'hoa':100,'insurance':160,'storage':275,'source':'','note':'Sparse market; planning estimate.','home_value':550000,'home_source':'','renter_storage_default':False},
 'bridgeport': {'name':'Bridgeport, CA','rent':1550,'tax':1.12,'hoa':100,'insurance':155,'storage':250,'source':'','note':'Sparse market; planning estimate.','home_value':400000,'home_source':'','renter_storage_default':False},
 'benton': {'name':'Benton, CA','rent':1450,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'','note':'Very sparse market; rough planning estimate.','home_value':350000,'home_source':'','renter_storage_default':False},
 'bishop': {'name':'Bishop, CA','rent':1950,'tax':1.12,'hoa':250,'insurance':155,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/bishop-ca/','note':'Published or saved 1BR benchmark.','home_value':602317,'home_source':'https://www.zillow.com/home-values/23717/bishop-ca/','renter_storage_default':False},
 'big-pine': {'name':'Big Pine, CA','rent':1300,'tax':1.12,'hoa':100,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/big-pine-ca/','note':'Very small sample; rough planning benchmark.','home_value':420000,'home_source':'','renter_storage_default':False},
 'paradise-sunny-slopes': {'name':'Paradise / Sunny Slopes, CA','rent':1800,'tax':1.12,'hoa':100,'insurance':160,'storage':250,'source':'','note':'Combined local planning estimate.','home_value':500000,'home_source':'','renter_storage_default':False},
 'swall-meadows': {'name':'Swall Meadows, CA','rent':1900,'tax':1.12,'hoa':100,'insurance':165,'storage':275,'source':'','note':'Sparse market; planning estimate.','home_value':600000,'home_source':'','renter_storage_default':False},
 'chalfant': {'name':'Chalfant Valley, CA','rent':1650,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'','note':'Sparse market; planning estimate.','home_value':425000,'home_source':'','renter_storage_default':False},
 'independence': {'name':'Independence, CA','rent':1595,'tax':1.12,'hoa':75,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/independence-ca/','note':'Extremely small sample; use caution.','home_value':325000,'home_source':'','renter_storage_default':False},
 'lone-pine': {'name':'Lone Pine, CA','rent':1800,'tax':1.12,'hoa':100,'insurance':150,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/lone-pine-ca/','note':'Sparse listings; planning fallback.','home_value':400000,'home_source':'','renter_storage_default':False},
 'carson-city': {'name':'Carson City, NV','rent':1250,'tax':0.69,'hoa':300,'insurance':145,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/carson-city-nv/','note':'Published 1BR benchmark.','home_value':501950,'home_source':'https://www.zillow.com/home-values/30772/carson-city-nv/','renter_storage_default':False},
 'gardnerville': {'name':'Gardnerville, NV','rent':1300,'tax':0.65,'hoa':250,'insurance':145,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/gardnerville-nv/','note':'Published 1BR benchmark.','home_value':615068,'home_source':'https://www.zillow.com/home-values/31701/gardnerville-nv/','renter_storage_default':False},
 'truckee': {'name':'Truckee, CA','rent':2000,'tax':1.10,'hoa':700,'insurance':210,'storage':400,'source':'https://www.zillow.com/rental-manager/market-trends/truckee-ca/','note':'Published 1BR benchmark; luxury and vacation inventory heavily affect overall averages.','home_value':1030167,'home_source':'https://www.zillow.com/home-values/48047/truckee-ca/','renter_storage_default':True},
 'sonora': {'name':'Sonora, CA','rent':1195,'tax':1.10,'hoa':300,'insurance':150,'storage':250,'source':'https://www.zillow.com/rental-manager/market-trends/sonora-ca/','note':'Published 1BR benchmark.','home_value':420000,'home_source':'','renter_storage_default':False},
 'fresno': {'name':'Fresno, CA','rent':980,'tax':1.11,'hoa':300,'insurance':145,'storage':225,'source':'https://www.zillow.com/rental-manager/market-trends/fresno-ca/','note':'Published 1BR benchmark; citywide apartment mix varies substantially by neighborhood.','home_value':392929,'home_source':'https://www.zillow.com/home-values/18203/fresno-ca/','renter_storage_default':False},
 'south-lake-tahoe': {'name':'South Lake Tahoe, CA','rent':1595,'tax':1.10,'hoa':650,'insurance':200,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/south-lake-tahoe-ca/','note':'Published 1BR benchmark; HOA varies widely.','home_value':665209,'home_source':'https://www.zillow.com/home-values/40979/south-lake-tahoe-ca/','renter_storage_default':True},
 'incline-village': {'name':'Incline Village, NV','rent':2400,'tax':0.65,'hoa':700,'insurance':185,'storage':375,'source':'https://www.zillow.com/rental-manager/market-trends/incline-village-nv/','note':'Published 1BR benchmark.','home_value':1400000,'home_source':'','renter_storage_default':True},
 'stateline': {'name':'Stateline, NV','rent':2100,'tax':0.65,'hoa':700,'insurance':185,'storage':350,'source':'https://www.zillow.com/rental-manager/market-trends/stateline-nv/','note':'Small, vacation-heavy market; planning benchmark.','home_value':725000,'home_source':'','renter_storage_default':True},
 'zephyr-cove': {'name':'Zephyr Cove, NV','rent':1950,'tax':0.65,'hoa':650,'insurance':185,'storage':350,'source':'','note':'Small sample; planning benchmark.','home_value':1100000,'home_source':'','renter_storage_default':True},
 'custom': {'name':'Custom / Anywhere','rent':2000,'tax':1.10,'hoa':300,'insurance':160,'storage':250,'source':'','note':'Enter local values manually.','home_value':500000,'home_source':'','renter_storage_default':False},
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

def bedroom_rents(one_bed):
    # Planning ratios derived from typical long-term-rental relationships.
    # Exact bedroom-specific figures remain editable because small mountain
    # markets often lack enough active listings for stable averages.
    return {
        '1': round(one_bed),
        '2': round(one_bed * 1.32),
        '3': round(one_bed * 1.62),
        '4': round(one_bed * 1.92),
    }

def bedroom_prices(home_value, property_type='condo'):
    # These are editable planning estimates, not appraisals. The overall local
    # home-value benchmark is adjusted by property size and type.
    if property_type == 'single':
        factors = {'1': 0.65, '2': 0.82, '3': 1.00, '4': 1.25}
    else:
        factors = {'1': 0.48, '2': 0.70, '3': 0.92, '4': 1.10}
    return {k: round(home_value * f / 1000) * 1000 for k, f in factors.items()}

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
    try:
        if not loc.get('home_source'): raise ValueError('No live home-value source')
        t=fetch(loc['home_source'])
        hv=first_float([
            r'average[^$]{0,100}home value[^$]{0,50}\$([0-9,]+)',
            r'Typical Home Values[^$]{0,30}\$([0-9,]+)',
            r'##\s*\$([0-9,]+)'
        ],t)
        if hv: out['home_value']=hv
        out['status']['home_value']='Updated from public home-value page'
    except Exception:
        out['status']['home_value']='Saved editable local home-value benchmark'
    out['bedroom_rents']=bedroom_rents(out['rent'])
    out['bedroom_prices']={
        'condo': bedroom_prices(out['home_value'],'condo'),
        'single': bedroom_prices(out['home_value'],'single')
    }
    out['status']['bedroom_rents']='Editable bedroom estimates anchored to the local 1BR benchmark'
    out['status']['bedroom_prices']='Editable purchase-price estimates anchored to the local overall home-value benchmark'
    out['status']['hoa']='Location-specific editable condo benchmark'
    out['status']['insurance']='Editable home-insurance planning estimate'
    out['status']['storage']='Editable one-car garage / roughly 10×20 storage estimate'
    out['sources']={'mortgage':MORTGAGE_URL,'rent':loc.get('source',''),'home':loc.get('home_source','')}
    return out

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/market':
            q=parse_qs(u.query); location=q.get('location',['mammoth'])[0]
            data=json.dumps(market(location)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path=='/api/locations':
            data=json.dumps({k:{'name':v['name'],**v,
                'bedroom_rents':bedroom_rents(v['rent']),
                'bedroom_prices':{
                    'condo':bedroom_prices(v['home_value'],'condo'),
                    'single':bedroom_prices(v['home_value'],'single')
                }} for k,v in LOCATIONS.items()}).encode()
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
