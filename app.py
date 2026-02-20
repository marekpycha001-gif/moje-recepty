import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os, re

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {
    "api":"",
    "recipes":[],
    "show_new":False,
    "show_search":False,
    "show_api":False
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- AI ----------
def ai(txt):
    try:
        genai.configure(api_key=st.session_state.api)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = """
Z textu vytvoř recept ve formátu:

NAZEV: ...
DOBA: ...
KALORIE: ...
INGREDIENCE:
- ...
POSTUP:
1. ...
"""
        return model.generate_content([prompt, txt]).text
    except Exception as e:
        return f"AI chyba: {e}"

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE,encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def load_db():
    try:
        r=requests.get(SDB_URL,timeout=5)
        if r.status_code==200:
            data=[]
            for x in r.json():
                data.append({
                    "id":x.get("id",""),
                    "title":x.get("nazev","Bez názvu"),
                    "text":x.get("text",""),
                    "fav":str(x.get("fav","")).lower()=="true"
                })
            return data
    except:
        pass
    return load_local()

def save_db():
    try:
        for r in st.session_state.recipes:
            if not r.get("id"):
                res=requests.post(SDB_URL,json={
                    "text":r["text"],
                    "nazev":r["title"],
                    "fav":"true" if r["fav"] else "false"
                })
                if res.status_code==200:
                    r["id"]=res.json()["created"]
            else:
                requests.patch(f"{SDB_URL}/id/{r['id']}",json={
                    "text":r["text"],
                    "nazev":r["title"],
                    "fav":"true" if r["fav"] else "false"
                })
    except:
        pass
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- DESIGN ----------
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
}

.stExpanderContent{
 background:#cce0ff !important;
 color:black;
 border-radius:10px;
}
</style>
""",unsafe_allow_html=True)

# ---------- IKONY NAHOŘE (BEZ RELOADU) ----------
c1,c2,c3,c4 = st.columns(4)

with c1:
    if st.button("➕", use_container_width=True):
        st.session_state.show_new = not st.session_state.show_new

with c2:
    if st.button("🔄", use_container_width=True):
        save_db()

with c3:
    if st.button("🔍", use_container_width=True):
        st.session_state.show_search = not st.session_state.show_search

with c4:
    if st.button("🔑", use_container_width=True):
        st.session_state.show_api = not st.session_state.show_api

# ---------- TITLE ----------
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api = st.text_input("API klíč",type="password")

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat podle názvu nebo ingredience")

# ---------- NOVÝ RECEPT ----------
if st.session_state.show_new:

    tab1,tab2 = st.tabs(["Text","Foto"])

    with tab1:
        with st.form("add"):
            txt = st.text_area("Text")
            title = st.text_input("Název")
            if st.form_submit_button("Uložit"):
                if txt:
                    st.session_state.recipes.insert(0,{
                        "id":"",
                        "title":title or "Bez názvu",
                        "text":ai(txt),
                        "fav":False
                    })
                    save_db()
                    st.rerun()

    with tab2:
        img = st.file_uploader("Foto",type=["jpg","png"])
        title2 = st.text_input("Název foto")
        if img and st.button("Uložit foto"):
            st.session_state.recipes.insert(0,{
                "id":"",
                "title":title2 or "Bez názvu",
                "text":ai(Image.open(img)),
                "fav":False
            })
            save_db()
            st.rerun()

# ---------- LIST ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in (r["title"]+r["text"]).lower():
        continue

    with st.expander(r["title"]):

        nt = st.text_input("Název",r["title"],key=f"t{i}")
        tx = st.text_area("Text",r["text"],key=f"x{i}",height=250)

        c1,c2,c3 = st.columns(3)

        with c1:
            if st.button("💾",key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                save_db()
                st.rerun()

        with c2:
            if st.button("⭐",key=f"f{i}"):
                st.session_state.recipes[i]["fav"]=not st.session_state.recipes[i]["fav"]
                save_db()
                st.rerun()

        with c3:
            if st.button("🗑",key=f"d{i}"):
                rid = st.session_state.recipes[i].get("id")
                if rid:
                    try:
                        requests.delete(f"{SDB_URL}/id/{rid}")
                    except:
                        pass
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
