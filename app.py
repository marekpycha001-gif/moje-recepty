import streamlit as st
import json, os, requests, re
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"
CACHE_FILE = "conversion_cache.json"

# ---------- SESSION ----------
defaults = {"recipes": [], "show_new": False, "show_search": False, "edit_index": None}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- LOAD/SAVE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def load_cache():
    if os.path.exists(CACHE_FILE):
        return json.load(open(CACHE_FILE, encoding="utf8"))
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

conversion_cache = load_cache()

def load_db():
    recipes = []
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            for x in r.json():
                recipes.append(x)
    except:
        pass
    if not recipes:
        recipes = load_local()

    for r in recipes:
        r.setdefault("name","Bez názvu")
        r.setdefault("type","slané")
        r.setdefault("portions",4)
        r.setdefault("ingredients","")
        r.setdefault("steps","")
        r.setdefault("fav", False)
    return recipes

def save_db():
    try:
        requests.delete(SDB_URL+"/all", timeout=3)
        requests.post(SDB_URL, json=st.session_state.recipes, timeout=3)
    except:
        st.warning("⚠️ Nepodařilo se připojit k Google Sheet.")
    save_local(st.session_state.recipes)
    save_cache(conversion_cache)

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.title{font-family:'Dancing Script',cursive; font-size:24px; text-align:center; color:#00ccff; margin-bottom:15px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px;}
.stTextInput input, textarea{color:black;}
.smallgap p{margin-bottom:0px; line-height:1.1;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP ----------
col1, col2, col3 = st.columns([1,1,2])
col1.button("➕", on_click=lambda: st.session_state.update({"show_new": not st.session_state.show_new}))
col2.button("🔍", on_click=lambda: st.session_state.update({"show_search": not st.session_state.show_search}))
col3.button("☁️ Sync", on_click=save_db)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search = st.text_input("Hledat recept")

# ---------- CONVERSION ----------
unit_map = {
    "ml":1,
    "l":1000,
    "lžíce":15,
    "lžic":15,
    "lžíci":15,
    "lžička":5,
    "lžičky":5,
    "hrnek":120,
    "hrnky":120,
    "hrnků":120
}

density_map = {
    "olej":0.92,
    "mléko":1.03,
    "voda":1.0,
    "med":1.42
}

def convert_line(line):
    line=line.strip()
    m=re.match(r"([\d\/., ]+)\s*([^\d\s]+)?\s*(.*)",line)
    if not m:
        return line

    qty,unit,name=m.groups()
    name_clean=name.lower().strip()

    try:
        qty=float(sum(Fraction(x) for x in qty.replace(",",".").split()))
    except:
        return line

    coef=None

    if unit:
        unit=unit.lower()
        if unit in unit_map:
            coef=unit_map[unit]

    if coef and any(k in name_clean for k in density_map):
        for k in density_map:
            if k in name_clean:
                coef*=density_map[k]

    if coef:
        grams=round(qty*coef)
        conversion_cache[name_clean]=coef
        return f"{grams} g {name}"

    return line

def convert_text(text):
    return "\n".join(convert_line(l) for l in text.splitlines() if l.strip())

# ---------- NEW ----------
if st.session_state.show_new:
    st.markdown("### Přidat nový recept")
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
            "steps":steps,
            "fav":False
        })
        save_db()
        st.session_state.show_new=False

    st.button("Uložit",on_click=save_new)

# ---------- DISPLAY ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in (r["name"]+r["ingredients"]).lower():
        continue

    with st.expander(("⭐ " if r["fav"] else "")+r["name"]):

        st.markdown("**Ingredience**")
        st.markdown('<div class="smallgap">',unsafe_allow_html=True)
        for l in r["ingredients"].splitlines():
            st.write("•",l)
        st.markdown("</div>",unsafe_allow_html=True)

        st.markdown("**Postup**")
        for l in r["steps"].splitlines():
            st.write(l)

        c1,c2,c3=st.columns(3)

        c1.button("⭐",key=f"f{i}",on_click=lambda i=i:[st.session_state.recipes[i].update({"fav":not st.session_state.recipes[i]["fav"]}),save_db()])
        c2.button("🗑",key=f"d{i}",on_click=lambda i=i:[st.session_state.recipes.pop(i),save_db()])
        c3.button("✏️",key=f"e{i}",on_click=lambda i=i:st.session_state.update({"edit_index":i}))

# ---------- EDIT ----------
if st.session_state.edit_index is not None:
    r=st.session_state.recipes[st.session_state.edit_index]

    st.markdown(f"### Editace: {r['name']}")
    name=st.text_input("Název",r["name"])
    typ=st.radio("Typ",["sladké","slané"],index=0 if r["type"]=="sladké" else 1)
    portions=st.number_input("Porce",1,20,r["portions"])
    ing=st.text_area("Ingredience",r["ingredients"])
    steps=st.text_area("Postup",r["steps"])

    def save_edit():
        r.update({
            "name":name,
            "type":typ,
            "portions":portions,
            "ingredients":ing,
            "steps":steps
        })
        save_db()
        st.session_state.edit_index=None

    st.button("💾 Uložit změny",on_click=save_edit)
