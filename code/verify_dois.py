import json, urllib.request, urllib.parse, sys, time
dois=[l.strip() for l in open(sys.argv[1]) if l.strip() and not l.startswith('#')]
out={}
for doi in dois:
    u="https://api.crossref.org/works/"+urllib.parse.quote(doi)+"?mailto=research@example.org"
    try:
        m=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"AFRO-FINRES-research/1.0 (mailto:contact@izilifepay.com)"}),timeout=30))['message']
        au="; ".join(f"{a.get('family','')}, {a.get('given','')}" for a in m.get('author',[])[:8])
        yr=(m.get('issued') or {}).get('date-parts',[[None]])[0][0]
        out[doi]=m
        print(f"OK  {doi} | {yr} | {au[:80]} | {m.get('title',[''])[0][:90]} | {(m.get('container-title') or [''])[0][:50]}")
    except Exception as e:
        print(f"ERR {doi} {e}")
    time.sleep(1.5)
json.dump(out,open(sys.argv[1]+'.json','w'))
