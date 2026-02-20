import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {
    "show_api":False,
    "show_new":False,
    "show_search":False,
    "api_key":"",
    "recipes":[]
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ---------- FUNKCE ----------
def ai(txt):
    try:
        genai.configure(api_key=st.session_state.api_key)
        m=[m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods][0]
        model=genai.GenerativeModel(m)
        prompt="Vytvoř recept: NAZEV:, INGREDIENCE:, POSTUP:"
        return model.generate_content([prompt,txt]).text
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

.iconbar{
 display:flex;
 justify-content:center;
 gap:8px;
 margin-bottom:5px;
}

.iconbar button{
 width:45px !important;
 height:38px !important;
 font-size:18px !important;
 border-radius:10px !important;
 background:#0099ff !important;
 color:white !important;
 border:none !important;
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
st.markdown('<div class="iconbar">',unsafe_allow_html=True)
b1,b2,b3,b4=st.columns([1,1,1,1])
with b1:
    if st.button("➕"): st.session_state.show_new=not st.session_state.show_new
with b2:
    if st.button("🔄"): save_db()
with b3:
    if st.button("🔍"): st.session_state.show_search=not st.session_state.show_search
with b4:
    if st.button("🔑"): st.session_state.show_api=not st.session_state.show_api
st.markdown('</div>',unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api_key=st.text_input("API klíč",type="password")

# ---------- SEARCH ----------
search=st.text_input("Hledat") if st.session_state.show_search else ""

# ---------- NOVÝ ----------
if st.session_state.show_new:

    tab1,tab2=st.tabs(["Text","Foto"])

    with tab1:
        with st.form("new"):
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

    with tab2:
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

# ---------- SEZNAM ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["title"].lower():
        continue

    with st.expander(r["title"]):

        new_title=st.text_input("Název",r["title"],key=f"title{i}")
        new_text=st.text_area("Text",r["text"],key=f"text{i}",height=250)

        c1,c2=st.columns(2)

        with c1:
            if st.button("💾 Uložit",key=f"s{i}"):
                st.session_state.recipes[i]["title"]=new_title
                st.session_state.recipes[i]["text"]=new_text
                save_db()
                st.rerun()

        with c2:
            if st.button("🗑 Smazat",key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
