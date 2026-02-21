import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

# ========= KONFIG =========
SDB_URL="https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE="recipes.json"

# ========= SESSION =========
defaults={
    "api":"",
    "recipes":[],
    "show_new":False,
    "show_search":False,
    "show_api":False,
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k]=v

# ========= AI =========
def ai(txt):
    if not st.session_state.api:
        return txt
    try:
        genai.configure(api_key=st.session_state.api)

        model=genai.GenerativeModel("gemini-1.5-flash")

        prompt=f"""
Uprav tento recept do přehledné struktury.
Jazyk: čeština
Formát:
NÁZEV:
INGREDIENCE:
POSTUP:

Text:
{txt}
"""
        return model.generate_content(prompt).text

    except Exception as e:
        return f"AI chyba: {e}"


# ========= STORAGE =========
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
            return [{
                "title":x.get("nazev","Bez názvu"),
                "text":x.get("text",""),
                "fav":str(x.get("fav","false")).lower()=="true"
            } for x in r.json()]
    except:
        pass
    return load_local()

def save_db():
    try:
        requests.delete(SDB_URL+"/all",timeout=3)
        requests.post(SDB_URL,json=[{
            "text":r["text"],
            "fav":"true" if r["fav"] else "false",
            "nazev":r["title"]
        } for r in st.session_state.recipes],timeout=3)
    except:
        pass
    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes=load_db()

# ========= DESIGN =========
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

body,[data-testid="stAppViewContainer"]{
 background:radial-gradient(circle at bottom,#000428,#004e92);
 color:white;
}

/* IKONY */
.topbar{
 display:flex;
 justify-content:center;
 gap:6px;
 margin-bottom:10px;
}

.topbtn{
 background:#0099ff;
 color:white;
 border:none;
 padding:6px 10px;
 border-radius:10px;
 font-size:18px;
 cursor:pointer;
}

/* NADPIS */
.title{
 font-family:'Dancing Script',cursive;
 font-size:20px;
 text-align:center;
 color:#00ccff;
 margin-bottom:15px;
}

/* KARTA */
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

# ========= IKONY =========
c1,c2,c3,c4=st.columns([1,1,1,1])

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


# ========= TITLE =========
st.markdown('<div class="title">Márova kuchařka</div>',unsafe_allow_html=True)

# ========= API =========
if st.session_state.show_api:
    st.session_state.api=st.text_input("API klíč",type="password")

# ========= SEARCH =========
search=""
if st.session_state.show_search:
    search=st.text_input("Hledat podle názvu nebo textu")

# ========= NOVÝ RECEPT =========
if st.session_state.show_new:

    tab1,tab2=st.tabs(["Ručně","AI"])

    # RUČNÍ
    with tab1:
        with st.form("manual"):
            title=st.text_input("Název")
            text=st.text_area("Text receptu")
            if st.form_submit_button("Uložit"):
                if text:
                    st.session_state.recipes.insert(0,{
                        "title":title or "Bez názvu",
                        "text":text,
                        "fav":False
                    })
                    save_db()
                    st.rerun()

    # AI
    with tab2:
        with st.form("ai"):
            title=st.text_input("Název (volitelné)")
            text=st.text_area("Text pro AI")
            if st.form_submit_button("Vygenerovat"):
                if text:
                    st.session_state.recipes.insert(0,{
                        "title":title or "Bez názvu",
                        "text":ai(text),
                        "fav":False
                    })
                    save_db()
                    st.rerun()

# ========= SEZNAM =========
for i,r in enumerate(st.session_state.recipes):

    if search:
        s=search.lower()
        if s not in r["title"].lower() and s not in r["text"].lower():
            continue

    with st.expander(("⭐ " if r["fav"] else "")+r["title"]):

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
