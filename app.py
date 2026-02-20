import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import json
import os
import re

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- STAV ----------
if "show_api_input" not in st.session_state: st.session_state.show_api_input = False
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "show_new_recipe" not in st.session_state: st.session_state.show_new_recipe = False
if "show_search" not in st.session_state: st.session_state.show_search = False
if "recipes" not in st.session_state: st.session_state.recipes = []

# ---------- FUNKCE ----------
def analyze(content):
    try:
        genai.configure(api_key=st.session_state.api_key)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        model_name = next((m for m in models if "flash" in m.lower()), models[0])
        model = genai.GenerativeModel(model_name)
        prompt = "Jsi expert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
        res = model.generate_content([prompt, content])
        return res.text
    except Exception as e:
        return f"CHYBA AI: {e}"

def save_local(data):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_local():
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    return []

def load_recipes():
    recipes = []
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            recipes = [
                {"title": x.get("nazev","").strip() or "Bez názvu",
                 "text": x.get("text","").strip(),
                 "fav": str(x.get("fav","")).lower()=="true",
                 "img": x.get("img","")}
                for x in r.json()
            ]
    except:
        pass
    if not recipes:
        recipes = load_local()
        for r in recipes:
            if not r.get("title") or r["title"].strip() == "": r["title"] = "Bez názvu"
            if "img" not in r: r["img"]=""
    return recipes

def db_save():
    for r in st.session_state.recipes:
        if not r.get("title") or r["title"].strip() == "": r["title"] = "Bez názvu"
    try:
        requests.delete(SDB_URL + "/all", timeout=3)
        requests.post(SDB_URL, json=[{"text": r["text"],"fav":"true" if r["fav"] else "false",
                                     "nazev": r["title"],"img": r.get("img","")}
                                    for r in st.session_state.recipes], timeout=3)
    except:
        pass
    save_local(st.session_state.recipes)

def scale_recipe(text):
    return re.sub(r"\d+(\.\d+)?", lambda m: str(round(float(m.group()))), text)

if not st.session_state.recipes: st.session_state.recipes = load_recipes()

# ---------- CSS ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap');
body, [data-testid="stAppViewContainer"] {background: radial-gradient(ellipse at bottom, #000428 0%, #004e92 100%); color: #ffffff;}
h1.app-title {font-family: 'Dancing Script', cursive; font-size:20px; color:#00ccff; font-weight:700; margin:0px;}
div.icon-row {display:flex; flex-direction:row; justify-content:flex-start; gap:3px; margin-bottom:5px; flex-wrap:nowrap;}
div.icon-row button {height:35px; font-size:18px; background:#0099ff; color:white; border-radius:8px; padding:0 6px;}
.stExpanderHeader {background:#1E3A8A !important; border-radius:8px; padding:5px; color:#ffffff !important;}
.stExpanderContent {background:#cce0ff !important; border-radius:8px; padding:10px; color:#000000;}
label, .stTextInput label, .stNumberInput label {color:#ffffff !important; font-weight:700;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea {color:#000000;}
</style>
""", unsafe_allow_html=True)

# ---------- IKONY NAHORU JEDEN RADEK ----------
st.markdown("""
<div class="icon-row">
    <button onclick="document.querySelector('#plus').click()">➕</button>
    <button onclick="document.querySelector('#sync').click()">🔄</button>
    <button onclick="document.querySelector('#search').click()">🔍</button>
    <button onclick="document.querySelector('#key').click()">🔑</button>
</div>
""", unsafe_allow_html=True)

if st.button("plus", key="plus"): st.session_state.show_new_recipe = not st.session_state.show_new_recipe
if st.button("sync", key="sync"): db_save()
if st.button("search", key="search"): st.session_state.show_search = not st.session_state.show_search
if st.button("key", key="key"): st.session_state.show_api_input = not st.session_state.show_api_input

st.markdown('<h1 class="app-title">Márova kuchařka</h1>', unsafe_allow_html=True)

if st.session_state.show_api_input:
    st.session_state.api_key = st.text_input("API klíč (jednou na spuštění)", type="password")

search = st.text_input("Hledat recept") if st.session_state.show_search else ""

# ---------- NOVÝ RECEPT (SCHOVANÝ) ----------
if st.session_state.show_new_recipe:
    t1, t2 = st.tabs(["Text", "Foto"])
    with t1:
        with st.form("t_form", clear_on_submit=True):
            u = st.text_area("Vložit text:")
            title = st.text_input("Název receptu")
            if st.form_submit_button("Čimilali"):
                if u:
                    r_t = analyze(u)
                    st.session_state.recipes.insert(0, {"title": title or "Bez názvu", "text": r_t, "fav": False, "img": ""})
                    db_save()
                    st.experimental_rerun()
    with t2:
        f = st.file_uploader("Foto", type=["jpg","png"])
        title2 = st.text_input("Název receptu (foto)")
        if f and st.button("Čimilali", key="c2"):
            r_t = analyze(Image.open(f))
            st.session_state.recipes.insert(0, {"title": title2 or "Bez názvu", "text": r_t, "fav": False, "img": ""})
            db_save()
            st.experimental_rerun()

# ---------- ZOBRAZENÍ RECEPTŮ ----------
for i, r in enumerate(st.session_state.recipes):
    with st.expander(f"{r['title']}"):
        st.write(r["text"])
        if st.button("Smazat", key=f"d_{i}"):
            st.session_state.recipes.pop(i)
            db_save()
            st.experimental_rerun()
