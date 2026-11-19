import json, urllib.request, time, csv
ss=[c['id'] for c in json.load(open('ssf.json'))[1]]
IND={ # code: source
 'GOV_WGI_RQ.EST':3,'GOV_WGI_GE.EST':3,'GOV_WGI_RL.EST':3,'GOV_WGI_CC.EST':3,
 'IT.NET.SECR.P6':2,'IT.NET.USER.ZS':2,'EG.ELC.ACCS.ZS':2,'IC.ELC.OUTG.ZS':2,'IT.CEL.SETS.P2':2,'SP.POP.TOTL':2,'NY.GDP.PCAP.PP.KD':2,
 'account.t.d':28,'mobileaccount.t.d':28,'con18.s':28,'con19.s':28,'fin11d.s':28,'fin25e4c':28,'fin13_1a':28,'fin16':28,
}
rows=[]
for code,src in IND.items():
    url=f"https://api.worldbank.org/v2/country/{';'.join(ss)}/indicator/{code}?source={src}&format=json&per_page=20000&date=2015:2025"
    for a in range(3):
        try:
            d=json.load(urllib.request.urlopen(url,timeout=60))
            if len(d)<2: print('ERR',code,d); d=[{},[]]
            break
        except Exception as e: print('retry',code,e); time.sleep(3)
    n=0
    for r in (d[1] or []):
        if r['value'] is not None:
            rows.append([r['countryiso3code'] or r['country']['id'],code,r['date'],r['value']]);n+=1
    print(code,n,d[0].get('lastupdated'))
with open('wb_raw.csv','w',newline='') as f:
    w=csv.writer(f);w.writerow(['iso3','indicator','year','value']);w.writerows(rows)
