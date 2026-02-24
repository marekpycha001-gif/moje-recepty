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
defaults = {"recipes": [], "show_new": False, "show_search": False, "edit_id": None}
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
        if "color" not in x:
            x["color"]="#1E3A8A"
    return data

def save_db():
    safe_save_json(LOCAL_FILE,st.session_state.recipes)

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
font-size:24px;
text-align:center;
color:#00ccff;
margin-bottom:10px;
}

.topbar{
position:sticky;
top:0;
z-index:999;
background:#000428;
padding:4px;
display:flex;
gap:4px;
flex-wrap:wrap;
}

.topbar button{
height:36px;
font-size:18px;
flex:1 1 auto;
min-width:40px;
}

.stExpanderHeader{
background:#1E3A8A !important;
color:white !important;
border-radius:10px;
margin-bottom:2px !important;
padding:4px !important;
}

.stExpanderContent{
background:#cce0ff !important;
color:black !important;
border-radius:10px !important;
padding:4px !important;
}

p{margin:0px !important; padding:0px !important; line-height:1.2 !important;}
.block-container{padding-top:0.5rem;}
</style>
""",unsafe_allow_html=True)

# ---------- COLOR HELPERS ----------
def text_color(bg_hex):
    bg_hex = bg_hex.lstrip("#")
    r,g,b = int(bg_hex[0:2],16), int(bg_hex[2:4],16), int(bg_hex[4:6],16)
    luminance = (0.299*r + 0.587*g + 0.114*b)/255
    return "#000000" if luminance>0.5 else "#FFFFFF"

# ---------- TOP BAR ----------
st.markdown('<div class="topbar">',unsafe_allow_html=True)
b1,b2 = st.columns([1,1])
with b1:
    st.button("➕",use_container_width=True,
              on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
with b2:
    st.button("🔍",use_container_width=True,
              on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
st.markdown("</div>",unsafe_allow_html=True)
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- ALL CATEGORIES ----------
all_cats=set()
for r in st.session_state.recipes:
    all_cats.update(r.get("category",[]))
all_cats=sorted(all_cats)
selected_cat = st.selectbox("Kategorie",["Vše"]+all_cats)

# ---------- CONVERSIONS ----------
unit_map={"ml":1,"l":1000,"g":1,"kg":1000,"lžíce":15,"lžička":5,"hrnek":240}
density={"voda":1,"mléko":1.03,"olej":0.92,"med":1.42}
ignore_units=["ks","vejce","špetka"]

def parse_qty(q):
    try:return float(sum(Fraction(x) for x in q.replace(",",".").split()))
    except:
        try:return float(q)
        except:return None

def convert_line(line):
    m=re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)",line.strip())
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

    selected_cats_new = st.multiselect("Kategorie",all_cats)
    new_cat_new = st.text_input("Nová kategorie")
    color = st.color_picker("Barva kategorie","#4ECDC4")

    def save_new():
        cats=selected_cats_new.copy()
        if new_cat_new.strip():
            cats.append(new_cat_new.strip())
        if not cats:
            cats=["slané"]
        st.session_state.recipes.insert(0,{
            "id":new_id(),
            "name":n or "Bez názvu",
            "portions":por,
            "ingredients":convert_text(split_ingredients(ing)),
            "steps":steps,
            "category":cats,
            "color":color,
            "fav":False
        })
        save_db()
        st.session_state.show_new=False

    st.button("Uložit",on_click=save_new)

# ---------- FILTER ----------
recipes_sorted=sorted(st.session_state.recipes,key=lambda x:(not x.get("fav",False),x["name"]))
recipes_filtered=[]
terms=search.lower().split()
for r in recipes_sorted:
    if selected_cat!="Vše" and selected_cat not in r.get("category",[]):
        continue
    text=(r["name"]+" "+r["ingredients"]).lower()
    if terms and not all(term in text for term in terms):
        continue
    recipes_filtered.append(r)

# ---------- DISPLAY ----------
for r in recipes_filtered:
    color=r.get("color","#1E3A8A")
    tcolor=text_color(color)
    title=("⭐ "+r["name"]) if r.get("fav") else r["name"]

    st.markdown(f"""
    <div style="background:{color};color:{tcolor};padding:6px;border-radius:8px;font-weight:bold;">
    {r['name']}
    </div>
    """,unsafe_allow_html=True)

    with st.expander("Otevřít recept"):
        if st.session_state.edit_id==r["id"]:
            en=st.text_input("Název",r["name"])
            ep=st.number_input("Porce",1,20,r["portions"])
            ei=st.text_area("Ingredience",r["ingredients"])
            es=st.text_area("Postup",r["steps"])

            def save_edit(r=r):
                r.update({
                    "name":en,
                    "portions":ep,
                    "ingredients":convert_text(split_ingredients(ei)),
                    "steps":es
                })
                st.session_state.edit_id=None
                save_db()

            st.button("💾 Uložit změny",on_click=save_edit)

        else:
            st.markdown("**Ingredience**")
            for l in r["ingredients"].splitlines():
                st.markdown(f"<p>• {l}</p>",unsafe_allow_html=True)

            st.markdown("**Postup**")
            for l in r["steps"].splitlines():
                st.markdown(f"<p>{l}</p>",unsafe_allow_html=True)

            c1,c2,c3=st.columns([1,1,1])
            c1.button("⭐",key=r["id"]+"f",on_click=lambda r=r:[r.update({"fav":not r["fav"]}),save_db()])
            c2.button("✏️",key=r["id"]+"e",on_click=lambda r=r:st.session_state.update({"edit_id":r["id"]}))
            c3.button("🗑",key=r["id"]+"d",on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db()])
