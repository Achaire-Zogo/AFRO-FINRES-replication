import json, urllib.request, sys, time
dois=[l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
try: out=json.load(open('verified.json'))
except: out={}
for doi in dois:
    if doi in out: continue
    for a in range(4):
        try:
            req=urllib.request.Request("https://doi.org/"+doi,headers={"Accept":"application/vnd.citationstyles.csl+json","User-Agent":"AFRO-FINRES/1.0 (mailto:contact@izilifepay.com)"})
            m=json.load(urllib.request.urlopen(req,timeout=40)); out[doi]=m
            yr=(m.get('issued') or {}).get('date-parts',[[None]])[0][0]
            au=(m.get('author') or [{}])[0].get('family','')
            t=m.get('title',''); t=t[0] if isinstance(t,list) else t
            ct=m.get('container-title',''); ct=ct[0] if isinstance(ct,list) and ct else ct
            print(f"OK  {doi} | {yr} | {au} | {t[:90]} | {str(ct)[:45]}",flush=True); break
        except Exception as e:
            if '404' in str(e): print('NOTFOUND',doi,flush=True); break
            time.sleep(5*(a+1))
    else: print('ERR',doi,flush=True)
    time.sleep(1.5)
json.dump(out,open('verified.json','w'))
