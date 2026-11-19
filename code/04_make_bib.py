import json, re, unicodedata
V=json.load(open('refs/verified.json'))
def ascii(s): return unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
def tex(s): return s.replace('&amp;','\\&').replace('&','\\&').replace('%','\\%').replace('_','\\_')
out=[]; keys={}
for doi,m in V.items():
    au=m.get('author',[]); yr=(m.get('issued') or {}).get('date-parts',[[None]])[0][0]
    first=(ascii(au[0].get('family','') if au else (m.get('publisher','') or 'anon')).split() or ['anon'])[0]
    key=re.sub(r'[^A-Za-z]','',first)+str(yr); 
    while key in keys.values(): key+='b'
    keys[doi]=key
    t=m.get('title',''); t=t[0] if isinstance(t,list) else t
    ct=m.get('container-title',''); ct=ct[0] if isinstance(ct,list) and ct else (ct if isinstance(ct,str) else '')
    typ=m.get('type','')
    authors=' and '.join(f"{a.get('family','')}, {a.get('given','')}".strip(', ') if 'family' in a else '{'+a.get('literal','')+'}' for a in au) or '{'+tex(m.get('publisher',''))+'}'
    et='article' if typ in ('journal-article','article-journal') else ('incollection' if 'chapter' in typ else 'misc' if typ in ('posted-content','report','article') else 'book' if 'book' in typ or typ=='monograph' else 'misc')
    f={'author':authors,'title':'{'+tex(t)+'}','year':str(yr),'doi':doi}
    if et=='article': f['journal']=tex(ct); f.update({k:str(m[k]) for k in ['volume','page'] if k in m}); f.setdefault('number',str(m.get('issue',''))) 
    elif et=='incollection': f['booktitle']=tex(ct); f['publisher']=tex(m.get('publisher',''))
    else: f['publisher']=tex(m.get('publisher','')); 
    if ct and et=='misc': f['howpublished']=tex(ct)
    if 'page' in f: f['pages']=f.pop('page').replace('-','--')
    out.append('@'+et+'{'+key+',\n'+',\n'.join(f'  {k} = {{{v}}}' if not v.startswith('{') else f'  {k} = {v}' for k,v in f.items() if v)+'\n}')
open('manuscript/refs_verified.bib','w').write('\n\n'.join(out)+'\n')
for d,k in keys.items(): print(k,d)
