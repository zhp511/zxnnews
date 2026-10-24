#!/usr/bin/env python3
"""ZXN Election Day HQ results feed -> data/election/results.json (the /election/ page polls it every 60s).

There is no free, licensed national real-time results API (AP/Decision Desk are paid). So results are entered
from official sources (state Secretary of State results sites, e.g. results.enr.clarityelections.com, or
network race calls) using this CLI, then pushed. NEVER enter a result you have not seen from a real source.

  python3 election_results.py call senate Georgia "Full Name" --party Democratic --pct 97 --source URL
  python3 election_results.py update governor Ohio --pct 40 --votes "Name A=1200,Name B=1100" --source URL
  python3 election_results.py call house "Texas 15" "Full Name" --party Republican --source URL
  python3 election_results.py import results.csv   # columns: chamber,race,winner,party,pct_reporting,source
  python3 election_results.py clear                # reset to awaiting results
  add --push to git commit + push immediately (else the 5-min refresh routine pushes it).
"""
import json, sys, os, csv, argparse, datetime, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); F=os.path.join(HERE,"data","election","results.json")
def load():
    try: return json.load(open(F))
    except Exception: return {"updated":None,"note":"No results yet. Polls close Nov 3, 2026.","races":{}}
def save(d,push=False):
    d["updated"]=datetime.datetime.now(datetime.timezone.utc).isoformat(); json.dump(d,open(F,"w"),indent=1,ensure_ascii=False)
    print("wrote",F,len(d["races"]),"races")
    if push:
        subprocess.run(["git","-C",HERE,"add",F]); subprocess.run(["git","-C",HERE,"commit","-m","Election results update"])
        subprocess.run(["git","-C",HERE,"push"])
def key(ch,race): return f"{ch}:{race}"
def main():
    a=argparse.ArgumentParser(); a.add_argument("cmd"); a.add_argument("args",nargs="*")
    a.add_argument("--party",default=""); a.add_argument("--pct",type=float); a.add_argument("--votes",default="")
    a.add_argument("--source",default=""); a.add_argument("--push",action="store_true"); o=a.parse_args(); d=load()
    if o.cmd=="clear": d["races"]={}; return save(d,o.push)
    if o.cmd=="import":
        for r in csv.DictReader(open(o.args[0])):
            e=d["races"].setdefault(key(r["chamber"],r["race"]),{})
            if r.get("winner"): e.update(winner=r["winner"],party=r.get("party",""),called=True)
            if r.get("pct_reporting"): e["pct_reporting"]=float(r["pct_reporting"])
            if r.get("source"): e["source"]=r["source"]
        return save(d,o.push)
    ch,race=o.args[0],o.args[1]; e=d["races"].setdefault(key(ch,race),{})
    if o.cmd=="call": e.update(winner=o.args[2],party=o.party,called=True)
    if o.pct is not None: e["pct_reporting"]=o.pct
    if o.votes: e["votes"]={k.strip():int(v) for k,v in (p.split("=") for p in o.votes.split(","))}
    if o.source: e["source"]=o.source
    save(d,o.push)
if __name__=="__main__": main()
