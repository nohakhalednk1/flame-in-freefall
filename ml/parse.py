import csv,re
def num(s):
    m=re.search(r'-?\d+(\.\d+)?',s or ''); return float(m.group()) if m else None
def thickness_mm(m):
    s=m.lower()
    mm=re.search(r'(\d+)\s*micron',s)
    if mm: return int(mm.group(1))/1000
    mm=re.search(r'(\d*\.\d+|\d+)\s*mm',s)
    if mm: return float(mm.group(1))
    if '1/4' in s: return 6.35
    if '3/8"' in s: return 9.53
    if '1/2"' in s or '0.5"' in s: return 12.7
    if 'sibal' in s or 'fabric' in s: return 0.37
    if 'nomex' in s: return 0.4
    return None
def group(m):
    s=m.lower()
    if 'nomex' in s: return 'Nomex'
    if 'sibal' in s: return 'Fabric'
    if 'candle' in s or 'spher' in s: return None
    if 'rod' in s: return 'PMMA rod'
    t=thickness_mm(m)
    if t is not None and t>=1: return 'PMMA sheet'
    return 'PMMA film'
def load():
    rows=list(csv.reader(open('data/raw/PSI-25_Experimental_table_BASS-II.csv',encoding='utf-8-sig')))[1:]
    out=[]
    for r in rows:
        mat=r[5]; ico,fco=num(r[15]),num(r[16]); o2=num(r[11]); air=num(r[8])
        out.append(dict(mat=mat,g=group(mat),th=thickness_mm(mat),o2=o2,air=air,frames=num(r[10]),ico=ico,fco=fco,
                        ext='ext' in (r[7]+r[8]).lower(), co=(fco-ico) if ico is not None and fco is not None else None))
    return out
if __name__=='__main__':
    from collections import Counter
    d=load(); print(Counter(x['g'] for x in d)); 
    ok=[x for x in d if x['co'] is not None and x['th'] and x['o2'] and x['air'] is not None]
    print(len(d),len(ok)); print(Counter(x['g'] for x in ok))
    for x in d:
        if x['g']=='Other' or x['th'] is None: print('??',x['mat'])
