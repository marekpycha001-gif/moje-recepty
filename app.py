import streamlit as st
import json, os, re, time, random, string
from fractions import Fraction

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

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
defaults = {
    "recipes": [],
    "show_new": False,
    "show_search": False,
    "edit_id": None,
    "unit_mode":"Původní"
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

LOCAL_FILE = "recipes.json"

# ---------- LOAD DB ----------
def load_db():
    data = safe_load_json(LOCAL_FILE,[])
    for x in data:
        if "id" not in x:
            x["id"]=new_id()
        if "category" not in x:
            x["category"]=["slané"]
    return data

def save_db():
    safe_save_json(LOCAL_FILE,st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- STYLE ----------
st.markdown("""
<style>
body,[data-testid="stAppViewContainer"]{
background:radial-gradient(circle at bottom,#000428,#004e92);
color:white;
}
.title{
font-size:24px;
text-align:center;
color:#00ccff;
margin-bottom:10px;
}
.block-container{padding-top:1rem;}
.topbar{position:sticky;top:0;z-index:999;background:#000428;padding-bottom:6px;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP ----------
st.markdown('<div class="topbar">',unsafe_allow_html=True)
c1,c2,c3 = st.columns([1,1,2])
c1.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
c2.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
st.markdown("</div>",unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- CATEGORY ----------
all_cats=set()
for r in st.session_state.recipes:
    all_cats.update(r.get("category", []))
all_cats=sorted(all_cats)
selected_cat=st.selectbox("Kategorie",["Vše"]+all_cats)

# ---------- UNIT MODE ----------
unit_mode = st.selectbox("Jednotky",["Původní","Gramy","Mililitry"])

# ---------- DATABASE HUSTOT ----------
density_db = {
    "voda":1,
    "water":1,

    "mléko":1.03,
    "milk":1.03,

    "olej":0.92,
    "oil":0.92,

    "med":1.42,
    "honey":1.42,

    "mouka":0.53,
    "flour":0.53,

    "cukr":0.85,
    "sugar":0.85,

    "sůl":1.2,
    "salt":1.2,

    "rýže":0.85,
    "rice":0.85
}

# ---------- UNITS ----------
unit_map={
    "ml":1,
    "l":1000,
    "g":1,
    "kg":1000,
    "lžíce":15,
    "lžička":5,
    "hrnek":240,
    "cup":240
}

# ---------- PARSE NUMBER ----------
def parse_qty(q):
    q=q.replace(",",".")
    try:
        return float(sum(Fraction(x) for x in q.split()))
    except:
        try:return float(q)
        except:return None

# ---------- FIND DENSITY ----------
def find_density(name):

    name=name.lower()

    for key,val in density_db.items():
        if key in name:
            return val

    return 1

# ---------- CONVERT ----------
def convert_line(line,scale):

    m=re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)",line.strip())
    if not m:
        return line

    qty,unit,name=m.groups()

    val=parse_qty(qty)
    if val is None:
        return line

    val*=scale

    if unit_mode=="Původní":
        return f"{round(val,2)} {unit or ''} {name}".strip()

    coef=unit_map.get((unit or "").lower())
    if not coef:
        return f"{round(val,2)} {unit or ''} {name}".strip()

    ml=val*coef

    if unit_mode=="Mililitry":
        return f"{round(ml)} ml {name}"

    dens=find_density(name)
    g=ml*dens

    return f"{round(g)} g {name}"

def convert_text(text,scale):
    return "\n".join(convert_line(l,scale) for l in text.splitlines() if l.strip())

# ---------- SPLIT ----------
def split_ingredients(text):
    text=text.replace(",",".")
    parts=re.split(r'(?<!\d),(?!\d)|\s+a\s+', text)
    return "\n".join(p.strip() for p in parts if p.strip())

# ---------- NEW ----------
if st.session_state.show_new:

    st.subheader("Nový recept")

    n=st.text_input("Název")
    por=st.number_input("Porce",1,20,4)
    ing=st.text_area("Ingredience")
    steps=st.text_area("Postup")

    cats=st.multiselect("Kategorie",all_cats)

    if st.button("Uložit"):
        st.session_state.recipes.insert(0,{
            "id":new_id(),
            "name":n or "Bez názvu",
            "portions":por,
            "ingredients":split_ingredients(ing),
            "steps":steps,
            "category":cats or ["slané"],
            "fav":False
        })
        save_db()
        st.session_state.show_new=False
        st.rerun()

# ---------- FILTER ----------
recipes_sorted=sorted(st.session_state.recipes,key=lambda x:(not x.get("fav",False),x["name"]))
recipes_filtered=[]

for r in recipes_sorted:
    if selected_cat!="Vše" and selected_cat not in r.get("category",[]):
        continue
    text=(r["name"]+" "+r["ingredients"]).lower()
    if search and search.lower() not in text:
        continue
    recipes_filtered.append(r)

# ---------- DISPLAY ----------
for r in recipes_filtered:

    title=("⭐ " if r.get("fav") else "")+r["name"]

    with st.expander(title):

        st.markdown(f"**{r['name']}**")

        new_portions=st.number_input(
            "Porce",
            1,50,r["portions"],
            key="p"+r["id"]
        )

        scale=new_portions/r["portions"]

        st.markdown("**Ingredience**")

        for l in convert_text(r["ingredients"],scale).splitlines():
            st.write("•",l)

        st.markdown("**Postup**")
        st.write(r["steps"])

        c1,c2=st.columns(2)
        c1.button("⭐",key=r["id"],on_click=lambda r=r:[r.update({"fav":not r["fav"]}),save_db()])
        c2.button("🗑",key=r["id"]+"d",on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db(),st.rerun()])
