import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os, re

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
for k,v in {
    "show_api":False,
    "show_new":False,
    "show_search":False,
    "api_key":"",
    "recipes":[]
}.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- FUNKCE ----------
def ai(txt):
    try:
        genai.configure(api_key=st.session_state.api_key)
        m=[m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods][0]
        model=genai.GenerativeModel(m)
        p="Vytvoř recept: NAZEV:, INGREDIENCE:, POSTUP:"
        return model.generate_content([p,txt]).text
    except Exception as e:
        return f"AI chyba: {e}"

def save_local(d):
    with open(LOCAL_FILE,"w",encoding="utf8") as f:
        json.dump(d,f,ensure_ascii=False,indent=2)

def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE,encoding="utf8"))
    return []

def load_db():
    try:
        r=requests.get(SDB_URL,timeout=3)
        if r.status_code==200:
            return [{"title":x.get("nazev","Bez názvu"),
                     "text":x.get("text",""),
                     "fav":str(x.get("fav","")).lower()=="true"}
                    for x in r.json()]
    except: pass
    return load_local()

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=3)
        requests.post(SDB_URL,json=[{
            "text":r["text"],
            "fav":"true" if r["fav"] else "false",
            "nazev":r["title"]
        } for r in st.session_state.recipes],timeout=3)
    except: pass
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

[data-testid="stHorizontalBlock"]{
 display:flex;
 flex-wrap:nowrap !important;
}

[data-testid="column"]{
 flex:1 1 0 !important;
 min-width:0 !important;
}

button{
 width:100%;
 height:40px;
 font-size:18px !important;
 border-radius:10px !important;
 background:#0099ff !important;
 color:white !important;
 border:none !important;
}

body,[data-testid="stAppViewContainer"]{
 background:radial-gradient(circle at bottom,#000428,#004e92);
 color:white;
}

.title{
 font-family:'Dancing Script',cursive;
 font-size:20px;
 text-align:center;
 color:#00ccff;
 margin-top:-10px;
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

label{color:white !important;}
</style>
""",unsafe_allow_html=True)

# ---------- IKONY ----------
c1,c2,c3,c4=st.columns(4)

with c1:
    if st.button("➕"):
        st.session_state.show_new=not st.session_state.show_new
with c2:
    if st.button("🔄"):
        save_db()
with c3:
    if st.button("🔍"):
        st.session_state.show_search=not st.session_state.show_search
with c4:
    if st.button("🔑"):
        st.session_state.show_api=not st.session_state.show_api

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api_key=st.text_input("API klíč",type="password")

# ---------- SEARCH ----------
search=st.text_input("Hledat") if st.session_state.show_search else ""

# ---------- NOVÝ ----------
if st.session_state.show_new:
    t1,t2=st.tabs(["Text","Foto"])

    with t1:
        with st.form("f"):
            txt=st.text_area("Text")
            title=st.text_input("Název")
            if st.form_submit_button("Uložit"):
                if txt:
                    st.session_state.recipes.insert(0,{
                        "title":title or "Bez názvu",
                        "text":ai(txt),
                        "fav":False
                    })
                    save_db()
                    st.rerun()

    with t2:
        img=st.file_uploader("Foto",type=["jpg","png"])
        title2=st.text_input("Název foto")
        if img and st.button("Uložit foto"):
            st.session_state.recipes.insert(0,{
                "title":title2 or "Bez názvu",
                "text":ai(Image.open(img)),
                "fav":False
            })
            save_db()
            st.rerun()

# ---------- LIST ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["title"].lower():
        continue

    with st.expander(r["title"]):
        st.write(r["text"])
        if st.button("Smazat",key=i):
            st.session_state.recipes.pop(i)
            save_db()
            st.rerun()
