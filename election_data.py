#!/usr/bin/env python3
"""Build data/election/{senate,governor,house}.json from Wikipedia (CC BY-SA) 2026 election pages.
Names are taken verbatim from the candidate lists; anything missing is 'TBD'. Run: python3 election_data.py"""
import json, re, urllib.request, datetime, os
from bs4 import BeautifulSoup
UA={"User-Agent":"ZXN-ElectionHQ/1.0 (zhp511.github.io/zxnnews)"}
PAGES={"senate":"2026_United_States_Senate_elections","governor":"2026_United_States_gubernatorial_elections",
       "house":"2026_United_States_House_of_Representatives_elections"}
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","election")
def get(p):
    return BeautifulSoup(urllib.request.urlopen(urllib.request.Request("https://en.wikipedia.org/api/rest_v1/page/html/"+p,headers=UA),timeout=60).read(),"html.parser")
def txt(el):
    for s in el.find_all(["sup","style"]): s.decompose()
    return re.sub(r"\s+"," ",el.get_text(" ",strip=True)).strip()
def cands(cell):
    out=[]
    for li in cell.find_all("li"):
        t=txt(li).lstrip("▌ ").strip()
        m=re.match(r"^(.*?)\s*\(([^)]*)\)",t)
        if m: out.append({"name":m.group(1).strip(),"party":m.group(2).strip()})
        elif t: out.append({"name":t,"party":""})
    return out
def rows(t):
    return [r.find_all(["th","td"]) for r in t.find_all("tr")]
def is_cand_table(t,first):
    h=txt(t.find("tr"))
    return h.startswith(first) and "Candidates" in h
def build(kind,soup):
    src="https://en.wikipedia.org/wiki/"+PAGES[kind]; races=[]
    tables=[t for t in soup.find_all("table",class_="wikitable")]
    if kind=="senate":
        for t in tables:
            if not is_cand_table(t,"Constituency"): continue
            for c in rows(t)[2:]:
                if len(c)<6: continue
                st=txt(c[0]); special="Class" in st
                races.append({"state":re.sub(r"\s*\(.*","",st),"label":st,"incumbent":txt(c[2]),"incumbent_party":txt(c[3]),
                              "status":txt(c[-2]),"candidates":cands(c[-1]),"special":special})
    elif kind=="governor":
        for t in tables:
            if not is_cand_table(t,"State"): continue
            for c in rows(t)[1:]:
                if len(c)<6: continue
                races.append({"state":txt(c[0]),"label":txt(c[0]),"incumbent":txt(c[1]),"incumbent_party":txt(c[2]),
                              "status":txt(c[-2]),"candidates":cands(c[-1])})
    else:
        for t in tables:
            if not is_cand_table(t,"District"): continue
            for c in rows(t)[2:]:
                if len(c)<5: continue
                d=txt(c[0]); m=re.match(r"^(.*?)\s+(\d+|at-large|At-large)$",d,re.I)
                if not m: continue
                inc=txt(c[2]); np_=len(c)<7
                races.append({"state":m.group(1),"district":m.group(2).lower() if not m.group(2).isdigit() else int(m.group(2)),
                              "label":d,"incumbent":inc,"incumbent_party":"" if np_ else txt(c[3]),
                              "status":txt(c[-2]),"candidates":cands(c[-1])})
    for r in races:
        if not r["candidates"]: r["candidates"]=[{"name":"TBD","party":""}]
    return {"source":src,"license":"CC BY-SA 4.0 (Wikipedia)","fetched":datetime.datetime.now(datetime.timezone.utc).isoformat(),"races":races}
def polls(soup):
    out={}
    for t in soup.find_all("table",class_="wikitable"):
        if "Poll closing" in txt(t.find("tr")):
            for c in rows(t)[1:]:
                vals=[txt(x) for x in c]
                pm=[v for v in vals if re.search(r"\b(am|pm)\b",v)]
                if pm: out[vals[0]]=pm[-1]+" ET"
    return out
if __name__=="__main__":
    os.makedirs(OUT,exist_ok=True); sen=None
    for k,p in PAGES.items():
        s=get(p)
        if k=="senate": pc=polls(s)
        d=build(k,s); json.dump(d,open(f"{OUT}/{k}.json","w"),indent=1,ensure_ascii=False)
        tbd=sum(1 for r in d["races"] if r["candidates"][0]["name"]=="TBD")
        print(k,len(d["races"]),"races,",tbd,"TBD")
    json.dump({"source":"https://en.wikipedia.org/wiki/"+PAGES["senate"],"poll_close_eastern":pc},open(f"{OUT}/polls.json","w"),indent=1)
    print("poll times",len(pc))
