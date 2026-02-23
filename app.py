import streamlit as st
import json, os, requests, re
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ---------- CONFIG ----------
SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"
CACHE_FILE = "conversion_cache.json"

# ---------- SESSION ----------
defaults = {"recipes": [], "show_new": False, "show_search": False, "edit_index": None}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- LOAD/SAVE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE,encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE,encoding="utf8"))
    return {}

def save_cache(c):
    with open(CACHE_FILE,"w",encoding="utf8") as f:
        json.dump(c,f,ensure_ascii=False,indent=2)

conversion_cache = load_cache()

def load_db():
    recipes=[]
    try:
        r=requests.get(SDB_URL,timeout=3)
        if r.status_code==200:
            recipes=r.json()
    except: pass
    if not recipes:
        recipes=load_local()
    for r in recipes:
        r.setdefault("name","Bez názvu")
        r.setdefault("type","slané")
        r.setdefault("portions",4)
        r.setdefault("ingredients","")
        r.setdefault("steps","")
        r.setdefault("fav",False)
    return recipes

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=3)
        requests.post(SDB_URL,json=st.session_state.recipes,timeout=3)
    except:
        st.warning("⚠️ Nepodařilo se připojit k SheetDB")
    save_local(st.session_state.recipes)
    save_cache(conversion_cache)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.topbtn{background:#0099ff;color:white;border:none;padding:6px 12px;border-radius:10px;font-size:18px;}
.title{font-family:'Dancing Script';font-size:24px;text-align:center;color:#00ccff;margin-bottom:15px;}
.stExpanderHeader{background:#1E3A8A!important;color:white!important;border-radius:12px;}
.stExpanderContent{background:#cce0ff!important;color:black!important;border-radius:12px;}
</style>
""",unsafe_allow_html=True)

# ---------- HEADER ----------
c1,c2,c3=st.columns([1,1,2])
c1.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
c2.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
c3.button("☁️ Sync",on_click=save_db)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- CONVERSION ----------
unit_map={
    "ml":1,"l":1000,
    "lžíce":15,"lžic":15,"lž":15,
    "lžička":5,"lžiček":5,
    "hrnek":120,"hrnků":120
}

density_map={
    "olej":0.92,
    "mléko":1.03,
    "voda":1,
    "med":1.42
}

def convert_line(line):
    if " g " in line:
        return line
    m=re.match(r"([\d\/\., ]+)\s*([^\d ]+)?\s*(.+)",line.strip())
    if not m:
        return line
    qty,unit,name=m.groups()
    try:
        qty=float(sum(Fraction(x) for x in qty.replace(",",".").split()))
    except:
        return line
    unit=unit.lower() if unit else ""
    name_clean=re.sub(r"[^\w]","",name.lower())

    coef=unit_map.get(unit)
    if coef:
        coef*=density_map.get(name_clean,1)
    else:
        coef=conversion_cache.get(name_clean)

    if not coef:
        return line

    grams=round(qty*coef)
    conversion_cache[name_clean]=coef
    return f"{grams} g {name}"

def convert_text(text):
    return "\n".join(convert_line(l) for l in text.splitlines())

# ---------- NEW ----------
if st.session_state.show_new:
    st.subheader("Nový recept")
    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    portions=st.number_input("Porce",1,20,4)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    def save_new():
        st.session_state.recipes.insert(0,{
            "name":name or "Bez názvu",
            "type":typ,
            "portions":portions,
            "ingredients":convert_text(ing),
            "steps":convert_text(steps),
            "fav":False
        })
        save_db()
        st.session_state.show_new=False

    st.button("Uložit",on_click=save_new)

# ---------- LIST ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in (r["name"]+r["ingredients"]).lower():
        continue

    with st.expander(("⭐ " if r["fav"] else "")+r["name"]):

        st.markdown("**Ingredience**")
        st.markdown(
            "<div style='line-height:1.1'>"+
            "".join(f"• {l}<br>" for l in r["ingredients"].splitlines())+
            "</div>",unsafe_allow_html=True)

        st.markdown("**Postup**")
        st.markdown(
            "<div style='line-height:1.15'>"+
            "<br>".join(r["steps"].splitlines())+
            "</div>",unsafe_allow_html=True)

        c1,c2,c3=st.columns(3)

        c1.button("⭐",key=f"f{i}",on_click=lambda i=i:[
            st.session_state.recipes[i].update({"fav":not st.session_state.recipes[i]["fav"]}),
            save_db()
        ])

        c2.button("🗑",key=f"d{i}",on_click=lambda i=i:[
            st.session_state.recipes.pop(i),
            save_db()
        ])

        c3.button("✏️",key=f"e{i}",on_click=lambda i=i:st.session_state.update({"edit_index":i}))

# ---------- EDIT ----------
if st.session_state.edit_index is not None:
    r=st.session_state.recipes[st.session_state.edit_index]
    st.subheader("Editace")

    n=st.text_input("Název",r["name"])
    t=st.radio("Typ",["sladké","slané"],index=0 if r["type"]=="sladké" else 1)
    p=st.number_input("Porce",1,20,r["portions"])
    ing=st.text_area("Ingredience",r["ingredients"])
    steps=st.text_area("Postup",r["steps"])

    def save_edit():
        r.update({
            "name":n,
            "type":t,
            "portions":p,
            "ingredients":convert_text(ing),
            "steps":convert_text(steps)
        })
        save_db()
        st.session_state.edit_index=None

    st.button("💾 Uložit změny",on_click=save_edit)
