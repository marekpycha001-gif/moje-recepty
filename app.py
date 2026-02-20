import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {
    "recipes": [],
    "show_new": False,
    "show_search": False,
    "show_api": False,
    "api_key": ""
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- DATA ----------
def load_db():
    try:
        r = requests.get(SDB_URL, timeout=4)
        if r.status_code == 200:
            return [{
                "title": x.get("nazev", "Bez názvu"),
                "text": x.get("text", ""),
                "fav": str(x.get("fav", "")).lower() == "true"
            } for x in r.json()]
    except:
        pass
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_db():
    try:
        requests.delete(SDB_URL + "/all", timeout=4)
        requests.post(SDB_URL, json=[{
            "nazev": r["title"],
            "text": r["text"],
            "fav": "true" if r["fav"] else "false"
        } for r in st.session_state.recipes], timeout=4)
    except:
        pass
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(st.session_state.recipes, f, ensure_ascii=False, indent=2)

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- AI ----------
def analyze(content):
    genai.configure(api_key=st.session_state.api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Vytvoř recept ve formátu: NAZEV:, INGREDIENCE:, POSTUP:"
    return model.generate_content([prompt, content]).text

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@700&display=swap');

body,[data-testid="stAppViewContainer"]{
 background:radial-gradient(circle at bottom,#000428,#004e92);
 color:white;
}

.header-icons{
 display:flex;
 gap:6px;
 justify-content:center;
 margin-bottom:4px;
}

.header-icons button{
 width:38px !important;
 height:38px !important;
 padding:0 !important;
 font-size:18px !important;
 border-radius:10px !important;
 background:#0ea5e9 !important;
 color:white !important;
 border:none !important;
}

.title{
 font-family:'Dancing Script',cursive;
 font-size:22px;
 text-align:center;
 color:#7dd3fc;
 margin-bottom:10px;
}

.stExpanderHeader{
 background:#1e3a8a !important;
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
""", unsafe_allow_html=True)

# ---------- HEADER ----------
c = st.container()
with c:
    col = st.columns([1])[0]
    with col:
        st.markdown('<div class="header-icons">', unsafe_allow_html=True)
        if st.button("➕"):
            st.session_state.show_new = not st.session_state.show_new
        if st.button("🔄"):
            save_db()
        if st.button("🔍"):
            st.session_state.show_search = not st.session_state.show_search
        if st.button("🔑"):
            st.session_state.show_api = not st.session_state.show_api
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="title">Márova kuchařka</div>', unsafe_allow_html=True)

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api_key = st.text_input("API klíč", type="password")

# ---------- SEARCH ----------
search = st.text_input("Hledat recept") if st.session_state.show_search else ""

# ---------- NEW ----------
if st.session_state.show_new:
    t1, t2 = st.tabs(["Text", "Foto"])

    with t1:
        with st.form("new_text"):
            title = st.text_input("Název")
            txt = st.text_area("Text")
            if st.form_submit_button("Vytvořit"):
                if txt:
                    st.session_state.recipes.insert(0, {
                        "title": title or "Bez názvu",
                        "text": analyze(txt),
                        "fav": False
                    })
                    save_db()
                    st.rerun()

    with t2:
        img = st.file_uploader("Foto", type=["jpg", "png"])
        title2 = st.text_input("Název foto")
        if img and st.button("Vytvořit z fotky"):
            st.session_state.recipes.insert(0, {
                "title": title2 or "Bez názvu",
                "text": analyze(Image.open(img)),
                "fav": False
            })
            save_db()
            st.rerun()

# ---------- LIST + EDIT ----------
for i, r in enumerate(st.session_state.recipes):
    if search and search.lower() not in r["title"].lower():
        continue

    with st.expander(r["title"]):
        new_title = st.text_input("Název receptu", r["title"], key=f"title_{i}")
        new_text = st.text_area("Text receptu", r["text"], height=220, key=f"text_{i}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Uložit", key=f"save_{i}"):
                r["title"] = new_title
                r["text"] = new_text
                save_db()
                st.rerun()

        with c2:
            if st.button("🗑 Smazat", key=f"del_{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
