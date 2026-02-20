import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests, json, os, re

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- SESSION ----------
defaults = {
    "api": "",
    "recipes": [],
    "show_new": False,
    "show_search": False,
    "show_api": False
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- AI ----------
def ai(txt):
    try:
        genai.configure(api_key=st.session_state.api)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
Z textu vytvoř recept a vrať formát:

Čas: XX min
Kalorie: XXX kcal

POSTUP:
recept

TEXT:
{txt}
"""
        out = model.generate_content(prompt).text

        time = re.search(r"Čas:\s*(.*)", out)
        kcal = re.search(r"Kalorie:\s*(.*)", out)

        return {
            "text": out,
            "time": time.group(1) if time else "?",
            "kcal": kcal.group(1) if kcal else "?"
        }
    except Exception as e:
        return {"text": f"AI chyba: {e}", "time": "?", "kcal": "?"}

# ---------- STORAGE ----------
def load_local():
    if os.path.exists(LOCAL_FILE):
        return json.load(open(LOCAL_FILE, encoding="utf8"))
    return []

def save_local(d):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def load_db():
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            return [{
                "title": x.get("nazev","Bez názvu"),
                "text": x.get("text",""),
                "time": x.get("time","?"),
                "kcal": x.get("kcal","?"),
                "fav": str(x.get("fav","")).lower()=="true"
            } for x in r.json()]
    except: pass
    return load_local()

def save_db():
    try:
        data = [{
            "nazev": r["title"],
            "text": r["text"],
            "time": r["time"],
            "kcal": r["kcal"],
            "fav": "true" if r["fav"] else "false"
        } for r in st.session_state.recipes]

        requests.post(SDB_URL, json=data, timeout=3)
    except: pass

    save_local(st.session_state.recipes)

if not st.session_state.recipes:
    st.session_state.recipes = load_db()

# ---------- TOP MENU ----------
clicked = st.query_params.get("btn","")

st.markdown("""
<div style="display:flex;justify-content:center;gap:6px">
<a href="?btn=new"><button>➕</button></a>
<a href="?btn=sync"><button>🔄</button></a>
<a href="?btn=search"><button>🔍</button></a>
<a href="?btn=api"><button>🔑</button></a>
</div>
""", unsafe_allow_html=True)

if clicked == "new":
    st.session_state.show_new = not st.session_state.show_new
if clicked == "search":
    st.session_state.show_search = not st.session_state.show_search
if clicked == "api":
    st.session_state.show_api = not st.session_state.show_api
if clicked == "sync":
    save_db()

st.markdown("## 🍳 Márova kuchařka")

# ---------- API ----------
if st.session_state.show_api:
    st.session_state.api = st.text_input("API klíč", type="password")

# ---------- SEARCH ----------
search = ""
if st.session_state.show_search:
    search = st.text_input("Hledat recept")

# ---------- NEW ----------
if st.session_state.show_new:

    tab1, tab2 = st.tabs(["Text","Foto"])

    with tab1:
        with st.form("add"):
            txt = st.text_area("Text")
            title = st.text_input("Název")

            if st.form_submit_button("Uložit"):
                if txt:
                    data = ai(txt)
                    st.session_state.recipes.insert(0,{
                        "title": title or "Bez názvu",
                        "text": data["text"],
                        "time": data["time"],
                        "kcal": data["kcal"],
                        "fav": False
                    })
                    save_db()
                    st.rerun()

    with tab2:
        img = st.file_uploader("Foto", type=["jpg","png"])
        title2 = st.text_input("Název foto")

        if img and st.button("Uložit foto"):
            data = ai(Image.open(img))
            st.session_state.recipes.insert(0,{
                "title": title2 or "Bez názvu",
                "text": data["text"],
                "time": data["time"],
                "kcal": data["kcal"],
                "fav": False
            })
            save_db()
            st.rerun()

# ---------- LIST ----------
for i, r in enumerate(st.session_state.recipes):

    if search and search.lower() not in r["title"].lower():
        continue

    with st.expander(f"{r['title']} ⏱ {r['time']} 🔥 {r['kcal']}"):

        nt = st.text_input("Název", r["title"], key=f"t{i}")
        tx = st.text_area("Text", r["text"], key=f"x{i}", height=250)
        tm = st.text_input("Čas", r["time"], key=f"time{i}")
        kc = st.text_input("Kalorie", r["kcal"], key=f"kcal{i}")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("💾 Uložit", key=f"s{i}"):
                st.session_state.recipes[i]["title"]=nt
                st.session_state.recipes[i]["text"]=tx
                st.session_state.recipes[i]["time"]=tm
                st.session_state.recipes[i]["kcal"]=kc
                save_db()
                st.rerun()

        with c2:
            if st.button("🗑 Smazat", key=f"d{i}"):
                st.session_state.recipes.pop(i)
                save_db()
                st.rerun()
