import streamlit as st
import json, os, requests, re, time, random, string
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ---------- CONFIG ----------
SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"
CACHE_FILE = "conversion_cache.json"

# ---------- HELPERS ----------
def new_id():
    return "r_" + str(int(time.time())) + "_" + "".join(random.choices(string.ascii_lowercase+string.digits,k=4))

def safe_load_json(path, default):
    try:
        if os.path.exists(path):
            return json.load(open(path, encoding="utf8"))
    except:
        pass
    return default

def safe_save_json(path,data):
    with open(path,"w",encoding="utf8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

# ---------- SESSION ----------
defaults = {"recipes": [], "show_new": False, "show_search": False, "edit_id": None}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- CACHE ----------
conversion_cache = safe_load_json(CACHE_FILE,{})

# ---------- LOAD DB ----------
def load_db():
    try:
        r=requests.get(SDB_URL,timeout=3)
        data=r.json() if r.status_code==200 else []
    except:
        data=[]

    if not data:
        data=safe_load_json(LOCAL_FILE,[])

    for x in data:
        if "id" not in x:
            x["id"]=new_id()
    return data

def save_db():
    safe_save_json(LOCAL_FILE,st.session_state.recipes)
    safe_save_json(CACHE_FILE,conversion_cache)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- STYLE ----------
st.markdown("""
<style>

header{visibility:hidden;}

body,[data-testid="stAppViewContainer"]{
background:radial-gradient(circle at bottom,#000428,#004e92);
color:white;
}

.title{
font-size:24px;
text-align:center;
color:#00ccff;
margin-bottom:10px;
font-weight:700;
}

.topbar{
position:sticky;
top:0;
z-index:999;
background:#000428;
padding-bottom:6px;
border:none!important;
}

button{
border-radius:10px!important;
transition:.15s;
}
button:hover{transform:scale(1.05)}

.ingredients p{
margin:0;
line-height:1.05;
font-size:15px;
}

[data-testid="stExpander"]{
border:none!important;
box-shadow:none!important;
}

</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
st.markdown('<div class="topbar">',unsafe_allow_html=True)
c1,c2,c3=st.columns([1,1,2])
with c1:
    st.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
with c2:
    st.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
with c3:
    st.button("💾 Uložit",on_click=save_db)
st.markdown("</div>",unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat").lower()

# ---------- CONVERSION ----------
unit_map={"ml":1,"l":1000,"g":1,"kg":1000,"lžíce":15,"lžička":5,"hrnek":240,"cup":240}
density={"voda":1,"mléko":1.03,"olej":0.92,"med":1.42}
ignore_units=["ks","kus","vejce","špetka","trochu"]

def parse_qty(q):
    try:return float(sum(Fraction(x) for x in q.replace(",",".").split()))
    except:
        try:return float(q)
        except:return None

def convert_line(line):
    line=line.strip()
    m=re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)",line)
    if not m:return line
    qty,unit,name=m.groups()
    val=parse_qty(qty)
    if val is None:return line
    if unit and unit.lower() in ignore_units:return line
    coef=unit_map.get((unit or "").lower(),1)
    coef*=density.get(name.lower().strip(),1)
    if coef==1:return line
    return f"{round(val*coef)} g {name.strip()}"

def convert_text(t):
    return "\n".join(convert_line(l) for l in t.splitlines() if l.strip())

# ---------- NEW ----------
if st.session_state.show_new:
    st.markdown("### Nový recept")
    n=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    por=st.number_input("Porce",1,20,4)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    def save_new():
        st.session_state.recipes.insert(0,{
            "id":new_id(),
            "name":n or "Bez názvu",
            "type":typ,
            "portions":por,
            "ingredients":convert_text(ing),
            "steps":steps,
            "fav":False
        })
        save_db()
        st.session_state.show_new=False
        st.rerun()

    st.button("Uložit recept",on_click=save_new)

# ---------- SORT ----------
recipes_sorted=sorted(st.session_state.recipes,key=lambda x:(not x.get("fav",False),x["name"]))

# ---------- DISPLAY ----------
for r in recipes_sorted:

    text=(r["name"]+r["ingredients"]+r["type"]).lower()
    if search and search not in text:
        continue

    title=("⭐ "+r["name"]) if r.get("fav") else r["name"]

    with st.expander(title):

        if st.session_state.edit_id==r["id"]:
            en=st.text_input("Název",r["name"])
            et=st.radio("Typ",["sladké","slané"],index=0 if r["type"]=="sladké" else 1)
            ep=st.number_input("Porce",1,20,r["portions"])
            ei=st.text_area("Ingredience",r["ingredients"])
            es=st.text_area("Postup",r["steps"])

            def save_edit(r=r):
                r.update({"name":en,"type":et,"portions":ep,"ingredients":convert_text(ei),"steps":es})
                st.session_state.edit_id=None
                save_db()
                st.rerun()

            st.button("💾 uložit změny",on_click=save_edit)

        else:
            st.markdown("**Ingredience**")
            html="<div class='ingredients'>"
            for l in r["ingredients"].splitlines():
                html+=f"<p>• {l}</p>"
            html+="</div>"
            st.markdown(html,unsafe_allow_html=True)

            st.markdown("**Postup**")
            for l in r["steps"].splitlines():
                st.markdown(l)

            c1,c2,c3=st.columns(3)
            c1.button("⭐",key=r["id"]+"f",on_click=lambda r=r:[r.update({"fav":not r["fav"]}),save_db(),st.rerun()])
            c2.button("✏️",key=r["id"]+"e",on_click=lambda r=r:st.session_state.update({"edit_id":r["id"]}))
            c3.button("🗑",key=r["id"]+"d",on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db(),st.rerun()])
