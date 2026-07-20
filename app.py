#!/usr/bin/env python3
import json, re, threading, webbrowser, os
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
PORT = int(os.environ.get('PORT', '8765'))

SOURCES = {
    'mortgage': 'https://www.freddiemac.com/pmms',
    'rent': 'https://www.zillow.com/rental-manager/market-trends/mammoth-lakes-ca/',
    'hoa': 'https://www.mammothlakesresortrealty.com/mammoth-lakes-condos-for-sale/',
    'tax': 'https://monocounty.ca.gov/tax/page/property-tax-rates',
    'tax_benchmark': 'https://www.ownwell.com/trends/california/mono-county/mammoth-lakes'
}

def fetch(url):
    req = Request(url, headers={'User-Agent':'Mozilla/5.0 MammothRentBuyDashboard/2.0'})
    with urlopen(req, timeout=15) as r:
        return r.read().decode('utf-8', errors='ignore')

def first_float(patterns, text):
    for p in patterns:
        m = re.search(p, text, re.I|re.S)
        if m:
            return float(m.group(1).replace(',',''))
    return None

def live_market_data():
    now = datetime.now(timezone.utc).isoformat()
    out = {
      'updated_at': now,
      'mortgage_rate': 6.55,
      'one_bed_rent': 2985,
      'overall_rent': 3980,
      'hoa_benchmark': 900,
      'hoa_range_low': 550,
      'hoa_range_high': 2000,
      'property_tax_rate': 1.16,
      'insurance_monthly': 125,
      'insurance_note': 'Editable planning estimate; no authoritative live Mammoth condo-policy average is published.',
      'sources': SOURCES,
      'status': {}
    }
    try:
        t=fetch(SOURCES['mortgage'])
        x=first_float([r'30-year fixed-rate mortgage averaged\s*([0-9.]+)%',r'30-Yr FRM[^0-9]+([0-9.]+)%'],t)
        if x: out['mortgage_rate']=x
        out['status']['mortgage']='live'
    except Exception as e: out['status']['mortgage']='fallback: '+str(e)[:90]
    try:
        t=fetch(SOURCES['rent'])
        x=first_float([r'one-bedroom apartment[^$]{0,150}\$([0-9,]+)',r'one bedroom[^$]{0,150}\$([0-9,]+)'],t)
        y=first_float([r'average rent in Mammoth Lakes[^$]{0,100}\$([0-9,]+)'],t)
        if x: out['one_bed_rent']=x
        if y: out['overall_rent']=y
        out['status']['rent']='live'
    except Exception as e: out['status']['rent']='fallback: '+str(e)[:90]
    try:
        t=fetch(SOURCES['hoa'])
        lo=first_float([r'HOA averages are approximately\s*\$([0-9,]+)'],t)
        hi=first_float([r'up to\s*\$([0-9,]+)'],t)
        if lo: out['hoa_range_low']=lo
        if hi: out['hoa_range_high']=hi
        # A conservative central planning benchmark, not a published statistical average.
        out['hoa_benchmark']=round((out['hoa_range_low']+min(out['hoa_range_high'],1250))/2)
        out['status']['hoa']='live range; benchmark estimated'
    except Exception as e: out['status']['hoa']='fallback: '+str(e)[:90]
    try:
        t=fetch(SOURCES['tax_benchmark'])
        x=first_float([r'median effective property tax rate of\s*([0-9.]+)%'],t)
        if x: out['property_tax_rate']=x
        out['status']['tax']='live benchmark'
    except Exception as e: out['status']['tax']='fallback: '+str(e)[:90]
    out['status']['insurance']='editable estimate'
    return out

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/market'):
            data=json.dumps(live_market_data()).encode()
            self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path=='/': self.path='/index.html'
        if self.path.startswith('/share/'):
            self.path='/index.html'
        return super().do_GET()
    def log_message(self, fmt, *args):
        pass

def main():
    os.chdir(ROOT)
    host = os.environ.get('HOST', '0.0.0.0')
    server=ThreadingHTTPServer((host,PORT),Handler)
    url=f'http://127.0.0.1:{PORT}'
    print(f'Ryan Mammoth Dashboard running at {url}')
    if os.environ.get('OPEN_BROWSER', '1') == '1' and not os.environ.get('RENDER'):
        threading.Timer(0.8, lambda:webbrowser.open(url)).start()
    try: server.serve_forever()
    except KeyboardInterrupt: pass

if __name__=='__main__': main()
