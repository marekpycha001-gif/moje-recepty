import streamlit as st
import json, os, re, time, random, string
from fractions import Fraction
from streamlit_sortable import sortable_container, sortable_item  # drag-and-drop

# ---------- PAGE ----------
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

def clean(x):
    return int(x) if x==int(x) else round(x,2)

# ---------- SESSION ----------
defaults = {
    "recipes": [],
    "show_new": False,
    "show_search": False,
    "edit_id": None,
    "tags": {}  # globální štítky
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

RECIPES_FILE = "recipes.json"
TAGS_FILE = "tags.json"

# ---------- LOAD ----------
if not st.session_state.recipes:
    st.session_state.recipes = safe_load_json(RECIPES_FILE,[])
if not st.session_state.tags:
    st.session_state.tags = safe_load_json(TAGS_FILE,{
        "dezert":"#FFB6C1",
        "oběd":"#4CAF50",
        "Itálie":"#FFA500",
        "Asie":"#00BCD4",
        "slané pečivo":"#FF5722",
        "chuťovky":"#9C27B0",
        "jiné":"#607D8B"
    })

def save_db():
    safe_save_json(RECIPES_FILE,st.session_state.recipes)
    safe_save_json(TAGS_FILE,st.session_state.tags)

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
font-size:28px;
text-align:center;
color:#00ccff;
margin-bottom:10px;
}
.topbar{
position:sticky;
top:0;
z-index:999;
background:#000428;
padding-bottom:6px;
}
.block-container{padding-top:1rem;}
</style>
""",unsafe_allow_html=True)

# ---------- TOP BAR ----------
st.markdown('<div class="topbar">',unsafe_allow_html=True)
c1,c2,c3=st.columns([1,1,2])
c1.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
c2.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
st.markdown("</div>",unsafe_allow_html=True)
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- UNITS ----------
unit_mode=st.selectbox("Jednotky",["Původní","Gramy","Mililitry"])

unit_map={
    "ml":1,"l":1000,"g":1,"kg":1000,
    "lžíce":15,"lžička":5,
    "hrnek":240,"cup":240
}

density_db={
    "voda":1,
    "mléko":1.03,
    "olej":0.92,
    "med":1.42,
    "mouka":0.53,
    "cukr":0.85,
    "sůl":1.2
}

ignore_units=["ks","kus","vejce","špetka","trochu"]

def normalize_unit(u):
    if not u: return u
    u=u.lower()
    variants={
        "hrnky":"hrnek","hrnku":"hrnek","hrncích":"hrnek",
        "lžičky":"lžička","lžiček":"lžička",
        "lžíce":"lžíce","lžící":"lžíce"
    }
    return variants.get(u,u)

def parse_qty(q):
    q=q.replace(",",".")
    try:
        return float(sum(Fraction(x) for x in q.split()))
    except:
        try: return float(q)
        except: return None

def find_density(name):
    name=name.lower()
    for k,v in density_db.items():
        if k in name:
            return v
    return 1

def convert_line(line,scale):
    line=line.strip()
    m=re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)",line)
    if not m: return line
    qty,unit,name=m.groups()
    val=parse_qty(qty)
    if val is None: return line
    val*=scale
    unit=normalize_unit(unit)
    if unit_mode=="Původní": return f"{clean(val)} {unit or ''} {name}".strip()
    if unit in ignore_units: return f"{clean(val)} {unit or ''} {name}".strip()
    coef=unit_map.get(unit)
    if not coef: return f"{clean(val)} {unit or ''} {name}".strip()
    ml=val*coef
    if unit_mode=="Mililitry": return f"{clean(ml)} ml {name}"
    g=ml*find_density(name)
    return f"{clean(g)} g {name}"

def convert_text(text,scale):
    return "\n".join(convert_line(l,scale) for l in text.splitlines() if l.strip())

def split_ingredients(text):
    text=text.replace(",",".")
    parts=re.split(r'(?<!\d),(?!\d)|\s+a\s+', text)
    return "\n".join(p.strip() for p in parts if p.strip())

# ---------- RECIPE FORM ----------
def recipe_form(r=None):
    if r:
        st.subheader("Upravit recept")
        n=r["name"]
        por=r["portions"]
        ing=r["ingredients"]
        steps=r["steps"]
        selected_tags=r.get("tags",[])
    else:
        st.subheader("Nový recept")
        n=""
        por=4
        ing=""
        steps=""
        selected_tags=[]

    n=st.text_input("Název",n)
    por=st.number_input("Porce",1,20,por)
    ing=st.text_area("Ingredience",ing)
    steps=st.text_area("Postup",steps)

    # multi-select štítky
    tag_names=list(st.session_state.tags.keys())
    selected_tags=st.multiselect("Štítky",tag_names,default=selected_tags)

    # přidání nového štítku
    with st.expander("Přidat nový štítek"):
        new_tag_name=st.text_input("Název štítku")
        new_tag_color=st.color_picker("Barva štítku","#AAAAAA")
        if st.button("Přidat štítek"):
            if new_tag_name and new_tag_name not in st.session_state.tags:
                st.session_state.tags[new_tag_name]=new_tag_color
                save_db()
                st.rerun()

    if st.button("Uložit recept"):
        data={
            "id": r["id"] if r else new_id(),
            "name": n or "Bez názvu",
            "portions": por,
            "ingredients": split_ingredients(ing),
            "steps": steps,
            "tags": selected_tags
        }
        if r:
            # update
            idx=[i for i,x in enumerate(st.session_state.recipes) if x["id"]==r["id"]][0]
            st.session_state.recipes[idx]=data
        else:
            st.session_state.recipes.insert(0,data)
        save_db()
        st.session_state.edit_id=None
        st.rerun()

# ---------- SHOW RECIPES WITH DRAG & DROP ----------
def show_recipes():
    search_lower = search.lower() if search else ""
    recipes = st.session_state.recipes

    with sortable_container(key="recipe_sort"):
        for r in recipes:
            if search and search_lower not in (r["name"]+r["ingredients"]).lower():
                continue
            with sortable_item(r["id"]):
                with st.expander(r["name"],expanded=False):
                    # edit
                    if st.session_state.edit_id==r["id"]:
                        recipe_form(r)
                    else:
                        # porce
                        new_portions=st.number_input("Porce",1,50,r["portions"],key="p"+r["id"])
                        scale=new_portions/r["portions"]

                        # štítky
                        tag_line=""
                        for t in r.get("tags",[]):
                            color=st.session_state.tags.get(t,"#CCCCCC")
                            tag_line+=f'<span style="background:{color};padding:2px 6px;border-radius:6px;margin-right:4px;">{t}</span>'
                        if tag_line: st.markdown(tag_line,unsafe_allow_html=True)

                        # ingredience
                        st.markdown("**Ingredience**")
                        for l in convert_text(r["ingredients"],scale).splitlines():
                            st.write("•",l)

                        # postup
                        st.markdown("**Postup**")
                        st.write(r["steps"])

                        # tlačítka
                        c1,c2=st.columns(2)
                        c1.button("✏️ Upravit",key="e"+r["id"],on_click=lambda r=r:st.session_state.update({"edit_id":r["id"]}))
                        c2.button("🗑 Smazat",key="d"+r["id"],on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db(),st.rerun()])

show_recipes()

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    recipe_form()
