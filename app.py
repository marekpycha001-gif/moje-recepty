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
defaults = {"recipes": [],"show_new": False,"show_search": False,"edit_id": None,"tags": {}}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

RECIPES_FILE="recipes.json"
TAGS_FILE="tags.json"

if not st.session_state.recipes:
    st.session_state.recipes=safe_load_json(RECIPES_FILE,[])

if not st.session_state.tags:
    st.session_state.tags=safe_load_json(TAGS_FILE,{
        "dezert":"#FFB6C1","oběd":"#4CAF50","Itálie":"#FFA500",
        "Asie":"#00BCD4","slané pečivo":"#FF5722","chuťovky":"#9C27B0","jiné":"#607D8B"
    })

def save_db():
    safe_save_json(RECIPES_FILE,st.session_state.recipes)
    safe_save_json(TAGS_FILE,st.session_state.tags)

# ---------- STYLE ----------
st.markdown("""
<style>

header{visibility:hidden;}

[data-testid="stAppViewContainer"]{
animation:fadein 0.6s ease;
}

@keyframes fadein{
from{opacity:0; transform:translateY(10px)}
to{opacity:1; transform:translateY(0)}
}

body,[data-testid="stAppViewContainer"]{
background:radial-gradient(circle at bottom,#000428,#004e92);
color:white;
}

.title{
font-size:30px;
text-align:center;
color:#00ccff;
margin-bottom:12px;
font-weight:700;
letter-spacing:.5px;
}

.topbar{
position:sticky;
top:0;
z-index:999;
background:#000428;
padding-bottom:6px;
}

.topbuttons{display:flex;gap:6px;}
.topbuttons button{
font-size:14px!important;
padding:4px 12px!important;
border-radius:8px!important;
transition:all .15s ease!important;
}

.topbuttons button:hover{
transform:scale(1.08);
}

.ingredients p{
margin:0;
padding:0;
line-height:1.05;
font-size:15px;
}

[data-testid="stExpander"]{
border-radius:14px!important;
overflow:hidden!important;
transition:all .25s ease;
border:1px solid rgba(255,255,255,.05)!important;
}

[data-testid="stExpander"]:hover{
transform:scale(1.01);
box-shadow:0 0 18px rgba(0,0,0,.35);
}

button[kind="secondary"]{
border-radius:10px!important;
transition:.15s;
}
button[kind="secondary"]:hover{
transform:scale(1.05);
}

.tag{
display:inline-block;
padding:3px 8px;
border-radius:8px;
font-size:13px;
margin-right:4px;
margin-bottom:3px;
font-weight:500;
}

</style>
""",unsafe_allow_html=True)

# ---------- TOP ----------
st.markdown('<div class="topbar"><div class="topbuttons">',unsafe_allow_html=True)
c1,c2=st.columns([1,1])
c1.button("➕",on_click=lambda:st.session_state.update({"show_new":not st.session_state.show_new}))
c2.button("🔍",on_click=lambda:st.session_state.update({"show_search":not st.session_state.show_search}))
st.markdown("</div></div>",unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat").lower()

# ---------- FILTER TAG ----------
tags=list(st.session_state.tags.keys())
selected_tag=st.selectbox("Filtrovat štítek",["Vše"]+tags)

# ---------- UNITS ----------
unit_mode=st.selectbox("Jednotky",["Původní","Gramy","Mililitry"])

unit_map={"ml":1,"l":1000,"g":1,"kg":1000,"lžíce":15,"lžička":5,"hrnek":240,"cup":240}
density_db={"voda":1,"mléko":1.03,"olej":0.92,"med":1.42,"mouka":0.53,"cukr":0.85,"sůl":1.2}
ignore_units=["ks","kus","vejce","špetka","trochu"]

def normalize_unit(u):
    if not u:return u
    u=u.lower()
    return {"hrnky":"hrnek","hrnku":"hrnek","lžičky":"lžička","lžiček":"lžička","lžící":"lžíce"}.get(u,u)

def parse_qty(q):
    q=q.replace(",",".")
    try:return float(sum(Fraction(x) for x in q.split()))
    except:
        try:return float(q)
        except:return None

def clean(x):
    return int(x) if x==int(x) else round(x,2)

def find_density(name):
    name=name.lower()
    for k,v in density_db.items():
        if k in name:return v
    return 1

def convert_line(line,scale):
    line=line.strip()
    m=re.match(r"([\d\/\.,\s]+)\s*([^\d\s]+)?\s*(.*)",line)
    if not m:return line
    qty,unit,name=m.groups()
    val=parse_qty(qty)
    if val is None:return line
    val*=scale
    unit=normalize_unit(unit)

    if unit_mode=="Původní" or unit in ignore_units:
        return f"{clean(val)} {unit or ''} {name}".strip()

    coef=unit_map.get(unit)
    if not coef:return f"{clean(val)} {unit or ''} {name}".strip()

    ml=val*coef
    if unit_mode=="Mililitry":
        return f"{clean(ml)} ml {name}"

    g=ml*find_density(name)
    return f"{clean(g)} g {name}"

def convert_text(text,scale):
    return "\n".join(convert_line(l,scale) for l in text.splitlines() if l.strip())

def split_ingredients(text):
    text=text.replace(",",".")
    parts=re.split(r'(?<!\d),(?!\d)|\s+a\s+', text)
    return "\n".join(p.strip() for p in parts if p.strip())

# ---------- FORM ----------
def recipe_form(r=None):

    if r:
        n=r["name"]; por=r["portions"]; ing=r["ingredients"]; steps=r["steps"]; sel=r.get("tags",[])
        st.subheader("Upravit recept")
    else:
        n=""; por=4; ing=""; steps=""; sel=[]
        st.subheader("Nový recept")

    n=st.text_input("Název",n)
    por=st.number_input("Porce",1,20,por)
    ing=st.text_area("Ingredience",ing)
    steps=st.text_area("Postup",steps)

    sel=st.multiselect("Štítky",list(st.session_state.tags.keys()),default=sel)

    with st.expander("Nový štítek"):
        name=st.text_input("Název")
        col=st.color_picker("Barva","#AAAAAA")
        if st.button("Přidat štítek"):
            if name and name not in st.session_state.tags:
                st.session_state.tags[name]=col
                save_db()
                st.rerun()

    if st.button("Uložit recept"):
        data={"id":r["id"] if r else new_id(),"name":n or "Bez názvu","portions":por,
              "ingredients":split_ingredients(ing),"steps":steps,"tags":sel,
              "last":r.get("last",0) if r else 0}

        if r:
            idx=[i for i,x in enumerate(st.session_state.recipes) if x["id"]==r["id"]][0]
            st.session_state.recipes[idx]=data
        else:
            st.session_state.recipes.insert(0,data)

        save_db()
        st.session_state.edit_id=None
        st.rerun()

# ---------- SORT ----------
st.session_state.recipes=sorted(st.session_state.recipes,key=lambda x:x.get("last",0),reverse=True)

# ---------- SHOW ----------
for r in st.session_state.recipes:

    if selected_tag!="Vše" and selected_tag not in r.get("tags",[]):continue
    if search:
        text=(r["name"]+" "+r["ingredients"]).lower()
        if search not in text:continue

    with st.expander(r["name"]):

        r["last"]=time.time()
        save_db()

        if st.session_state.edit_id==r["id"]:
            recipe_form(r)

        else:
            newp=st.number_input("Porce",1,50,r["portions"],key="p"+r["id"])
            scale=newp/r["portions"]

            line=""
            for t in r.get("tags",[]):
                color=st.session_state.tags.get(t,"#ccc")
                line+=f'<span class="tag" style="background:{color}">{t}</span>'
            if line:st.markdown(line,unsafe_allow_html=True)

            st.markdown("**Ingredience**")
            html="<div class='ingredients'>"
            for l in convert_text(r["ingredients"],scale).splitlines():
                html+=f"<p>• {l}</p>"
            html+="</div>"
            st.markdown(html,unsafe_allow_html=True)

            st.markdown("**Postup**")
            st.write(r["steps"])

            c1,c2=st.columns(2)
            c1.button("✏️ Upravit",key="e"+r["id"],on_click=lambda r=r:st.session_state.update({"edit_id":r["id"]}))
            c2.button("🗑 Smazat",key="d"+r["id"],on_click=lambda r=r:[st.session_state.recipes.remove(r),save_db(),st.rerun()])
