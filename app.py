import streamlit as st
import json, os, re, requests

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE="recipes.json"

# ---------- SESSION ----------
defaults={
    "recipes":[],
    "show_new":False,
    "show_search":False
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE,encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def load_db():
    recipes=[]
    try:
        r=requests.get(SDB_URL,timeout=3)
        if r.status_code==200:
            for x in r.json():
                recipes.append({
                    "name": x.get("name","Bez názvu"),
                    "type": x.get("type","slané"),
                    "category": x.get("category",""),
                    "portions": x.get("portions",4),
                    "ingredients": x.get("ingredients",""),
                    "steps": x.get("steps",""),
                    "fav": x.get("fav",False)
                })
    except: 
        pass
    if not recipes:
        recipes=load_local()
    for r in recipes:
        r.setdefault("name","Bez názvu")
        r.setdefault("type","slané")
        r.setdefault("category","")
        r.setdefault("portions",4)
        r.setdefault("ingredients","")
        r.setdefault("steps","")
        r.setdefault("fav",False)
    return recipes

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=3)
        requests.post(SDB_URL,json=st.session_state.recipes,timeout=3)
    except: pass
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- DESIGN ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');
body,[data-testid="stAppViewContainer"]{background:radial-gradient(circle at bottom,#000428,#004e92); color:white;}
.topbar{display:flex; justify-content:center; gap:4px; margin-bottom:10px; flex-wrap:nowrap;}
.topbtn{background:#0099ff; color:white; border:none; padding:5px 10px; border-radius:8px; font-size:18px; cursor:pointer;}
.title{font-family:'Dancing Script',cursive; font-size:22px; text-align:center; color:#00ccff; margin-bottom:15px;}
.stExpanderHeader{background:#1E3A8A !important; color:white !important; border-radius:10px;}
.stExpanderContent{background:#cce0ff !important; color:black !important; border-radius:10px;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea{color:black;}
</style>
""",unsafe_allow_html=True)

# ---------- CALLBACKS ----------
def toggle_show_new():
    st.session_state.show_new = not st.session_state.show_new

def toggle_show_search():
    st.session_state.show_search = not st.session_state.show_search

def sync_all():
    save_db()
    st.success("Synchronizováno!")

# ---------- TOP ICON BAR ----------
col1, col2, col3 = st.columns([1,1,1])
with col1:
    st.button("➕", on_click=toggle_show_new)
with col2:
    st.button("🔍", on_click=toggle_show_search)
with col3:
    st.button("☁️ Sync", on_click=sync_all)

# ---------- TITLE ----------
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search = st.text_input("Hledat recept podle názvu/ingrediencí")

# ---------- NEW RECIPE ----------
if st.session_state.show_new:
    st.markdown("### Přidat nový recept")
    name=st.text_input("Název")
    typ=st.radio("Typ",["sladké","slané"],horizontal=True)
    category=st.text_input("Kategorie")
    portions=st.number_input("Počet porcí",1,20,4)
    ingredients=st.text_area("Ingredience (každá na nový řádek)")
    steps=st.text_area("Postup")

    def save_new_recipe():
        st.session_state.recipes.insert(0,{
            "name":name or "Bez názvu",
            "type":typ,
            "category":category,
            "portions":portions,
            "ingredients":ingredients,
            "steps":steps,
            "fav":False
        })
        save_db()
        st.experimental_rerun()

    st.button("Uložit recept", on_click=save_new_recipe)

# ---------- FILTER BY TYPE ----------
st.markdown("### Filtr:")
filt_col1, filt_col2 = st.columns(2)
show_sladke = st.button("Sladké")
show_slane = st.button("Slané")

# ---------- DISPLAY RECIPES ----------
for i,r in enumerate(st.session_state.recipes):
    r.setdefault("portions",4)  # prevent KeyError
    r.setdefault("fav",False)
    r.setdefault("category","")

    title_prefix = ("⭐ " if r.get("fav") else "") + ("🍰 " if r["type"]=="sladké" else "🥩 ")
    title = title_prefix + r["name"]

    if search and search.lower() not in (r["name"]+r["ingredients"]).lower():
        continue
    if show_sladke and r["type"]!="sladké": continue
    if show_slane and r["type"]!="slané": continue

    with st.expander(title):

        mult = st.slider("Porce",1,20,r["portions"],key=f"portions{i}")

        st.markdown(f"**Kategorie:** {r['category']}")

        st.markdown("**Ingredience**")
        for line in r["ingredients"].splitlines():
            m = re.search(r'(\d+)',line)
            if m:
                num=int(m.group(1))
                new=int(num*mult/r["portions"])
                line=line.replace(str(num),str(new),1)
            st.write("•",line)

        st.markdown("**Postup**")
        st.write(r["steps"])

        c1,c2,c3=st.columns([1,1,1])
        def toggle_fav(i=i):
            r["fav"]=not r.get("fav",False)
            save_db()
            st.experimental_rerun()
        st.button("⭐", key=f"fav{i}", on_click=toggle_fav)

        def delete_recipe(i=i):
            st.session_state.recipes.pop(i)
            save_db()
            st.experimental_rerun()
        st.button("🗑", key=f"del{i}", on_click=delete_recipe)

        def sync_recipe(i=i):
            try:
                requests.post(SDB_URL,json=r)
                st.success("Synchronizováno")
            except:
                st.warning("Nepodařilo se připojit k Google Sheet")
        st.button("☁️", key=f"sync{i}", on_click=sync_recipe)
