#!/usr/bin/env python3
import hashlib, ipaddress, json, os, re, threading, time, webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse, parse_qs, urlencode

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

# Citywide/countywide median listing-price-per-square-foot planning proxies.
# These are not ADU comparable-sale appraisals. Sparse locations use a
# clearly identified nearby or county-level fallback and remain editable.
ADU_MARKET_PSF={
 'mammoth': {'value':672,'source':'https://www.realtor.com/local/market/california/mono-county/mammoth-lakes','note':'Mammoth Lakes citywide median listing $/sq ft (June 2026).'},
 'june-lake': {'value':566,'source':'https://www.realtor.com/local/market/california/mono-county/june-lake','note':'June Lake / 93529 listing $/sq ft benchmark (2026).'},
 'crowley-lake': {'value':638,'source':'https://www.realtor.com/local/market/california/mono-county','note':'Mono County fallback because Crowley Lake has sparse direct data.'},
 'toms-place': {'value':667,'source':'https://www.realtor.com/local/market/california/mono-county/toms-place','note':"Tom's Place listing $/sq ft benchmark (2026)."},
 'lee-vining': {'value':638,'source':'https://www.realtor.com/local/market/california/mono-county','note':'Mono County fallback because Lee Vining has sparse direct data.'},
 'bridgeport': {'value':638,'source':'https://www.realtor.com/local/market/california/mono-county','note':'Mono County fallback because Bridgeport has sparse direct data.'},
 'benton': {'value':344,'source':'https://www.realtor.com/local/market/california/inyo-county','note':'Inyo County fallback because Benton has sparse direct data.'},
 'bishop': {'value':359,'source':'https://www.realtor.com/local/market/california/inyo-county/bishop','note':'Bishop citywide median listing $/sq ft (June 2026).'},
 'big-pine': {'value':344,'source':'https://www.realtor.com/local/market/california/inyo-county','note':'Inyo County fallback because Big Pine has sparse direct data.'},
 'paradise-sunny-slopes': {'value':359,'source':'https://www.realtor.com/local/market/california/mono-county/hammil-valley','note':'Nearby Hammil Valley / north Bishop-area planning proxy.'},
 'swall-meadows': {'value':359,'source':'https://www.realtor.com/local/market/california/mono-county/hammil-valley','note':'Nearby Hammil Valley planning proxy for sparse Swall Meadows data.'},
 'chalfant': {'value':359,'source':'https://www.realtor.com/local/market/california/mono-county/hammil-valley','note':'Nearby Hammil Valley planning proxy for sparse Chalfant data.'},
 'independence': {'value':344,'source':'https://www.realtor.com/local/market/california/inyo-county','note':'Inyo County fallback because Independence has sparse direct data.'},
 'lone-pine': {'value':288,'source':'https://www.realtor.com/local/market/california/inyo-county/lone-pine','note':'Lone Pine citywide median listing $/sq ft (June 2026).'},
 'carson-city': {'value':320,'source':'https://www.realtor.com/local/market/nevada/carson-city','note':'Carson City citywide median listing $/sq ft (2026).'},
 'gardnerville': {'value':410,'source':'https://www.realtor.com/local/market/nevada/douglas-county/gardnerville','note':'Gardnerville citywide median listing $/sq ft (June 2026).'},
 'truckee': {'value':594,'source':'https://www.realtor.com/local/market/california/nevada-county/truckee','note':'Truckee citywide median listing $/sq ft (June 2026).'},
 'sonora': {'value':269,'source':'https://www.realtor.com/local/market/california/tuolumne-county/sonora','note':'Sonora citywide median listing $/sq ft (June 2026).'},
 'fresno': {'value':249,'source':'https://www.realtor.com/realestateandhomes-search/Fresno_CA','note':'Fresno citywide median listing $/sq ft (2026).'},
 'south-lake-tahoe': {'value':502,'source':'https://www.realtor.com/local/market/california/el-dorado-county/south-lake-tahoe','note':'South Lake Tahoe citywide median listing $/sq ft (June 2026).'},
 'incline-village': {'value':846,'source':'https://www.realtor.com/local/market/nevada/washoe-county/incline-village','note':'Incline Village citywide median listing $/sq ft (June 2026).'},
 'stateline': {'value':645,'source':'https://www.realtor.com/local/market/nevada/douglas-county/stateline','note':'Stateline citywide median listing $/sq ft (2026).'},
 'zephyr-cove': {'value':1005,'source':'https://www.realtor.com/local/market/nevada/douglas-county/zephyr-cove','note':'Zephyr Cove citywide median listing $/sq ft (2026); luxury mix can overstate an ADU.'},
 'custom': {'value':300,'source':'','note':'Editable placeholder. Enter a local market $/sq ft estimate.'},
}


# Location-adjusted detached-ADU build-cost planning assumptions.
# These are deliberately editable starting points, not contractor bids.
# They use the statewide California ADU cost research as a floor and place
# remote/high-cost mountain markets toward the upper end of current ranges.
ADU_BUILD_PSF={
 'mammoth': {'value':500,'note':'Remote high-cost mountain-market planning assumption.'},
 'june-lake': {'value':475,'note':'Remote mountain-market planning assumption.'},
 'crowley-lake': {'value':450,'note':'Eastern Sierra planning assumption.'},
 'toms-place': {'value':450,'note':'Eastern Sierra planning assumption.'},
 'lee-vining': {'value':475,'note':'Remote Eastern Sierra planning assumption.'},
 'bridgeport': {'value':450,'note':'Remote Eastern Sierra planning assumption.'},
 'benton': {'value':350,'note':'Rural Eastern California planning assumption.'},
 'bishop': {'value':350,'note':'Bishop / Owens Valley planning assumption.'},
 'big-pine': {'value':350,'note':'Owens Valley planning assumption.'},
 'paradise-sunny-slopes': {'value':375,'note':'North Bishop / mountain-community planning assumption.'},
 'swall-meadows': {'value':375,'note':'North Bishop / mountain-community planning assumption.'},
 'chalfant': {'value':350,'note':'North Bishop-area planning assumption.'},
 'independence': {'value':325,'note':'Southern Owens Valley planning assumption.'},
 'lone-pine': {'value':325,'note':'Southern Owens Valley planning assumption.'},
 'carson-city': {'value':350,'note':'Carson City planning assumption.'},
 'gardnerville': {'value':350,'note':'Carson Valley planning assumption.'},
 'truckee': {'value':475,'note':'High-cost Sierra resort-market planning assumption.'},
 'sonora': {'value':325,'note':'Sierra foothill planning assumption.'},
 'fresno': {'value':300,'note':'Central Valley planning assumption.'},
 'south-lake-tahoe': {'value':450,'note':'High-cost Tahoe planning assumption.'},
 'incline-village': {'value':500,'note':'High-cost Tahoe resort-market planning assumption.'},
 'stateline': {'value':475,'note':'High-cost Tahoe resort-market planning assumption.'},
 'zephyr-cove': {'value':500,'note':'High-cost Tahoe resort-market planning assumption.'},
 'custom': {'value':350,'note':'Editable generic planning assumption.'},
}
ADU_BUILD_COST_SOURCE='https://ternercenter.berkeley.edu/blog/cci-adu-survey/'


# USDA Single Family Housing Guaranteed Loan Program FY 2026 adjusted
# income limits, effective 07-13-2026. USDA groups household sizes 1-4
# together and 5-8 together for the moderate-income guaranteed-loan limit.
USDA_GUARANTEED_LIMIT_SOURCE='https://www.rd.usda.gov/files/rd-grhlimitmap.pdf'
USDA_ELIGIBILITY_CHECKER='https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do?pageAction=sfp'
USDA_INCOME_CHECKER='https://eligibility.sc.egov.usda.gov/eligibility/incomeEligibilityAction.do?pageAction=state'

USDA_AREAS={
 'mono-ca': {
   'area':'Mono County, CA',
   'one_four':129150,
   'five_eight':170500,
 },
 'inyo-ca': {
   'area':'Inyo County, CA',
   'one_four':124900,
   'five_eight':164900,
 },
 'fresno-ca': {
   'area':'Fresno, CA HUD Metro FMR Area',
   'one_four':124900,
   'five_eight':164900,
 },
 'nevada-ca': {
   'area':'Nevada County, CA',
   'one_four':143850,
   'five_eight':189950,
 },
 'tuolumne-ca': {
   'area':'Tuolumne County, CA',
   'one_four':124900,
   'five_eight':164900,
 },
 'el-dorado-ca': {
   'area':'El Dorado County / Sacramento HUD Metro area, CA',
   'one_four':151100,
   'five_eight':199500,
 },
 'carson-city-nv': {
   'area':'Carson City, NV MSA',
   'one_four':122800,
   'five_eight':162100,
 },
 'douglas-nv': {
   'area':'Douglas County, NV',
   'one_four':128250,
   'five_eight':169300,
 },
 'washoe-nv': {
   'area':'Reno, NV HUD Metro FMR Area (Washoe County)',
   'one_four':134350,
   'five_eight':177350,
 },
 'custom': {
   'area':'Select or enter a location',
   'one_four':None,
   'five_eight':None,
 },
}

USDA_LOCATION_AREA={
 'mammoth':'mono-ca',
 'june-lake':'mono-ca',
 'crowley-lake':'mono-ca',
 'toms-place':'mono-ca',
 'lee-vining':'mono-ca',
 'bridgeport':'mono-ca',
 'benton':'mono-ca',
 'paradise-sunny-slopes':'mono-ca',
 'swall-meadows':'mono-ca',
 'chalfant':'mono-ca',
 'bishop':'inyo-ca',
 'big-pine':'inyo-ca',
 'independence':'inyo-ca',
 'lone-pine':'inyo-ca',
 'carson-city':'carson-city-nv',
 'gardnerville':'douglas-nv',
 'truckee':'nevada-ca',
 'sonora':'tuolumne-ca',
 'fresno':'fresno-ca',
 'south-lake-tahoe':'el-dorado-ca',
 'incline-village':'washoe-nv',
 'stateline':'douglas-nv',
 'zephyr-cove':'douglas-nv',
 'custom':'custom',
}

def usda_limits_for_location(location):
    key=USDA_LOCATION_AREA.get(location,'custom')
    data=USDA_AREAS[key].copy()
    data.update({
        'effective_date':'July 13, 2026',
        'fiscal_year':2026,
        'source':USDA_GUARANTEED_LIMIT_SOURCE,
        'eligibility_checker':USDA_ELIGIBILITY_CHECKER,
        'income_checker':USDA_INCOME_CHECKER,
    })
    return data

MORTGAGE_URL='https://www.freddiemac.com/pmms'

def fetch(url):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 HouseAlpha/35.0'})
    with urlopen(req,timeout=10) as r:
        return r.read().decode('utf-8',errors='ignore')

PROPERTY_LOOKUP_SCHEMA=1
PROPERTY_LOOKUP_CACHE_TTL=15*60
PROPERTY_LOOKUP_CACHE_MAX=64
PROPERTY_LOOKUP_BODY_MAX=4096
PROPERTY_LOOKUP_RATE_WINDOW=10*60
PROPERTY_LOOKUP_RATE_MAX=12
PROPERTY_LOOKUP_SEMAPHORE=threading.BoundedSemaphore(3)
PROPERTY_LOOKUP_LOCK=threading.Lock()
PROPERTY_LOOKUP_SALT=os.urandom(32)
PROPERTY_LOOKUP_CACHE={}
PROPERTY_LOOKUP_RATE={}
try:RENTCAST_PROCESS_CALL_MAX=max(0,int(os.environ.get('RENTCAST_PROCESS_CALL_LIMIT','45')))
except ValueError:RENTCAST_PROCESS_CALL_MAX=45
RENTCAST_PROCESS_CALL_COUNT=0
RENTCAST_BASE='https://api.rentcast.io/v1'
CENSUS_GEOCODER='https://geocoding.geo.census.gov/geocoder/locations/onelineaddress'

BENCHMARK_BY_CITY_STATE={
    ('MAMMOTH LAKES','CA'):'mammoth',('JUNE LAKE','CA'):'june-lake',('CROWLEY LAKE','CA'):'crowley-lake',
    ("TOM'S PLACE",'CA'):'toms-place',('LEE VINING','CA'):'lee-vining',('BRIDGEPORT','CA'):'bridgeport',
    ('BENTON','CA'):'benton',('BISHOP','CA'):'bishop',('BIG PINE','CA'):'big-pine',
    ('PARADISE','CA'):'paradise-sunny-slopes',('SWALL MEADOWS','CA'):'swall-meadows',('CHALFANT','CA'):'chalfant',
    ('INDEPENDENCE','CA'):'independence',('LONE PINE','CA'):'lone-pine',('CARSON CITY','NV'):'carson-city',
    ('GARDNERVILLE','NV'):'gardnerville',('TRUCKEE','CA'):'truckee',('SONORA','CA'):'sonora',
    ('FRESNO','CA'):'fresno',('SOUTH LAKE TAHOE','CA'):'south-lake-tahoe',
    ('INCLINE VILLAGE','NV'):'incline-village',('STATELINE','NV'):'stateline',('ZEPHYR COVE','NV'):'zephyr-cove',
}

def fetch_json(url,headers=None,timeout=9,max_bytes=2_000_000):
    request_headers={'User-Agent':'Mozilla/5.0 HouseAlpha/35.0','Accept':'application/json'}
    request_headers.update(headers or {})
    req=Request(url,headers=request_headers)
    with urlopen(req,timeout=timeout) as response:
        raw=response.read(max_bytes+1)
        if len(raw)>max_bytes: raise ValueError('Upstream response too large')
        return json.loads(raw.decode('utf-8'))

def clean_lookup_address(value):
    if not isinstance(value,str): raise ValueError('Enter a street address.')
    if any(ord(char)<32 for char in value): raise ValueError('The address contains unsupported characters.')
    value=' '.join(value.split())
    if len(value)<8: raise ValueError('Enter a fuller street address, including city and state.')
    if len(value)>180: raise ValueError('The address is too long.')
    return value

def lookup_hash(value):
    return hashlib.sha256(PROPERTY_LOOKUP_SALT+value.casefold().encode('utf-8')).hexdigest()

def lookup_rate_allowed(client_value):
    now=time.monotonic();key=lookup_hash(client_value or 'unknown')
    with PROPERTY_LOOKUP_LOCK:
        recent=[stamp for stamp in PROPERTY_LOOKUP_RATE.get(key,[]) if now-stamp<PROPERTY_LOOKUP_RATE_WINDOW]
        if len(recent)>=PROPERTY_LOOKUP_RATE_MAX:
            PROPERTY_LOOKUP_RATE[key]=recent
            return False
        recent.append(now);PROPERTY_LOOKUP_RATE[key]=recent
        if len(PROPERTY_LOOKUP_RATE)>256:
            for old_key in list(PROPERTY_LOOKUP_RATE)[:64]: PROPERTY_LOOKUP_RATE.pop(old_key,None)
    return True

def reserve_provider_calls(count):
    global RENTCAST_PROCESS_CALL_COUNT
    with PROPERTY_LOOKUP_LOCK:
        if RENTCAST_PROCESS_CALL_COUNT+count>RENTCAST_PROCESS_CALL_MAX:return False
        RENTCAST_PROCESS_CALL_COUNT+=count
        return True

def lookup_client_address(handler):
    peer=str(handler.client_address[0] or 'unknown')
    if not os.environ.get('RENDER'):return peer
    forwarded=str(handler.headers.get('X-Forwarded-For','')).split(',')[0].strip()
    try:return ipaddress.ip_address(forwarded).compressed
    except ValueError:return peer

def finite_number(value,minimum=None,maximum=None):
    if isinstance(value,bool): return None
    try: number=float(value)
    except (TypeError,ValueError): return None
    if not (-float('inf')<number<float('inf')): return None
    if minimum is not None and number<minimum: return None
    if maximum is not None and number>maximum: return None
    return number

def normalized_property_type(value):
    text=str(value or '').casefold()
    if any(word in text for word in ('condo','townhouse','townhome')): return 'condo'
    if text in ('single family','single-family') or 'single family' in text: return 'single'
    return None

ADDRESS_WORDS={
    'STREET':'ST','ROAD':'RD','AVENUE':'AVE','BOULEVARD':'BLVD','DRIVE':'DR','LANE':'LN','COURT':'CT',
    'PLACE':'PL','PARKWAY':'PKWY','HIGHWAY':'HWY','CIRCLE':'CIR','TRAIL':'TRL','TERRACE':'TER',
    'NORTH':'N','SOUTH':'S','EAST':'E','WEST':'W','BUILDING':'BLDG','FLOOR':'FL',
}

def component_unit_match(value,allow_textual_ste=True):
    text=str(value or '').upper()
    match=re.search(r'(?:\b(?:APT|APARTMENT|UNIT|SUITE)\b\.?\s*#?\s*|#\s*)([A-Z0-9-]+)',text)
    if match:return match
    suffix=r'([A-Z0-9-]+)' if allow_textual_ste else r'([A-Z]*\d[A-Z0-9-]*|[A-Z])'
    return re.search(r'\bSTE\b\.?\s*#?\s*'+suffix+r'\b',text)

def address_unit(value):
    text=str(value or '').upper()
    parts=[part.strip() for part in text.split(',') if part.strip()]
    if len(parts)<3:
        match=component_unit_match(text,False)
        return match.group(1) if match else None
    state_index=None
    for index in range(len(parts)-1,0,-1):
        if re.fullmatch(r'[A-Z]{2}(?:\s+\d{5}(?:-\d{4})?)?',parts[index]):state_index=index;break
    components=[parts[0]]
    if state_index and state_index>2:components.extend(parts[1:state_index-1])
    for component in components:
        match=component_unit_match(component,True)
        if match:return match.group(1)
    return None

def preserve_address_unit(canonical,entered):
    unit=address_unit(entered)
    if not unit or address_unit(canonical):return canonical
    comma=canonical.find(',')
    return f'{canonical} UNIT {unit}' if comma<0 else f'{canonical[:comma]} UNIT {unit}{canonical[comma:]}'

def parsed_address_identity(value):
    text=str(value or '').strip().upper()
    if not text:return None
    parts=[part.strip() for part in text.split(',') if part.strip()]
    if len(parts)<3:return None
    number_match=re.match(r'\s*(\d+[A-Z-]*)\b',parts[0])
    state=None;state_index=None;state_zip=None
    for index in range(len(parts)-1,0,-1):
        match=re.fullmatch(r'([A-Z]{2})(?:\s+(\d{5})(?:-\d{4})?)?',parts[index])
        if match:state=match.group(1);state_index=index;state_zip=match.group(2);break
    city=tuple(re.findall(r'[A-Z0-9]+',parts[state_index-1])) if state_index and state_index>1 else ()
    unit_values=[];secondary=[]
    street_part=parts[0];street_unit=component_unit_match(street_part,True)
    if street_unit:
        unit_values.append(street_unit.group(1));secondary.extend(re.findall(r'[A-Z0-9]+',street_part[street_unit.end():]));street_part=street_part[:street_unit.start()]
    words=re.findall(r'[A-Z0-9]+',street_part)
    if words and number_match:words=words[1:]
    words=tuple(ADDRESS_WORDS.get(word,word) for word in words)
    if state_index and state_index>2:
        for part in parts[1:state_index-1]:
            unit_match=component_unit_match(part,True)
            if unit_match:
                unit_values.append(unit_match.group(1));residual=part[:unit_match.start()]+' '+part[unit_match.end():];secondary.extend(re.findall(r'[A-Z0-9]+',residual))
            else:secondary.extend(re.findall(r'[A-Z0-9]+',part))
    units={value for value in unit_values if value}
    if len(units)>1:return None
    unit=next(iter(units),None)
    secondary=tuple(ADDRESS_WORDS.get(word,word) for word in secondary)
    trailing_zip=None
    trailing_parts=parts[state_index+1:] if state_index is not None else []
    if trailing_parts:
        if state_zip or len(trailing_parts)!=1:return None
        trailing_match=re.fullmatch(r'(\d{5})(?:-\d{4})?',trailing_parts[0])
        if not trailing_match:return None
        trailing_zip=trailing_match.group(1)
    if not number_match or not words or not city or not state:return None
    return {'number':number_match.group(1),'street':words,'city':city,'state':state,'zip':state_zip or trailing_zip,'unit':unit,'secondary':secondary}

def compatible_property_address(candidate,requested):
    candidate_id=parsed_address_identity(candidate);requested_id=parsed_address_identity(requested)
    if not candidate_id or not requested_id:return False
    for key in ('number','street','city','state','secondary'):
        if candidate_id[key]!=requested_id[key]:return False
    if candidate_id['zip'] and requested_id['zip'] and candidate_id['zip']!=requested_id['zip']:return False
    if candidate_id['unit']!=requested_id['unit']:return False
    return True

def latest_tax_record(records):
    if not isinstance(records,dict) or not records: return None
    for key in sorted(records,reverse=True):
        record=records.get(key)
        if isinstance(record,dict):
            total=finite_number(record.get('total'),0,10_000_000)
            if total is not None:return {'value':round(total,2),'year':str(record.get('year') or key)}
    return None

def census_address_match(address):
    url=CENSUS_GEOCODER+'?'+urlencode({'address':address,'benchmark':'Public_AR_Current','format':'json'})
    payload=fetch_json(url,timeout=8,max_bytes=750_000)
    matches=payload.get('result',{}).get('addressMatches',[])
    if not isinstance(matches,list): return []
    clean=[]
    for item in matches[:4]:
        if not isinstance(item,dict):continue
        components=item.get('addressComponents') if isinstance(item.get('addressComponents'),dict) else {}
        matched=str(item.get('matchedAddress') or '').strip()
        if not matched:continue
        clean.append({'address':matched,'city':str(components.get('city') or '').strip(),'state':str(components.get('state') or '').strip(),'zip':str(components.get('zip') or '').strip()})
    return clean

def rentcast_requests(address,api_key,include_rent=False):
    headers={'X-Api-Key':api_key}
    query=urlencode({'address':address,'suppressLogging':'true'})
    urls={
        'record':f'{RENTCAST_BASE}/properties?{query}',
        'listing':f'{RENTCAST_BASE}/listings/sale?{urlencode({"address":address,"status":"Active","limit":5,"suppressLogging":"true"})}',
    }
    if include_rent:urls['rent']=f'{RENTCAST_BASE}/avm/rent/long-term?{query}'
    results={};errors=[]
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures={name:executor.submit(fetch_json,url,headers) for name,url in urls.items()}
        for name,future in futures.items():
            try:results[name]=future.result()
            except Exception:errors.append(name)
    return results,errors

def build_property_lookup(address,use_mode='primary'):
    use_mode=use_mode if use_mode in ('primary','rental','livein') else 'primary'
    rentcast_key=os.environ.get('RENTCAST_API_KEY','').strip()
    cache_key=lookup_hash(address+'\0'+use_mode+'\0'+('connected' if rentcast_key else 'address-only'));now=time.monotonic()
    with PROPERTY_LOOKUP_LOCK:
        cached=PROPERTY_LOOKUP_CACHE.get(cache_key)
        if cached and now-cached[0]<PROPERTY_LOOKUP_CACHE_TTL:return cached[1]
    census_matches=[];census_failed=False;provider_results={};provider_errors=[];provider_budget_reached=False
    try:census_matches=census_address_match(address)
    except Exception:census_failed=True
    parsed_requested=parsed_address_identity(address)
    requested_match_address=address if parsed_requested else (preserve_address_unit(census_matches[0]['address'],address) if len(census_matches)==1 else address)
    provider_address=requested_match_address
    # Enrich only a caller-entered, parser-complete identity. If Census had to
    # canonicalize an unparseable string, return that address for review first;
    # this prevents dropped/unknown unit aliases from inheriting building facts.
    provider_eligible=bool(parsed_requested) and len(census_matches)<=1
    provider_call_count=2+(1 if use_mode in ('rental','livein') else 0)
    provider_allowed=bool(rentcast_key) and provider_eligible and reserve_provider_calls(provider_call_count)
    if rentcast_key and provider_eligible and not provider_allowed:provider_budget_reached=True
    if provider_allowed:
        try:provider_results,provider_errors=rentcast_requests(provider_address,rentcast_key,use_mode in ('rental','livein'))
        except Exception:provider_errors=['record','listing']+(['rent'] if use_mode in ('rental','livein') else [])
    raw_records=provider_results.get('record')
    all_records=raw_records if isinstance(raw_records,list) else []
    records=[item for item in all_records if isinstance(item,dict) and compatible_property_address(item.get('formattedAddress'),requested_match_address)]
    record=records[0] if len(records)==1 and isinstance(records[0],dict) else None
    raw_listings=provider_results.get('listing')
    all_listings=raw_listings if isinstance(raw_listings,list) else []
    listings=[item for item in all_listings if isinstance(item,dict) and compatible_property_address(item.get('formattedAddress'),requested_match_address)]
    active=[item for item in listings if isinstance(item,dict) and str(item.get('status') or '').casefold()=='active']
    listing=active[0] if len(active)==1 else None
    rent=provider_results.get('rent') if isinstance(provider_results.get('rent'),dict) else None
    rent_subject=rent.get('subjectProperty') if rent and isinstance(rent.get('subjectProperty'),dict) else None
    if rent and (not rent_subject or not compatible_property_address(rent_subject.get('formattedAddress'),requested_match_address)):rent=None
    if not rent:rent_subject=None
    retrieved_at=datetime.now(timezone.utc).isoformat()
    subject_sources=[
        (listing,'Active listing',(listing or {}).get('lastSeenDate') or (listing or {}).get('listedDate') or retrieved_at),
        (record,'Property record',retrieved_at),
        (rent_subject,'Rent estimate subject',retrieved_at),
    ]
    subject_sources=[item for item in subject_sources if isinstance(item[0],dict)]
    subject=subject_sources[0][0] if subject_sources else {}
    def sourced(field):
        for source,label,as_of in subject_sources:
            value=source.get(field)
            if value is not None:return value,label,as_of
        return None,None,None
    canonical_value,_,_=sourced('formattedAddress');city_value,_,_=sourced('city');state_value,_,_=sourced('state')
    canonical=str(canonical_value or (census_matches[0]['address'] if len(census_matches)==1 else address)).strip()
    city=str(city_value or (census_matches[0]['city'] if len(census_matches)==1 else '')).strip()
    state=str(state_value or (census_matches[0]['state'] if len(census_matches)==1 else '')).strip().upper()
    benchmark_key=BENCHMARK_BY_CITY_STATE.get((city.upper(),state),'custom') if city and state else None
    facts={};warnings=[]

    raw_type,type_source,type_as_of=sourced('propertyType')
    ptype=normalized_property_type(raw_type)
    unsupported_type=not ptype
    ask=finite_number(listing.get('price') if listing else None,1_000,100_000_000)
    if ask is not None and ptype:
        facts['asking_price']={'value':round(ask),'unit':'USD','source':'Active sale listing','as_of':listing.get('lastSeenDate') or listing.get('listedDate'),'confidence':'high'}
    elif len(active)>1:warnings.append('More than one active sale listing matched, so no asking price was suggested.')
    if ptype:facts['property_type']={'value':ptype,'display':str(raw_type),'source':type_source,'as_of':type_as_of,'confidence':'high'}
    raw_beds,beds_source,beds_as_of=sourced('bedrooms');beds=finite_number(raw_beds,1,4)
    if ptype and beds is not None and float(beds).is_integer():facts['bedrooms']={'value':int(beds),'source':beds_source,'as_of':beds_as_of,'confidence':'high'}
    hoa=hoa_source=hoa_as_of=None
    for source,label,as_of in subject_sources:
        hoa_data=source.get('hoa')
        fee=finite_number(hoa_data.get('fee') if isinstance(hoa_data,dict) else None,0,100_000)
        if fee is not None:hoa=fee;hoa_source=label;hoa_as_of=as_of;break
    if hoa is not None and ptype:facts['hoa_monthly']={'value':round(hoa,2),'unit':'USD/month','source':hoa_source,'as_of':hoa_as_of,'confidence':'medium'}
    rent_value=finite_number(rent.get('rent') if rent else None,100,1_000_000)
    if rent_value is not None and ptype in ('single','condo'):
        facts['rent_monthly']={'value':round(rent_value),'unit':'USD/month','range_low':finite_number(rent.get('rentRangeLow'),0),'range_high':finite_number(rent.get('rentRangeHigh'),0),'source':'Rent estimate','as_of':retrieved_at,'confidence':'medium'}
    tax=latest_tax_record(record.get('propertyTaxes') if record else None)
    if tax:facts['property_tax_annual']={**tax,'unit':'USD/year','source':'County tax record','as_of':tax['year'],'confidence':'medium','reference_only':True}

    details={}
    if raw_type:details['provider_property_type']=str(raw_type)
    for key,label,minimum,maximum in [('bathrooms','bathrooms',0,100),('squareFootage','square_feet',1,1_000_000),('yearBuilt','year_built',1600,datetime.now().year+2)]:
        raw_value,_,_=sourced(key);value=finite_number(raw_value,minimum,maximum)
        if value is not None:details[label]=int(value) if float(value).is_integer() else value
    if record is None and len(records)>1:warnings.append('More than one property record matched; record-only facts were not suggested.')
    if (all_records and not records) or (all_listings and not listings):warnings.append('Provider results did not match the requested street number, ZIP, or unit, so those facts were not suggested.')
    if unsupported_type and (ask is not None or hoa is not None or rent_value is not None):
        if raw_type:warnings.append(f'The provider classified this as {raw_type}, which House Alpha does not model directly; asking price, HOA, bedrooms, and rent were left for manual review.')
        else:warnings.append('A supported single-family or condo property type could not be established, so asking price, HOA, bedrooms, and rent were left for manual review.')
    if tax:warnings.append('The reported tax bill is reference only and was not converted into a buyer tax rate.')
    if rent_value is not None:warnings.append('The rent figure is a provider estimate, not a signed lease or verified rent comp.')
    if census_failed:warnings.append('The U.S. Census address matcher was temporarily unavailable.')
    if provider_errors and rentcast_key:warnings.append('Some property-data sources were unavailable, so this result may be partial.')
    if provider_budget_reached:warnings.append('The property-data lookup allowance is currently reached; the address match still works and manual entry remains available.')
    canonical_review_required=bool(rentcast_key) and not parsed_requested and len(census_matches)==1
    if canonical_review_required:warnings.append('Review and apply the matched address, then choose Find property facts again for exact property-data enrichment.')
    matched=bool(census_matches or subject)
    response={
        'schema_version':PROPERTY_LOOKUP_SCHEMA,
        'status':'enriched' if facts else ('matched' if matched else 'not_found'),
        'match':{'canonical_address':canonical if matched else None,'source':'RentCast property data' if subject else 'U.S. Census Geocoder','retrieved_at':retrieved_at},
        'address_matches':census_matches if len(census_matches)>1 and not subject else [],
        'benchmark':{'key':benchmark_key,'name':LOCATIONS[benchmark_key]['name']} if benchmark_key in LOCATIONS else None,
        'provider':{'connected':bool(rentcast_key),'name':'RentCast' if rentcast_key else None,'enrichment_status':'canonical_review_required' if canonical_review_required else 'budget_reached' if provider_budget_reached else 'partial' if provider_errors and facts else 'available' if facts else 'unavailable' if rentcast_key else 'not_connected'},
        'facts':facts,'details':details,'warnings':warnings,
    }
    if not matched and census_failed and not provider_results:raise RuntimeError('lookup_unavailable')
    with PROPERTY_LOOKUP_LOCK:
        if len(PROPERTY_LOOKUP_CACHE)>=PROPERTY_LOOKUP_CACHE_MAX:
            oldest=min(PROPERTY_LOOKUP_CACHE,key=lambda key:PROPERTY_LOOKUP_CACHE[key][0]);PROPERTY_LOOKUP_CACHE.pop(oldest,None)
        PROPERTY_LOOKUP_CACHE[cache_key]=(now,response)
    return response

def first_float(patterns,text):
    for p in patterns:
        m=re.search(p,text,re.I|re.S)
        if m:return float(m.group(1).replace(',',''))
    return None

def property_rents(one_bed):
    # The public benchmark is generally closest to an apartment/condo 1BR.
    # These type-and-bedroom adjustments are editable planning estimates,
    # particularly in small markets with few long-term rental listings.
    condo_factors = {'1': 1.00, '2': 1.30, '3': 1.58, '4': 1.86}
    single_factors = {'1': 1.12, '2': 1.48, '3': 1.90, '4': 2.30}
    return {
        'condo': {k: round(one_bed * f / 25) * 25 for k, f in condo_factors.items()},
        'single': {k: round(one_bed * f / 25) * 25 for k, f in single_factors.items()},
    }

def bedroom_rents(one_bed):
    # Backward-compatible condo/apartment estimates.
    return property_rents(one_bed)['condo']

def bedroom_prices(home_value, property_type='condo'):
    # These are editable planning estimates, not appraisals. The overall local
    # home-value benchmark is adjusted by property size and type.
    if property_type == 'single':
        factors = {'1': 0.65, '2': 0.82, '3': 1.00, '4': 1.25}
    else:
        factors = {'1': 0.48, '2': 0.70, '3': 0.92, '4': 1.10}
    return {k: round(home_value * f / 1000) * 1000 for k, f in factors.items()}

def market(location='mammoth'):
    if location not in LOCATIONS:
        raise ValueError(f'Unknown location: {location}')
    loc=LOCATIONS[location].copy()
    out={
        'updated_at':datetime.now(timezone.utc).isoformat(),
        'mortgage_rate':6.69,
        'mortgage_rate_date':'August 6, 2026',
        'mortgage_benchmark_note':'Freddie Mac PMMS conventional conforming benchmark at 80% LTV or less',
        'location_key':location,
        **loc,
        'status':{}
    }
    def mortgage_update():
        try:
            text=fetch(MORTGAGE_URL)
            rate=first_float([r'30-year fixed-rate mortgage averaged\s*([0-9.]+)%',r'30-Yr FRM[^0-9]+([0-9.]+)%'],text)
            if rate is None: raise ValueError('Mortgage rate not found')
            date_match=re.search(r'as of\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',text,re.I)
            values={'mortgage_rate':rate}
            if date_match: values['mortgage_rate_date']=date_match.group(1)
            return values,'Updated from Freddie Mac PMMS'
        except Exception:
            return {},'Using saved weekly Freddie Mac benchmark'

    def rent_update():
        try:
            if not loc.get('source'): raise ValueError('No live source')
            text=fetch(loc['source'])
            rent=first_float([r'one-bedroom apartment[^$]{0,220}\$([0-9,]+)',r'one bedroom[^$]{0,220}\$([0-9,]+)'],text)
            if rent is None: raise ValueError('Rent value not found')
            return {'rent':rent},'Updated from public rental-market page'
        except Exception:
            return {},'Saved planning benchmark — live source unavailable'

    def home_value_update():
        try:
            if not loc.get('home_source'): raise ValueError('No live home-value source')
            text=fetch(loc['home_source'])
            value=first_float([
                r'average[^$]{0,100}home value[^$]{0,50}\$([0-9,]+)',
                r'Typical Home Values[^$]{0,30}\$([0-9,]+)',
                r'##\s*\$([0-9,]+)'
            ],text)
            if value is None: raise ValueError('Home value not found')
            return {'home_value':value},'Updated from public home-value page'
        except Exception:
            return {},'Saved editable local home-value benchmark'

    jobs={'mortgage':mortgage_update,'rent':rent_update,'home_value':home_value_update}
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures={name:executor.submit(job) for name,job in jobs.items()}
        for name,future in futures.items():
            values,status=future.result()
            out.update(values)
            out['status'][name]=status
    adu_psf=ADU_MARKET_PSF.get(location,ADU_MARKET_PSF['custom'])
    out['adu_market_psf']=adu_psf['value']
    out['adu_market_psf_source']=adu_psf['source']
    out['adu_market_psf_note']=adu_psf['note']
    adu_build=ADU_BUILD_PSF.get(location,ADU_BUILD_PSF['custom'])
    out['adu_build_psf']=adu_build['value']
    out['adu_build_psf_note']=adu_build['note']
    out['adu_build_cost_source']=ADU_BUILD_COST_SOURCE
    out['usda_limits']=usda_limits_for_location(location)
    out['property_rents']=property_rents(out['rent'])
    out['bedroom_rents']=out['property_rents']['condo']
    out['bedroom_prices']={
        'condo': bedroom_prices(out['home_value'],'condo'),
        'single': bedroom_prices(out['home_value'],'single')
    }
    out['status']['bedroom_rents']='Editable condo and single-family rent estimates anchored to the local 1BR benchmark'
    out['status']['property_rents']='Property-type and bedroom estimates; sparse markets require caution'
    out['status']['bedroom_prices']='Editable purchase-price estimates anchored to the local overall home-value benchmark'
    out['status']['hoa']='Location-specific editable condo benchmark'
    out['status']['insurance']='Editable home-insurance planning estimate'
    out['status']['storage']='Editable one-car garage / roughly 10×20 storage estimate'
    out['sources']={'mortgage':MORTGAGE_URL,'rent':loc.get('source',''),'home':loc.get('home_source','')}
    return out

class Handler(SimpleHTTPRequestHandler):
    def send_json(self,status,payload,extra_headers=None):
        data=json.dumps(payload,separators=(',',':')).encode()
        self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','private, no-store');self.send_header('X-Content-Type-Options','nosniff')
        for name,value in (extra_headers or {}).items():self.send_header(name,value)
        self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)

    def do_POST(self):
        u=urlparse(self.path)
        if u.path!='/api/property-lookup':self.send_json(404,{'error':'not_found'});return
        content_type=self.headers.get('Content-Type','').split(';')[0].strip().lower()
        if content_type!='application/json':self.send_json(415,{'error':'json_required','message':'Send the address as JSON.'});return
        try:length=int(self.headers.get('Content-Length','0'))
        except ValueError:length=0
        if length<2:self.send_json(400,{'error':'empty_request','message':'Enter a street address.'});return
        if length>PROPERTY_LOOKUP_BODY_MAX:self.send_json(413,{'error':'request_too_large','message':'The lookup request is too large.'});return
        origin=self.headers.get('Origin','').strip();host=self.headers.get('Host','').strip();local_host=host.startswith(('127.0.0.1:','localhost:'))
        if (not origin and not local_host) or (origin and urlparse(origin).netloc!=host):self.send_json(403,{'error':'origin_not_allowed'});return
        try:
            body=json.loads(self.rfile.read(length).decode('utf-8'))
            if not isinstance(body,dict) or 'address' not in body or not set(body).issubset({'address','use_mode'}):raise ValueError('Send only an address and property use.')
            address=clean_lookup_address(body.get('address'))
            use_mode=body.get('use_mode','primary')
            if use_mode not in ('primary','rental','livein'):raise ValueError('Choose a supported property use.')
        except (UnicodeDecodeError,json.JSONDecodeError,ValueError) as error:
            self.send_json(400,{'error':'invalid_request','message':str(error) or 'Enter a valid street address.'});return
        client=lookup_client_address(self)
        if not lookup_rate_allowed(client):self.send_json(429,{'error':'rate_limited','message':'Too many property lookups. Try again in a few minutes.'},{'Retry-After':'60'});return
        if not PROPERTY_LOOKUP_SEMAPHORE.acquire(timeout=.25):self.send_json(503,{'error':'lookup_busy','message':'Property lookup is busy. Try again shortly.'},{'Retry-After':'15'});return
        try:
            try:self.send_json(200,build_property_lookup(address,use_mode))
            except Exception:self.send_json(502,{'error':'lookup_unavailable','message':'Property lookup is unavailable right now. Your inputs have not changed.'})
        finally:PROPERTY_LOOKUP_SEMAPHORE.release()

    def do_GET(self):
        u=urlparse(self.path)
        if u.path=='/api/market':
            q=parse_qs(u.query); location=q.get('location',['mammoth'])[0]
            if location not in LOCATIONS:
                data=json.dumps({'error':'unknown_location','location_key':location}).encode()
                self.send_response(400);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            data=json.dumps(market(location)).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path=='/api/locations':
            data=json.dumps({k:{'name':v['name'],**v,
                'adu_market_psf':ADU_MARKET_PSF.get(k,ADU_MARKET_PSF['custom'])['value'],
                'adu_market_psf_source':ADU_MARKET_PSF.get(k,ADU_MARKET_PSF['custom'])['source'],
                'adu_market_psf_note':ADU_MARKET_PSF.get(k,ADU_MARKET_PSF['custom'])['note'],
                'adu_build_psf':ADU_BUILD_PSF.get(k,ADU_BUILD_PSF['custom'])['value'],
                'adu_build_psf_note':ADU_BUILD_PSF.get(k,ADU_BUILD_PSF['custom'])['note'],
                'adu_build_cost_source':ADU_BUILD_COST_SOURCE,
                'usda_limits':usda_limits_for_location(k),
                'property_rents':property_rents(v['rent']),
                'bedroom_rents':property_rents(v['rent'])['condo'],
                'bedroom_prices':{
                    'condo':bedroom_prices(v['home_value'],'condo'),
                    'single':bedroom_prices(v['home_value'],'single')
                }} for k,v in LOCATIONS.items()}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        if u.path in ('/','/index.html'):
            host=self.headers.get('Host','').strip()
            forwarded_proto=self.headers.get('X-Forwarded-Proto','').split(',')[0].strip().lower()
            proto=forwarded_proto if forwarded_proto in ('http','https') else ('http' if host.startswith(('127.0.0.1','localhost')) else 'https')
            origin=f'{proto}://{host}' if re.fullmatch(r'[A-Za-z0-9.-]+(?::\d{1,5})?',host) else ''
            data=(ROOT/'index.html').read_text(encoding='utf-8').replace('__HOUSE_ALPHA_ORIGIN__',origin).encode()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-cache');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
        return super().do_GET()
    def log_message(self,fmt,*args): pass

def main():
    os.chdir(ROOT);host=os.environ.get('HOST','0.0.0.0');server=ThreadingHTTPServer((host,PORT),Handler)
    url=f'http://127.0.0.1:{PORT}';print('House Alpha running at',url)
    if os.environ.get('OPEN_BROWSER','1')=='1' and not os.environ.get('RENDER'):threading.Timer(.8,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
if __name__=='__main__':main()
