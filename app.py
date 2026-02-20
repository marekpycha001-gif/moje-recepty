import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE="recipes.json"

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
def ai(txt):
    try:
        genai.configure(api_key=st.session_state.api)
        model=genai.GenerativeModel("gemini-1.5-flash")
        return model.generate_content(txt).text
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
        r=requests.get(SDB_URL,timeout=3)
        if r.status_code==200:
            return [{"title":x.get("nazev","Bez názvu"),
                     "text":x.get("text",""),
                     "fav":False} for x in r.json()]
    except: pass
    return load_local()

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=3)
        requests.post(SDB_URL,json=[{
            "text":r["text"],
            "fav":"false",
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

/* TOP BAR */
.topbar{
 display:flex;
 justify-content:center;
 gap:6px;
 margin-top:-10px;
 margin-bottom:5px;
}

.topbtn{
 background:#0099ff;
 color:white;
 border:none;
 padding:6px 10px;
 border-radius:8px;
 font-size:18px;
 cursor:pointer;
}

/* TITLE */
.title{
 font-family:'Dancing Script',cursive;
 font-size:20px;
 text-align:center;
 color:#00ccff;
 margin-bottom:10px;
}

/* EXPANDER */
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

# ---------- TOP ICON BAR ----------
clicked=st.query_params.get("btn","")

st.markdown(f"""
<div class="topbar">
<a href="?btn=new"><button class="topbtn">➕</button></a>
<a href="?btn=sync"><button class="topbtn">🔄</button></a>
<a href="?btn=search"><button class="topbtn">🔍</button></a>
<a href="?btn=api"><button class="topbtn">🔑</button></a>
</div>
""",unsafe_allow_html=True)

# ---------- ACTIONS ----------
if clicked=="new":
    st.session_state.show_new=not st.session_state.show_new
if clicked=="search":
    st.session_state.show_search=not st.session_state.show_search
if clicked=="api":
    st.session_state.show_api=not st.session_state.show_api
if clicked=="sync":
    save_db()

# ---------- TITLE ----------
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api=st.text_input("API klíč",type="password")

# ---------- SEARCH ----------
search_txt=""
if st.session_state.show_search:
    search_txt=st.text_input("Hledat recept")

# ---------- NEW ----------
if st.session_state.show_new:
    tab1,tab2=st.tabs(["Text","Foto"])

    with tab1:
        with st.form("add"):
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

# ---------- LIST ----------
for i,r in enumerate(st.session_state.recipes):

    # filtr podle search, ale ukazuje všechny, když search prázdný
    if search_txt and search_txt.lower() not in (r["title"]+r["text"]).lower():
        continue

    with st.expander(r["title"]):

        nt=st.text_input("Název",r["title"],key=f"t{i}")
        tx=st.text_area("Text",r["text"],key=f"x{i}",height=250)

        c1,c2=st.columns(2)

        with c1:
            if st.button("💾 Uložit",key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                save_db()
                st.rerun()

        with c2:
            if st.button("🗑 Smazat",key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
