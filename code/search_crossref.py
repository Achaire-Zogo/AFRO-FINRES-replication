import json, urllib.request, urllib.parse, sys, time
H={"User-Agent":"AFRO-FINRES-research/1.0 (mailto:contact@izilifepay.com)"}
for q in sys.argv[1:]:
    u="https://api.crossref.org/works?rows=8&select=DOI,title,author,issued,container-title,type,is-referenced-by-count&query.bibliographic="+urllib.parse.quote(q)
    try: items=json.load(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=40))['message']['items']
    except Exception as e: print('ERR',q,e); continue
    print('\n### ',q)
    for m in items:
        yr=(m.get('issued') or {}).get('date-parts',[[None]])[0][0]
        au=(m.get('author') or [{}])[0].get('family','')
        print(f"  {m['DOI']} | {yr} | {au} | {m.get('title',[''])[0][:95]} | {(m.get('container-title') or [''])[0][:40]} | cit={m.get('is-referenced-by-count')}")
    time.sleep(2)
