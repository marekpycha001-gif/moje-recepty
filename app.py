import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import json
import os
from io import BytesIO
import re
import base64

st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

if "show_api_input" not in st.session_state:
    st.session_state.show_api_input = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

def analyze(content):
    try:
        genai.configure(api_key=st.session_state.api_key)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        model_name = next((m for m in models if "flash" in m.lower()), models[0])
        model = genai.GenerativeModel(model_name)
        prompt = "Jsi expert na vareni. Format: NAZEV: [Nazev], PORCE: [pocet], INGREDIENCE: - 100 g cukr, POSTUP: 1. [Krok]"
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
                {
                    "title": x.get("nazev", "").strip() or "Bez názvu",
                    "text": x.get("text", "").strip(),
                    "fav": str(x.get("fav", "")).lower() == "true",
                    "img": x.get("img", "")
                }
                for x in r.json()
            ]
    except:
        pass
    if not recipes:
        recipes = load_local()
        for r in recipes:
            if not r.get("title") or r["title"].strip() == "":
                r["title"] = "Bez názvu"
            if "img" not in r:
                r["img"] = ""
    return recipes

if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()

def db_save():
    for r in st.session_state.recipes:
        if not r.get("title") or r["title"].strip() == "":
            r["title"] = "Bez názvu"
    try:
        requests.delete(SDB_URL + "/all", timeout=3)
        requests.post(
            SDB_URL,
            json=[
                {
                    "text": r["text"],
                    "fav": "true" if r["fav"] else "false",
                    "nazev": r["title"],
                    "img": r.get("img", "")
                }
                for r in st.session_state.recipes
            ],
            timeout=3,
        )
    except:
        pass
    save_local(st.session_state.recipes)

def scale_recipe(text, factor):
    def repl(match):
        num = float(match.group())
        return str(round(num))
    return re.sub(r"\d+(\.\d+)?", repl, text)

def export_pdf():
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Márova kuchařka", styles["Title"]), Spacer(1, 20)]
        for r in st.session_state.recipes:
            elements.append(Paragraph(r["title"], styles["Heading2"]))
            elements.append(Preformatted(r["text"], styles["Code"]))
            elements.append(Spacer(1, 15))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    except:
        return None

# -------- CSS PRO STYL A FLEX --------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap');
body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at bottom, #000428 0%, #004e92 100%);
    color: #ffffff;
}
h1.app-title {font-family: 'Dancing Script', cursive; font-size: 20px; color:#00ccff; font-weight:700; margin:0px;}
div.icon-row {display:flex; flex-direction:row; justify-content:flex-start; gap:5px; margin-bottom:5px;}
div.stButton > button {height:35px; font-size:16px; background:#0099ff; color:white; border-radius:8px;}
.stExpanderHeader {background:#1E3A8A !important; border-radius:8px; padding:5px; color:#ffffff !important;}
.stExpanderContent {background:#cce0ff !important; border-radius:8px; padding:10px; color:#000000;}
label, .stTextInput label, .stNumberInput label {color:#ffffff !important; font-weight:700;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea {color:#000000;}
</style>
""", unsafe_allow_html=True)

# -------- IKONY FLEX NAD NADPISEM --------
st.markdown("""
<div class="icon-row">
    <button onclick="document.querySelector('#new_rec').click()">➕</button>
    <button onclick="document.querySelector('#sync').click()">🔄</button>
    <button onclick="document.querySelector('#search_btn').click()">🔍</button>
    <button onclick="document.querySelector('#api_btn').click()">🔑</button>
</div>
""", unsafe_allow_html=True)

# Pomocné "skryté" streamlit tlačítka pro JS onclick
if st.button("hidden new_rec", key="new_rec", help="skrýt") : st.session_state.show_new_recipe = not st.session_state.get("show_new_recipe", False)
if st.button("hidden sync", key="sync", help="skrýt") : db_save()
if st.button("hidden search_btn", key="search_btn", help="skrýt") : st.session_state.show_search = not st.session_state.get("show_search", False)
if st.button("hidden api_btn", key="api_btn", help="skrýt") : st.session_state.show_api_input = not st.session_state.show_api_input

st.markdown('<h1 class="app-title">Márova kuchařka</h1>', unsafe_allow_html=True)

if st.session_state.show_api_input:
    st.session_state.api_key = st.text_input("API klíč (jednou na spuštění)", type="password")

if "show_search" not in st.session_state:
    st.session_state.show_search = False
search = st.text_input("Hledat recept") if st.session_state.show_search else ""

# --- Zbytek kódu pro nové recepty, seznam receptů a export PDF je stejný ---
