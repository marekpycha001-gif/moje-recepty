import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import json
import os
from io import BytesIO
import re
import base64

# -------- CONFIG --------
st.set_page_config(page_title="Márova kuchařka", page_icon="🍳", layout="wide")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# -------- API KLÍČ --------
if "show_api_input" not in st.session_state:
    st.session_state.show_api_input = False
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# -------- AI --------
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

# -------- LOCAL STORAGE --------
def save_local(data):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_local():
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    return []

# -------- LOAD RECIPES --------
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

# -------- SAVE --------
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

# -------- SCALE --------
def scale_recipe(text, factor):
    def repl(match):
        num = float(match.group())
        return str(round(num))
    return re.sub(r"\d+(\.\d+)?", repl, text)

# -------- PDF EXPORT --------
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

# -------- CSS PRO STYL --------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@400;700&display=swap');
body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(ellipse at bottom, #000428 0%, #004e92 100%);
    color: #ffffff;
}
h1 {font-family: 'Dancing Script', cursive; font-size:14px; color:#00ccff; font-weight:700; margin:0px; display:inline;}
div.stButton > button {height:35px; font-size:16px; background:#0099ff; color:white; border-radius:8px; margin:1px;}
textarea, input[type=text], input[type=number] {font-size:16px; padding:5px; color:#000;}
.stExpanderHeader {background:#1E3A8A !important; border-radius:8px; padding:5px; color:#ffffff !important;}
.stExpanderContent {background:#cce0ff !important; border-radius:8px; padding:10px; color:#000000;}
label, .stTextInput label, .stNumberInput label {color:#ffffff !important; font-weight:700;}
.stTextInput>div>div>input, .stNumberInput>div>div>input, textarea {color:#000000;}
</style>
""", unsafe_allow_html=True)

# -------- HORNÍ IKONKY UPLNĚ NAHORU --------
cols = st.columns([0.5,0.5,0.5,0.5])
with cols[0]:
    if st.button("➕"):
        st.session_state.show_new_recipe = not st.session_state.get("show_new_recipe", False)
with cols[1]:
    if st.button("🔄"):
        db_save()
        st.success("Synchronizováno ✅")
with cols[2]:
    if st.button("🔍"):
        st.session_state.show_search = not st.session_state.get("show_search", False)
with cols[3]:
    if st.button("🔑"):
        st.session_state.show_api_input = not st.session_state.show_api_input

if st.session_state.show_api_input:
    st.session_state.api_key = st.text_input("API klíč (jednou na spuštění)", type="password")

# -------- NADPIS A PODPŮRNÉ ELEMENTY --------
st.markdown("<h1 style='margin-top:5px;'>Márova kuchařka</h1>", unsafe_allow_html=True)

if "show_search" not in st.session_state:
    st.session_state.show_search = False
search = st.text_input("Hledat recept") if st.session_state.show_search else ""

# -------- NOVÝ RECEPT --------
if st.session_state.api_key and st.session_state.get("show_new_recipe", False):
    tab1, tab2 = st.tabs(["Text", "Foto"])
    with tab1:
        if "new_title_text" not in st.session_state:
            st.session_state.new_title_text = ""
        st.session_state.new_title_text = st.text_input("Název receptu", value=st.session_state.new_title_text)
        new_text = st.text_area("Vložit text", height=200)
        if st.button("Čimilali"):
            if new_text.strip():
                generated = analyze(new_text.strip())
                title_final = st.session_state.new_title_text.strip() or "Bez názvu"
                st.session_state.recipes.insert(0, {"title": title_final, "text": generated, "fav": False, "img": ""})
                db_save()
                st.session_state.new_title_text = ""

    with tab2:
        if "new_title_photo" not in st.session_state:
            st.session_state.new_title_photo = ""
        st.session_state.new_title_photo = st.text_input("Název receptu (pro foto)", value=st.session_state.new_title_photo)
        f = st.file_uploader("Foto", type=["jpg", "png"])
        if f and st.button("Čimilali foto"):
            generated = analyze(Image.open(f))
            buffered = BytesIO()
            Image.open(f).save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            title_final = st.session_state.new_title_photo.strip() or "Bez názvu"
            st.session_state.recipes.insert(0, {"title": title_final, "text": generated, "fav": False, "img": img_base64})
            db_save()
            st.session_state.new_title_photo = ""

# -------- LIST RECIPES --------
for i, r in enumerate(list(st.session_state.recipes)):
    if search and search.lower() not in r["text"].lower() and search.lower() not in r["title"].lower():
        continue

    header = f"{'⭐ ' if r['fav'] else ''}{r['title']}"
    with st.expander(header):
        factor = st.number_input("Násobek porcí", 0.1, 10.0, 1.0, 0.1, key=f"scale{i}")
        scaled = re.sub(r"\d+(\.\d+)?", lambda m: str(round(float(m.group()))), r["text"])

        title_edit = st.text_input("Název", r["title"], key=f"title{i}")
        edited = st.text_area("Text", scaled, key=f"edit{i}", height=200)

        c1, c2, c3 = st.columns([1,1,1])
        if c1.button("💾 Uložit", key=f"s{i}"):
            st.session_state.recipes[i]["title"] = title_edit.strip() or "Bez názvu"
            st.session_state.recipes[i]["text"] = edited
            db_save()

        if c2.button("⭐ Oblíbený", key=f"f{i}"):
            st.session_state.recipes[i]["fav"] = not st.session_state.recipes[i]["fav"]
            db_save()

        if c3.button("🗑 Smazat", key=f"d{i}"):
            st.session_state.recipes.pop(i)
            db_save()

# -------- EXPORT PDF --------
st.divider()
if st.button("📄 Export PDF"):
    pdf = export_pdf()
    if pdf:
        st.download_button("Stáhnout PDF", pdf, "kucharka.pdf")
    else:
        st.error("Nejdřív nainstaluj knihovnu: pip install reportlab")
