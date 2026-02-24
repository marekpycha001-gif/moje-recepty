import streamlit as st
import json, os, requests, re, time, random, string
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ---------- CONFIG ----------
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
    data = safe_load_json(LOCAL_FILE,[])
    for x in data:
        if "id" not in x:
            x["id"]=new_id()
        if "category" not in x:
            x["category"]=["slané"] if x.get("type","slané")=="slané" else ["sladké"]
    return data

def save_db():
    safe_save_json(LOCAL_FILE,st.session_state.recipes)
    safe_save_json(CACHE_FILE,conversion_cache)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- STYLE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

body,[data-testid="stAppViewContainer"]{
background:radial-gradient(circle at bottom,#000428,#004e92);
color:white;
}

.title{
font-family:'Dancing Script',cursive;
font-size:22px;
text-align:center;
color:#00ccff;
margin-bottom:10px;
}

.stExpanderHeader{
background:#1E3A8A !important;
color:white !important;
border-radius:10px;
margin-bottom:1px !important;
padding:4px !important;
}

.stExpanderContent{
background:#cce0ff !important;
color:black !important;
border-radius:10px !important;
padding:2px !important;
}

p{margin:0px !important; padding:0px !important; line-height:1.2 !important;}
.block-container{padding-top:1rem;}
.topbar{position:sticky;top:0;z-index:999;background:#000428;padding-bottom:6px;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
st.markdown('<div class="topbar">',unsafe_allow_html=True)
c1,c2,c3 = st.columns([1,1,2])
with c1:
    st.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
with c2:
    st.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
# c3 zůstává prázdné pro zarovnání
st.markdown("</div>",unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- CATEGORY FILTER ----------
all_cats = set()
for r in st.session_state.recipes:
    all_cats.update(r.get("category",[]))
all_cats = sorted(all_cats)
selected_cat = st.selectbox("Kategorie", ["Vše"] + all_cats)

# ---------- UNIT CONVERSION ----------
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

# ---------- SPLIT INGREDIENTS ----------
def split_ingredients(text):
    parts=re.split(r',| a ', text)
    return "\n".join(p.strip() for p in parts if p.strip())

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    st.markdown("### Nový recept")
    n=st.text_input("Název")
    por=st.number_input("Porce",1,20,4)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")
    cat_input = st.text_input("Kategorie (nové odděluj čárkou)")
    
    def save_new():
        cats = [c.strip() for c in cat_input.split(",") if c.strip()]
        if not cats:
            cats = ["sladké"] if st.session_state.show_new else ["slané"]
        ing_split=split_ingredients(ing)
        st.session_state.recipes.insert(0,{
            "id":new_id(),
            "name":n or "Bez názvu",
            "portions":por,
            "ingredients":convert_text(ing_split),
            "steps":steps,
            "category":cats,
            "fav":False
        })
        save_db()
        st.session_state.show_new=False
    
    st.button("Uložit",on_click=save_new)

# ---------- FILTER + SEARCH ----------
recipes_sorted=sorted(st.session_state.recipes,key=lambda x:(not x.get("fav",False),x["name"]))
recipes_filtered=[]
search_terms = search.lower().split()
for r in recipes_sorted:
    if selected_cat!="Vše" and selected_cat not in r.get("category",[]):
        continue
    # hledání podle části slov
    text=(r["name"]+" "+r["ingredients"]).lower()
    if search_terms and not all(any(term in w for w in text.split()) for term in search_terms):
        continue
    recipes_filtered.append(r)

# ---------- DISPLAY ----------
for r in recipes_filtered:
    title=("⭐ "+r["name"]) if r.get("fav") else r["name"]
    with st.expander(title):
        if st.session_state.edit_id==r["id"]:
            en=st.text_input("Název",r["name"])
            ep=st.number_input("Porce",1,20,r["portions"])
            ei=st.text_area("Ingredience",r["ingredients"])
            es=st.text_area("Postup",r["steps"])
            ec=st.text_input("Kategorie (odděl čárkou)"," ,".join(r.get("category",[])))

            def save_edit(r=r):
                cats = [c.strip() for c in ec.split(",") if c.strip()]
                ei_split=split_ingredients(ei)
                r.update({"name":en,"portions":ep,"ingredients":convert_text(ei_split),"steps":es,"category":cats})
                st.session_state.edit_id=None
                save_db()
            
            st.button("💾 Uložit změny",on_click=save_edit)
        else:
            st.markdown("**Kategorie:** "+", ".join(r.get("category",[])))
            st.markdown("**Ingredience**")
            for l in r["ingredients"].splitlines():
                st.markdown(f'<p style="margin:0px;padding:0px;">• {l}</p>',unsafe_allow_html=True)
            st.markdown("**Postup**")
            for l in r["steps"].splitlines():
                st.markdown(f'<p style="margin:0px;padding:0px;">{l}</p>',unsafe_allow_html=True)
            
            c1,c2,c3=st.columns(3)
            c1.button("⭐",key=r["id"]+"f",on_click=lambda r=r:[r.update({"fav":not r["fav"]}),save_db()])
            c2.button("✏️",key=r["id"]+"e",on_click=lambda r=r:st.session_state.update({"edit_id":r["id"]}))
            c3.button("🗑",key=r["id"]+"d",on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db()])
