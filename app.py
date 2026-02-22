import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

DB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL="recipes.json"

# ---------- SESSION ----------
defaults={
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
def ai_process(content):
    if not st.session_state.api:
        return content

    try:
        genai.configure(api_key=st.session_state.api)

        models=[m.name for m in genai.list_models()
                if "generateContent" in m.supported_generation_methods]

        model_name=None
        for m in models:
            if "2.0" in m:
                model_name=m
                break
        if not model_name:
            model_name=models[0]

        model=genai.GenerativeModel(model_name)

        prompt="""
Uprav tento recept do přehledné struktury.
Odpovídej česky.

Formát:
NÁZEV:
INGREDIENCE:
POSTUP:
"""

        res=model.generate_content([prompt,content])
        return res.text

    except Exception as e:
        return f"AI chyba: {e}"

# ---------- DB ----------
def load_local():
    if os.path.exists(LOCAL):
        return json.load(open(LOCAL,encoding="utf8"))
    return []

def save_local(d):
    json.dump(d,open(LOCAL,"w",encoding="utf8"),ensure_ascii=False,indent=2)

def load_db():
    try:
        r=requests.get(DB_URL,timeout=3)
        if r.status_code==200:
            return [{"title":x.get("nazev","Bez názvu"),
                     "text":x.get("text",""),
                     "fav":str(x.get("fav","")).lower()=="true"} for x in r.json()]
    except: pass
    return load_local()

def save_db():
    try:
        requests.delete(DB_URL+"/all",timeout=3)
        requests.post(DB_URL,json=[{
            "text":r["text"],
            "nazev":r["title"],
            "fav":"true" if r["fav"] else "false"
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
 margin-bottom:8px;
}

.toolbar{
 display:flex;
 justify-content:center;
 gap:8px;
 margin-bottom:8px;
}

.toolbar button{
 background:#0099ff;
 border:none;
 color:white;
 padding:6px 10px;
 font-size:18px;
 border-radius:8px;
 cursor:pointer;
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

# ---------- TOOLBAR ----------
c1,c2,c3,c4=st.columns(4)
with c1:
    if st.button("➕"): st.session_state.show_new=not st.session_state.show_new
with c2:
    if st.button("🔄"): save_db()
with c3:
    if st.button("🔍"): st.session_state.show_search=not st.session_state.show_search
with c4:
    if st.button("🔑"): st.session_state.show_api=not st.session_state.show_api

st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api=st.text_input("API klíč",type="password")

# ---------- SEARCH ----------
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat")

# ---------- ADD ----------
if st.session_state.show_new:

    tab1,tab2,tab3=st.tabs(["Ruční","Web","Obrázek"])

    # ruční
    with tab1:
        with st.form("manual"):
            t=st.text_input("Název")
            txt=st.text_area("Text receptu")
            if st.form_submit_button("Uložit"):
                st.session_state.recipes.insert(0,{
                    "title":t or "Bez názvu",
                    "text":txt,
                    "fav":False
                })
                save_db()
                st.rerun()

    # web
    with tab2:
        with st.form("web"):
            url=st.text_input("URL receptu")
            t=st.text_input("Název")
            if st.form_submit_button("Načíst"):
                if url:
                    page=requests.get(url).text
                    text=ai_process(page)
                    st.session_state.recipes.insert(0,{
                        "title":t or "Bez názvu",
                        "text":text,
                        "fav":False
                    })
                    save_db()
                    st.rerun()

    # image
    with tab3:
        img=st.file_uploader("Obrázek",type=["jpg","png"])
        t=st.text_input("Název")
        if img and st.button("Načíst obrázek"):
            text=ai_process(Image.open(img))
            st.session_state.recipes.insert(0,{
                "title":t or "Bez názvu",
                "text":text,
                "fav":False
            })
            save_db()
            st.rerun()

# ---------- LIST ----------
for i,r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["title"].lower() and search.lower() not in r["text"].lower():
        continue

    star="⭐" if r["fav"] else "☆"

    with st.expander(f"{star} {r['title']}"):

        nt=st.text_input("Název",r["title"],key=f"t{i}")
        tx=st.text_area("Text",r["text"],key=f"x{i}",height=250)

        c1,c2,c3=st.columns(3)

        with c1:
            if st.button("💾",key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                save_db()
                st.rerun()

        with c2:
            if st.button("⭐",key=f"f{i}"):
                st.session_state.recipes[i]["fav"]=not r["fav"]
                save_db()
                st.rerun()

        with c3:
            if st.button("🗑",key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
