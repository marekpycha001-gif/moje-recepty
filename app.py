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
                recipes.append({
                    "name": x.get("name","Bez názvu"),
                    "type": x.get("type","slané"),
                    "portions": x.get("portions",4),
                    "ingredients": x.get("ingredients",""),
                    "steps": x.get("steps",""),
                    "fav": x.get("fav", False)
                })
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
.topbar{display:flex; justify-content:center; gap:4px; margin-bottom:10px; flex-wrap:wrap;}
.topbtn{background:#0099ff; color:white; border:none; padding:5px 10px; border-radius:8px; font-size:18px; cursor:pointer;}
.title{font-family:'Dancing Script',cursive; font-size:22px; text-align:center; color:#00ccff; margin-bottom:15px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px; margin-bottom:2px; padding:5px 6px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px; margin-bottom:2px; padding:4px 6px; line-height:1.2;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea{color:black; margin-bottom:2px;}
ul{padding-left:15px; margin:0;}
li{margin-bottom:2px; line-height:1.2;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
col1, col2, col3 = st.columns([1,1,2])
with col1: st.button("➕", on_click=lambda: st.session_state.update({"show_new": not st.session_state.show_new}))
with col2: st.button("🔍", on_click=lambda: st.session_state.update({"show_search": not st.session_state.show_search}))
with col3: st.button("☁️ Sync", on_click=save_db)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search = st.text_input("Hledat recept podle názvu/ingrediencí")

# ---------- UNIT CONVERSION ----------
unit_map = {"ml":1, "l":1000, "lžíce":15, "lžic":15, "lžička":5, "lžiček":5, "hrnek":120, "hrnků":120, "cup":120, "cups":120}
density_map = {"olej":0.92, "mléko":1.03, "voda":1.0, "med":1.42}
ingredient_map = {"medu":"med", "medík":"med", "cukru":"cukr", "cuker":"cukr","oleje":"olej", "mlíko":"mléko"}

def normalize_name(name):
    n = re.sub(r"[^\w\s]", "", name.lower().strip())
    return ingredient_map.get(n,n)

def convert_line(line):
    line = line.strip()
    pattern = r"([\d\s\/,.]+)\s*([^\d\s]+)?\s*(.+)"
    m = re.match(pattern, line)
    if not m:
        return line
    qty, unit, name = m.groups()
    name_clean = normalize_name(name)
    try:
        qty = sum(Fraction(x) for x in qty.replace(",", ".").split())
    except:
        qty = 0
    coef = conversion_cache.get(name_clean,1)
    if unit:
        coef = unit_map.get(unit.lower(), coef)
    coef *= density_map.get(name_clean,1)
    grams = round(float(qty)*coef)
    conversion_cache[name_clean] = coef
    return f"{grams} g {name.strip()}"

def convert_text(text):
    return "\n".join([convert_line(l) for l in text.splitlines() if l.strip()])

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    st.markdown("### Přidat nový recept")
    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    portions=st.number_input("Počet porcí",1,20,4)
    ingredients=st.text_area("Ingredience (každá na nový řádek)")
    steps=st.text_area("Postup")
    def save_new_recipe():
        conv_ing = convert_text(ingredients)
        conv_steps = convert_text(steps)
        st.session_state.recipes.insert(0,{
            "name": name or "Bez názvu",
            "type": typ,
            "portions": portions,
            "ingredients": conv_ing,
            "steps": conv_steps,
            "fav": False
        })
        save_db()
        st.session_state.show_new = False
    st.button("Čimilali", on_click=save_new_recipe)

# ---------- DISPLAY RECIPES ----------
for i,r in enumerate(st.session_state.recipes):
    if search and search.lower() not in (r["name"]+r["ingredients"]).lower():
        continue
    with st.expander("⭐ "+r["name"] if r.get("fav") else r["name"]):
        st.markdown("### Ingredience")
        st.markdown("<ul style='margin:0;padding-left:15px;'>"+ "".join([f"<li>{line}</li>" for line in r["ingredients"].splitlines()])+"</ul>", unsafe_allow_html=True)
        st.markdown("### Postup")
        st.markdown("<ul style='margin:0;padding-left:15px;'>"+ "".join([f"<li>{line}</li>" for line in r["steps"].splitlines()])+"</ul>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns([1,1,1])
        c1.button("⭐", key=f"fav{i}", on_click=lambda i=i: [st.session_state.recipes[i].update({"fav": not st.session_state.recipes[i]["fav"]}), save_db()])
        c2.button("🗑", key=f"del{i}", on_click=lambda i=i: [st.session_state.recipes.pop(i), save_db()])
        c3.button("✏️", key=f"edit{i}", on_click=lambda i=i: st.session_state.update({"edit_index": i}))

# ---------- EDIT ----------
if st.session_state.edit_index is not None:
    r = st.session_state.recipes[st.session_state.edit_index]
    st.markdown(f"### Editace receptu: {r['name']}")
    edit_name = st.text_input("Název", r["name"])
    edit_type = st.radio("Typ", ["sladké","slané"], index=0 if r["type"]=="sladké" else 1)
    edit_portions = st.number_input("Počet porcí",1,20,r["portions"])
    edit_ingredients = st.text_area("Ingredience", r["ingredients"])
    edit_steps = st.text_area("Postup", r["steps"])
    def save_edit():
        r.update({
            "name": edit_name,
            "type": edit_type,
            "portions": edit_portions,
            "ingredients": convert_text(edit_ingredients),
            "steps": convert_text(edit_steps)
        })
        save_db()
        st.session_state.edit_index = None
    st.button("💾 Uložit změny", on_click=save_edit)
