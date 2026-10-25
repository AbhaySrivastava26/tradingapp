from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, desc
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, date, timedelta
from pathlib import Path
import os, csv, io, html, shutil, calendar
from fastapi import Request 

BASE=Path(__file__).resolve().parent.parent
DATA=BASE/"data"; UPLOADS=BASE/"uploads"
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True)
engine=create_engine(f"sqlite:///{DATA/'trading_journal.db'}",connect_args={"check_same_thread":False})
Session=sessionmaker(bind=engine,expire_on_commit=False)
Base=declarative_base()
app=FastAPI(title="Personal Trading Journal")
app.mount("/uploads",StaticFiles(directory=str(UPLOADS)),name="uploads")

class Trade(Base):
 __tablename__="trades"
 id=Column(Integer,primary_key=True)
 trade_date=Column(String(10),default=lambda:date.today().isoformat(),index=True)
 symbol=Column(String(50),default="XAUUSD"); market_type=Column(String(50),default="Forex/CFD")
 direction=Column(String(10),default="Long"); status=Column(String(20),default="Closed")
 entry=Column(Float,default=0); exit=Column(Float,nullable=True); stop_loss=Column(Float,nullable=True); take_profit=Column(Float,nullable=True)
 quantity=Column(Float,default=1); costs=Column(Float,default=0)
 entry_time=Column(String(10),default=""); exit_time=Column(String(10),default="")
 strategy=Column(String(100),default=""); session=Column(String(40),default="")
 reasons=Column(Text,default=""); emotion=Column(String(60),default=""); plan_adherence=Column(String(30),default="")
 exit_reason=Column(Text,default=""); mistakes=Column(Text,default=""); notes=Column(Text,default=""); lessons=Column(Text,default="")
 before_image=Column(String(255),default=""); after_image=Column(String(255),default="")
 created_at=Column(DateTime,default=datetime.utcnow); updated_at=Column(DateTime,default=datetime.utcnow,onupdate=datetime.utcnow)
class Review(Base):
 __tablename__="reviews"
 id=Column(Integer,primary_key=True); review_date=Column(String(10),index=True); content=Column(Text); created_at=Column(DateTime,default=datetime.utcnow)
Base.metadata.create_all(engine)

def e(v): return html.escape(str(v or ""))
def money(v): return "—" if v is None else f"{v:,.2f}"
def pnl(t):
 if t.status!="Closed" or t.exit is None:return None
 return ((t.exit-t.entry) if t.direction=="Long" else (t.entry-t.exit))*t.quantity-(t.costs or 0)
def metrics(ts):
 vals=[pnl(t) for t in ts]; vals=[x for x in vals if x is not None]
 wins=[x for x in vals if x>0]; losses=[x for x in vals if x<0]; gp=sum(wins); gl=abs(sum(losses))
 return {"count":len(ts),"closed":len(vals),"wins":len(wins),"losses":len(losses),"net":sum(vals),"winrate":len(wins)/len(vals)*100 if vals else 0,"avgwin":sum(wins)/len(wins) if wins else 0,"avgloss":sum(losses)/len(losses) if losses else 0,"pf":gp/gl if gl else (float("inf") if gp else None),"expectancy":sum(vals)/len(vals) if vals else 0}
def get_trades(db,start=None,end=None):
 q=db.query(Trade)
 if start:q=q.filter(Trade.trade_date>=start)
 if end:q=q.filter(Trade.trade_date<=end)
 return q.order_by(desc(Trade.trade_date),desc(Trade.id)).all()
def layout(body,active="Dashboard"):
 nav=[("Dashboard","/"),("Calendar","/calendar"),("Trades","/trades"),("Add Trade","/trade/new"),("Daily Reviews","/reviews"),("Analytics","/analytics"),("Risk Calculator","/risk"),("Settings & Backup","/settings")]
 links="".join(f'<a class="nav {"active" if n==active else ""}" href="{u}">{n}</a>' for n,u in nav)
 return f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>My Trading Journal</title><style>
:root{{--bg:#0b0c11;--panel:#151720;--line:#2b2f3d;--txt:#edf0f7;--muted:#9ba2b5;--purple:#a78bfa;--green:#4ade80;--red:#fb7185}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--txt);font:14px/1.5 system-ui,Segoe UI,sans-serif}}a{{color:var(--purple);text-decoration:none}}.app{{display:grid;grid-template-columns:220px 1fr;min-height:100vh}}aside{{padding:22px 13px;background:#101117;border-right:1px solid var(--line)}}.brand{{font-size:18px;font-weight:800;margin:0 9px 3px}}.muted{{color:var(--muted)}}.sub{{font-size:12px;color:var(--muted);margin:0 9px 22px}}.nav{{display:block;padding:10px 12px;margin:4px 0;border-radius:8px;color:#c7cbd6}}.nav.active,.nav:hover{{background:#29233b;color:#eee5ff}}main{{padding:26px;max-width:1500px;width:100%;min-width:0}}h1{{font-size:27px;margin:0 0 5px}}h2{{font-size:18px;margin:0 0 12px}}.row{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}.between{{justify-content:space-between}}.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:20px 0}}.card{{background:var(--panel);border:1px solid var(--line);border-radius:13px;padding:16px;min-width:0}}.metric{{font-size:24px;font-weight:750;margin-top:6px}}.green,.positive{{color:var(--green)}}.red,.negative{{color:var(--red)}}.formgrid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}}.field{{margin-bottom:12px;min-width:0}}label{{display:block;color:#c9ccda;font-size:12px;margin-bottom:5px}}input,select,textarea{{width:100%;background:#0e1017;color:var(--txt);border:1px solid #363a4a;border-radius:8px;padding:10px;font:inherit}}textarea{{min-height:86px}}button,.btn{{display:inline-block;border:0;border-radius:8px;padding:10px 13px;background:#8b5cf6;color:white;cursor:pointer;font:inherit;font-weight:650}}.secondary{{background:#272b38;color:#edf0f7}}.danger{{background:#a2384b}}table{{border-collapse:collapse;width:100%;min-width:700px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{font-size:12px;color:var(--muted)}}.tablewrap{{overflow:auto}}.section{{margin:18px 0}}.notice{{padding:12px;border:1px solid #594a27;background:#2a2518;color:#f6d88b;border-radius:9px}}.thumb{{max-width:190px;max-height:140px;border-radius:8px}}.calendar{{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:5px}}.day{{display:block;background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:7px;min-height:60px;color:var(--txt)}}.day small{{display:block;color:var(--muted);font-size:11px}}.profit{{border-color:#276747}}.loss{{border-color:#7c3343}}.actions{{display:flex;gap:8px;flex-wrap:wrap}}@media(max-width:950px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.formgrid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:650px){{.app{{grid-template-columns:1fr}}aside{{border-right:0;border-bottom:1px solid var(--line);padding:10px}}.sub{{margin-bottom:8px}}.navs{{display:flex;overflow:auto;gap:4px}}.nav{{white-space:nowrap;padding:8px}}main{{padding:15px}}.formgrid{{grid-template-columns:1fr}}.metric{{font-size:20px}}.calendar{{gap:3px}}.day{{padding:4px;min-height:48px;font-size:12px}}}}</style></head><body><div class="app"><aside><div class="brand">◈ My Trading Journal</div><div class="sub">Private · Local-first</div><div class="navs">{links}</div><div class="sub" style="margin-top:20px">Saved on this computer</div></aside><main>{body}</main></div></body></html>"""

FIELDS=[("trade_date","Trading date","date"),("symbol","Symbol","text"),("market_type","Market type","text"),("direction","Direction","select:Long,Short"),("status","Status","select:Open,Closed,Partially closed"),("entry","Entry price","number"),("exit","Exit price","number"),("stop_loss","Stop loss","number"),("take_profit","Take profit","number"),("quantity","Quantity / lots","number"),("costs","Total costs","number"),("entry_time","Entry time","time"),("exit_time","Exit time","time"),("strategy","Strategy / setup","text"),("session","Trading session","select:Asia,London,New York,Other"),("reasons","Why did you enter?","textarea"),("emotion","Emotion","select:Calm,Confident,Hesitant,Fearful,Greedy,FOMO,Frustrated,Revenge trading,Other"),("plan_adherence","Followed plan?","select:Yes,Partially,No,No plan"),("exit_reason","Why did you exit?","textarea"),("mistakes","Mistakes / rule violations","textarea"),("notes","Chart explanation / notes","textarea"),("lessons","Lessons learned","textarea")]
def control(k,label,typ,value=""):
 v=e(value)
 if typ.startswith("select:"):
  opts=typ.split(":",1)[1].split(",")
  return f'<div class="field"><label>{e(label)}</label><select name="{k}">'+''.join(f'<option {"selected" if str(o)==str(value) else ""}>{e(o)}</option>' for o in opts)+'</select></div>'
 if typ=="textarea":return f'<div class="field"><label>{e(label)}</label><textarea name="{k}">{v}</textarea></div>'
 return f'<div class="field"><label>{e(label)}</label><input name="{k}" type="{typ}" value="{v}" {"step=any" if typ=="number" else ""}></div>'
def save_image(f):
 if not f or not f.filename:return ""
 ext=Path(f.filename).suffix.lower()
 if ext not in {".png",".jpg",".jpeg",".webp"}:raise HTTPException(400,"Use PNG, JPG, JPEG, or WEBP images.")
 data=f.file.read(10*1024*1024+1)
 if len(data)>10*1024*1024:raise HTTPException(400,"Image maximum is 10 MB.")
 name=datetime.utcnow().strftime("%Y%m%d%H%M%S%f")+"_"+os.urandom(3).hex()+ext
 (UPLOADS/name).write_bytes(data);return name

@app.get("/",response_class=HTMLResponse)
def dashboard(start:str="",end:str=""):
 with Session() as db:
  ts=get_trades(db,start or None,end or None);m=metrics(ts);pf="∞" if m["pf"]==float("inf") else money(m["pf"])
  rows="".join(f'<tr><td><a href="/trade/{t.id}">{e(t.trade_date)}</a></td><td>{e(t.symbol)}</td><td>{e(t.direction)}</td><td>{e(t.status)}</td><td>{money(t.entry)}</td><td>{money(t.exit)}</td><td>{money(pnl(t))}</td><td><a href="/trade/{t.id}">Open</a></td></tr>' for t in ts[:8])
  body=f'<div class="row between"><div><h1>Dashboard</h1><p class="muted">Your trading records, stored locally.</p></div><a class="btn" href="/trade/new">＋ Add trade</a></div><form class="row section" method="get"><div><label>From</label><input type="date" name="start" value="{e(start)}"></div><div><label>To</label><input type="date" name="end" value="{e(end)}"></div><button>Filter</button><a class="btn secondary" href="/">Reset</a></form><div class="grid"><div class="card"><div class="muted">Net realized P&L</div><div class="metric">{money(m["net"])}</div></div><div class="card"><div class="muted">Trades recorded</div><div class="metric">{m["count"]}</div></div><div class="card"><div class="muted">Win rate</div><div class="metric">{m["winrate"]:.1f}%</div><div class="muted">{m["wins"]} wins · {m["losses"]} losses</div></div><div class="card"><div class="muted">Profit factor</div><div class="metric">{pf}</div></div><div class="card"><div class="muted">Expectancy / trade</div><div class="metric">{money(m["expectancy"])}</div></div><div class="card"><div class="muted">Average winner</div><div class="metric green">{money(m["avgwin"])}</div></div><div class="card"><div class="muted">Average loser</div><div class="metric red">{money(m["avgloss"])}</div></div><div class="card"><div class="muted">Closed trades</div><div class="metric">{m["closed"]}</div></div></div><div class="notice">P&L is a generic estimate: (exit − entry) × quantity for Long, reversed for Short, minus costs. Instrument contract sizes may change the real result.</div><div class="card section"><div class="row between"><h2>Recent trades</h2><a href="/trades">View all →</a></div><div class="tablewrap"><table><thead><tr><th>Date</th><th>Symbol</th><th>Side</th><th>Status</th><th>Entry</th><th>Exit</th><th>Net P&L</th><th></th></tr></thead><tbody>{rows or "<tr><td colspan=8>No trades yet. Add your first trade.</td></tr>"}</tbody></table></div></div>'
  return layout(body,"Dashboard")

@app.get("/trade/new",response_class=HTMLResponse)
def new_trade():
 defaults={"trade_date":date.today().isoformat(),"symbol":"XAUUSD","market_type":"Forex/CFD","direction":"Long","status":"Closed","quantity":"1","costs":"0"}
 fields="".join(control(k,l,t,defaults.get(k,"")) for k,l,t in FIELDS)
 return layout(f'<h1>Add trade</h1><p class="muted">Record your trade, reasoning and outcome.</p><form method="post" action="/trade/save" enctype="multipart/form-data"><div class="formgrid">{fields}<div class="field"><label>Before-entry screenshot</label><input type="file" name="before_image" accept="image/*"></div><div class="field"><label>After-exit screenshot</label><input type="file" name="after_image" accept="image/*"></div></div><button>Save trade</button> <a class="btn secondary" href="/trades">Cancel</a></form>',"Add Trade")
@app.post("/trade/save")
async def save_trade(request:Request,before_image:UploadFile|None=File(default=None),after_image:UploadFile|None=File(default=None)):
 form=await request.form()
 with Session() as db:
  t=Trade()
  for k,l,typ in FIELDS:
   v=form.get(k)
   if k in ("entry","exit","stop_loss","take_profit","quantity","costs"):
    try:setattr(t,k,float(v)) if v not in (None,"") else setattr(t,k,None)
    except ValueError:raise HTTPException(400,f"Invalid number: {l}")
   elif v is not None:setattr(t,k,str(v))
  t.before_image=save_image(before_image);t.after_image=save_image(after_image)
  if not t.symbol.strip() or t.entry is None or t.entry<=0:raise HTTPException(400,"Symbol and positive entry price are required.")
  if t.quantity is None or t.quantity<=0 or (t.costs is not None and t.costs<0):raise HTTPException(400,"Quantity must be positive and costs cannot be negative.")
  db.add(t);db.commit();tid=t.id
 return RedirectResponse(f"/trade/{tid}",status_code=303)

@app.get("/trade/{tid}",response_class=HTMLResponse)
def view_trade(tid:int):
 with Session() as db:
  t=db.get(Trade,tid)
  if not t:raise HTTPException(404,"Trade not found")
  vals=[("Date",t.trade_date),("Symbol",t.symbol),("Market",t.market_type),("Direction",t.direction),("Status",t.status),("Entry",money(t.entry)),("Exit",money(t.exit)),("Stop loss",money(t.stop_loss)),("Take profit",money(t.take_profit)),("Quantity",money(t.quantity)),("Costs",money(t.costs)),("Net P&L",money(pnl(t))),("Entry time",t.entry_time),("Exit time",t.exit_time),("Strategy",t.strategy),("Session",t.session),("Reasons",t.reasons),("Emotion",t.emotion),("Plan adherence",t.plan_adherence),("Exit reason",t.exit_reason),("Mistakes",t.mistakes),("Notes",t.notes),("Lessons",t.lessons)]
  rows="".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k,v in vals)
  imgs="".join(f'<div><h3>{label}</h3><a href="/uploads/{e(n)}"><img class="thumb" src="/uploads/{e(n)}"></a></div>' for label,n in [("Before entry",t.before_image),("After exit",t.after_image)] if n)
  body=f'<div class="row between"><div><h1>{e(t.symbol)} · {e(t.direction)}</h1><p class="muted">{e(t.trade_date)} · Trade #{t.id}</p></div><div class="actions"><a class="btn" href="/trade/{t.id}/edit">Edit</a><form method="post" action="/trade/{t.id}/delete" onsubmit="return confirm(\'Delete this trade?\')"><button class="danger">Delete</button></form></div></div><div class="card tablewrap"><table>{rows}</table></div><div class="card section"><h2>Screenshots</h2><div class="row">{imgs or "No screenshots attached."}</div></div><a class="btn secondary" href="/trades">Back to trades</a>'
  return layout(body,"Trades")
@app.get("/trade/{tid}/edit",response_class=HTMLResponse)
def edit_trade(tid:int):
 with Session() as db:
  t=db.get(Trade,tid)
  if not t:raise HTTPException(404,"Trade not found")
  fields="".join(control(k,l,typ,getattr(t,k) or "") for k,l,typ in FIELDS)
  imgs="".join(f'<p>{label}: <a href="/uploads/{e(n)}">view current image</a></p>' for label,n in [("Before image",t.before_image),("After image",t.after_image)] if n)
  return layout(f'<h1>Edit trade #{tid}</h1><form method="post" action="/trade/{tid}/update" enctype="multipart/form-data"><div class="formgrid">{fields}<div class="field"><label>Replace before image</label><input type="file" name="before_image" accept="image/*"></div><div class="field"><label>Replace after image</label><input type="file" name="after_image" accept="image/*"></div></div>{imgs}<button>Save changes</button></form>',"Trades")
@app.post("/trade/{tid}/update")
async def update_trade(tid:int,request:Request,before_image:UploadFile|None=File(default=None),after_image:UploadFile|None=File(default=None)):
 form=await request.form()
 with Session() as db:
  t=db.get(Trade,tid)
  if not t:raise HTTPException(404,"Trade not found")
  for k,l,typ in FIELDS:
   v=form.get(k)
   if k in ("entry","exit","stop_loss","take_profit","quantity","costs"):
    try:setattr(t,k,float(v)) if v not in (None,"") else setattr(t,k,None)
    except ValueError:raise HTTPException(400,f"Invalid number: {l}")
   elif v is not None:setattr(t,k,str(v))
  if before_image and before_image.filename:t.before_image=save_image(before_image)
  if after_image and after_image.filename:t.after_image=save_image(after_image)
  t.updated_at=datetime.utcnow();db.commit()
 return RedirectResponse(f"/trade/{tid}",status_code=303)
@app.post("/trade/{tid}/delete")
def delete_trade(tid:int):
 with Session() as db:
  t=db.get(Trade,tid)
  if t:
   for name in (t.before_image,t.after_image):
    if name:
     try:(UPLOADS/name).unlink(missing_ok=True)
     except OSError:pass
   db.delete(t);db.commit()
 return RedirectResponse("/trades",status_code=303)

@app.get("/trades",response_class=HTMLResponse)
def trades(q:str="",start:str="",end:str="",symbol:str=""):
 with Session() as db:
  ts=get_trades(db,start or None,end or None)
  if q:
   ql=q.lower();ts=[t for t in ts if ql in " ".join(str(getattr(t,k) or "") for k,_,_ in FIELDS).lower()]
  if symbol:ts=[t for t in ts if t.symbol.lower()==symbol.lower()]
  opts='<option value="">All symbols</option>'+''.join(f'<option {"selected" if symbol==s else ""}>{e(s)}</option>' for s in sorted({t.symbol for t in get_trades(db)}))
  rows="".join(f'<tr><td><a href="/trade/{t.id}">{e(t.trade_date)}</a></td><td>{e(t.symbol)}</td><td>{e(t.direction)}</td><td>{e(t.status)}</td><td>{money(t.entry)}</td><td>{money(t.exit)}</td><td>{money(t.stop_loss)}</td><td>{money(pnl(t))}</td><td><a href="/trade/{t.id}/edit">Edit</a></td></tr>' for t in ts)
  body=f'<div class="row between"><div><h1>Trades</h1><p class="muted">Search your saved history.</p></div><a class="btn" href="/trade/new">＋ Add trade</a></div><form class="formgrid section" method="get"><div class="field"><label>Search</label><input name="q" value="{e(q)}" placeholder="symbol, reason, notes"></div><div class="field"><label>Symbol</label><select name="symbol">{opts}</select></div><div class="field"><label>From date</label><input type="date" name="start" value="{e(start)}"></div><div class="field"><label>To date</label><input type="date" name="end" value="{e(end)}"></div><div class="field"><label>&nbsp;</label><button>Search</button></div></form><div class="card tablewrap"><table><thead><tr><th>Date</th><th>Symbol</th><th>Side</th><th>Status</th><th>Entry</th><th>Exit</th><th>SL</th><th>Net P&L</th><th></th></tr></thead><tbody>{rows or "<tr><td colspan=9>No matching trades.</td></tr>"}</tbody></table></div>'
  return layout(body,"Trades")

@app.get("/calendar",response_class=HTMLResponse)
def calendar_page(date:str=""):
 try:d=datetime.strptime(date,"%Y-%m-%d").date() if date else datetime.now().date()
 except ValueError:d=datetime.now().date()
 with Session() as db:
  ts=get_trades(db,d.isoformat(),d.isoformat());m=metrics(ts)
  daily="".join(f'<div class="card"><div class="row between"><a href="/trade/{t.id}"><b>{e(t.symbol)} · {e(t.direction)}</b></a><span>{money(pnl(t))}</span></div><p class="muted">{e(t.entry_time)} → {e(t.exit_time)} · {e(t.strategy)}</p><p>{e(t.reasons)}</p><a href="/trade/{t.id}">Open trade →</a></div>' for t in ts)
  first=d.replace(day=1);days=calendar.monthrange(d.year,d.month)[1];last=first+timedelta(days=days-1); monthts=get_trades(db,first.isoformat(),last.isoformat());by={}
  for t in monthts:by.setdefault(t.trade_date,[]).append(pnl(t))
  cells="".join(f'<div class="day"><small>{x}</small></div>' for x in ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]) + ''.join('<div class="day" style="opacity:.2"></div>' for _ in range(first.weekday()))
  for n in range(1,days+1):
   ds=first.replace(day=n).isoformat();vals=[x for x in by.get(ds,[]) if x is not None];total=sum(vals) if vals else None;cls="profit" if total is not None and total>0 else "loss" if total is not None and total<0 else ""
   cells+=f'<a class="day {cls}" href="/calendar?date={ds}">{n}<small>{money(total) if total is not None else (str(len(by.get(ds,[])))+" trade(s)" if ds in by else "")}</small></a>'
  daily_html = daily if daily else '<div class="card muted">No trades saved for this date.</div>'
  body=f'<div class="row between"><div><h1>Trading Calendar</h1><p class="muted">Select any date to see your records.</p></div><a class="btn" href="/trade/new">＋ Add trade</a></div><form class="row section" method="get"><div><label>Selected date</label><input type="date" name="date" value="{d.isoformat()}"></div><button>Open date</button></form><div class="card section"><h2>{d.strftime("%B %Y")}</h2><div class="calendar">{cells}</div></div><div class="section"><h2>{d.strftime("%A, %d %B %Y")} · {len(ts)} trades · Net P&L {money(m["net"])}</h2>{daily_html}</div>'
  return layout(body,"Calendar")

@app.get("/analytics",response_class=HTMLResponse)
def analytics():
 with Session() as db:
  ts=get_trades(db);by={}
  for t in ts:
   if pnl(t) is not None:by.setdefault(t.strategy or "Unspecified",[]).append(t)
  rows=""
  for name,group in sorted(by.items()):
   m=metrics(group);rows+=f'<tr><td>{e(name)}</td><td>{m["closed"]}</td><td>{m["winrate"]:.1f}%</td><td>{money(m["net"])}</td><td>{money(m["expectancy"])}</td></tr>'
  closed=sorted([t for t in ts if pnl(t) is not None],key=lambda t:(t.trade_date,t.id));cum=0;vals=[]
  for t in closed:cum+=pnl(t);vals.append(cum)
  if vals:
   lo=min([0]+vals);hi=max([1]+vals);span=hi-lo or 1;coords=" ".join(f'{10+i*780/max(1,len(vals)-1):.1f},{180-(v-lo)/span*160:.1f}' for i,v in enumerate(vals))
   svg=f'<svg viewBox="0 0 800 210" style="width:100%;height:220px"><polyline points="{coords}" fill="none" stroke="#a78bfa" stroke-width="3"/></svg>'
  else:svg='<p class="muted">Add closed trades to create your equity curve.</p>'
  body=f'<h1>Analytics</h1><p class="muted">Based on saved trades; contract multipliers are not configured.</p><div class="card section"><h2>Cumulative realized P&L</h2>{svg}</div><div class="card section"><h2>Strategy performance</h2><div class="tablewrap"><table><thead><tr><th>Strategy</th><th>Closed trades</th><th>Win rate</th><th>Net P&L</th><th>Expectancy</th></tr></thead><tbody>{rows or "<tr><td colspan=5>No closed trades with strategy names.</td></tr>"}</tbody></table></div></div><div class="card"><h2>Metric definitions</h2><p>Win rate = profitable trades / closed trades. Expectancy = average net P&L per closed trade. Profit factor = positive P&L / absolute negative P&L. Breakeven trades are included in win-rate denominator.</p></div>'
  return layout(body,"Analytics")

@app.get("/reviews",response_class=HTMLResponse)
def reviews():
 with Session() as db:
  rs=db.query(Review).order_by(desc(Review.review_date),desc(Review.id)).all()
  cards="".join(f'<div class="card section"><div class="row between"><h2>{e(r.review_date)}</h2><span class="muted">{r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else ""}</span></div><pre style="white-space:pre-wrap;font:inherit">{e(r.content)}</pre><form method="post" action="/reviews/{r.id}/delete" onsubmit="return confirm(\'Delete review?\')"><button class="danger">Delete review</button></form></div>' for r in rs)
  cards_html = cards if cards else '<div class="card muted">No reviews yet.</div>'
  body=f'<h1>Daily Reviews</h1><p class="muted">Saved daily reviews are available here anytime.</p><form method="post" action="/reviews/analyze" class="card section"><div class="field"><label>Date to analyze</label><input type="date" name="review_date" value="{date.today().isoformat()}" required></div><p class="muted">Rule-based review; no external AI service is used.</p><button>Analyze and save day</button></form>{cards_html}'
  return layout(body,"Daily Reviews")
@app.post("/reviews/analyze")
def analyze_day(review_date:str=Form(...)):
 with Session() as db:
  ts=get_trades(db,review_date,review_date);m=metrics(ts)
  lines=[f"Daily review for {review_date}",f"Trades recorded: {m['count']}",f"Closed trades: {m['closed']}",f"Net realized P&L: {money(m['net'])}",f"Win rate: {m['winrate']:.1f}%",f"Expectancy: {money(m['expectancy'])}",""]
  if not ts:lines.append("No trades were recorded on this date.")
  else:
   dev=[t for t in ts if t.plan_adherence in ("Partially","No","No plan")]
   lines.append(f"Plan adherence concerns: {len(dev)} of {len(ts)} trades were marked partial, no, or no plan.")
   emos={}
   for t in ts:
    if t.emotion:emos[t.emotion]=emos.get(t.emotion,0)+1
   lines.append("Recorded emotions: "+(", ".join(f"{k}: {v}" for k,v in emos.items()) if emos else "Not recorded."))
   lines.extend(["","Reflection prompts:","- Did each trade match a documented setup?","- Were stop loss and target defined before entry?","- Were exits consistent with your plan?","- What one process improvement will you focus on next session?","", "This report summarizes recorded data; it does not predict future prices."])
  db.add(Review(review_date=review_date,content="\n".join(lines)));db.commit()
 return RedirectResponse("/reviews",status_code=303)
@app.post("/reviews/{rid}/delete")
def delete_review(rid:int):
 with Session() as db:
  r=db.get(Review,rid)
  if r:db.delete(r);db.commit()
 return RedirectResponse("/reviews",status_code=303)

@app.get("/risk",response_class=HTMLResponse)
def risk():
 body="""<h1>Risk Calculator</h1><p class="muted">Planning calculator only. Verify contract specifications with your broker.</p><div class="card"><div class="formgrid"><div class="field"><label>Account equity</label><input id="equity" type="number" value="1000"></div><div class="field"><label>Risk per trade (%)</label><input id="riskpct" type="number" value="1"></div><div class="field"><label>Entry price</label><input id="entry" type="number" value="2650"></div><div class="field"><label>Stop loss</label><input id="sl" type="number" value="2645"></div><div class="field"><label>Value per price unit per quantity</label><input id="mult" type="number" value="1"></div></div><button onclick="let r=+equity.value*(+riskpct.value)/100, d=Math.abs(+entry.value-(+sl.value))*(+mult.value);result.innerHTML=d>0&&r>0?'<h2>Illustrative quantity: '+(r/d).toFixed(4)+'</h2><p>Planned risk amount: '+r.toFixed(2)+'</p>':'Enter valid values and nonzero stop distance.'">Calculate</button><div id="result" class="section"></div></div>"""
 return layout(body,"Risk Calculator")
@app.get("/settings",response_class=HTMLResponse)
def settings():
 return layout('<h1>Settings & Backup</h1><div class="card section"><h2>Export trades</h2><a class="btn" href="/export.csv">Download CSV</a></div><div class="card section"><h2>Database backup</h2><a class="btn" href="/backup">Download database backup</a><p class="muted">The database backup does not include images. Copy the uploads folder separately.</p></div><div class="card section"><h2>Storage locations</h2><p><code>data/trading_journal.db</code> stores trades and reviews.</p><p><code>uploads/</code> stores screenshots.</p></div><div class="notice">No login is configured. Anyone with access to this computer and files may see your records. App is bound to localhost only.</div>',"Settings & Backup")
@app.get("/export.csv")
def export_csv():
 with Session() as db:
  ts=get_trades(db);buf=io.StringIO();w=csv.writer(buf);w.writerow(["id"]+[k for k,_,_ in FIELDS]+["net_pnl","before_image","after_image"])
  for t in ts:w.writerow([t.id]+[getattr(t,k) for k,_,_ in FIELDS]+[pnl(t),t.before_image,t.after_image])
 return StreamingResponse(io.BytesIO(buf.getvalue().encode("utf-8-sig")),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=trades.csv"})
@app.get("/backup")
def backup():
 path=DATA/"trading_journal.db"
 if not path.exists():raise HTTPException(404,"No database yet.")
 target=DATA/"trading_journal_backup.db";shutil.copy2(path,target)
 return FileResponse(target,filename="trading_journal_backup.db",media_type="application/octet-stream")
