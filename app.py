import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import json
import os
from io import BytesIO
import re

st.set_page_config(page_title="Moje Recepty", page_icon="🍳", layout="centered")

SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"
LOCAL_FILE = "recipes.json"

# ---------- AI ----------
def analyze(content, api_key):
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        model_name = next((m for m in models if "flash" in m.lower()), models[0])
        model = genai.GenerativeModel(model_name)
        prompt = "Jsi expert na vareni. Format: NAZEV: [Nazev], PORCE: [pocet], INGREDIENCE: - 100 g cukr, POSTUP: 1. [Krok]"
        res = model.generate_content([prompt, content])
        return res.text
    except Exception as e:
        return f"CHYBA AI: {e}"

# ---------- LOCAL ----------
def save_local(data):
    with open(LOCAL_FILE, "w", encoding="utf8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_local():
    if os.path.exists(LOCAL_FILE):
        with open(LOCAL_FILE, "r", encoding="utf8") as f:
            return json.load(f)
    return []

# ---------- LOAD ----------
def load_recipes():
    recipes = []
    # nejprve z cloudu
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            recipes = [
                {
                    "title": x.get("title", "").strip() or "Bez názvu",
                    "text": x.get("text", "").strip(),
                    "fav": str(x.get("fav", "")).lower() == "true"
                }
                for x in r.json()
            ]
    except:
        pass
    # fallback do local
    if not recipes:
        recipes = load_local()
        # zajistíme, že všechny mají title
        for r in recipes:
            if not r.get("title"):
                r["title"] = "Bez názvu"
    return recipes

if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()

# ---------- SAVE ----------
def db_save():
    # u všech receptů zajistíme title
    for r in st.session_state.recipes:
        if not r.get("title"):
            r["title"] = "Bez názvu"
    try:
        requests.delete(SDB_URL + "/all", timeout=3)
        requests.post(
            SDB_URL,
            json=[{"title": r["title"], "text": r["text"], "fav": "true" if r["fav"] else "false"} for r in st.session_state.recipes],
            timeout=3,
        )
    except:
        pass
    save_local(st.session_state.recipes)

# ---------- SYNC ----------
def sync_online():
    try:
        requests.delete(SDB_URL + "/all", timeout=3)
        requests.post(
            SDB_URL,
            json=[{"title": r["title"], "text": r["text"], "fav": "true" if r["fav"] else "false"} for r in st.session_state.recipes],
            timeout=3,
        )
        st.success("Synchronizováno s cloudem ✅")
    except:
        st.error("Nelze se připojit k internetu")

# ---------- SCALE ----------
def scale_recipe(text, factor):
    def repl(match):
        num = float(match.group())
        return str(round(num * factor, 2))
    return re.sub(r"\d+(\.\d+)?", repl, text)

# ---------- PDF ----------
def export_pdf():
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Moje kuchařka", styles["Title"]), Spacer(1, 20)]
        for r in st.session_state.recipes:
            elements.append(Paragraph(r["title"], styles["Heading2"]))
            elements.append(Preformatted(r["text"], styles["Code"]))
            elements.append(Spacer(1, 15))
        doc.build(elements)
        buffer.seek(0)
        return buffer
    except:
        return None

# ---------- UI ----------
st.title("🍳 Můj chytrý receptář")

search = st.text_input("🔎 Hledat recept")
colA, colB = st.columns([3, 1])
with colB:
    if st.button("🔄 Synchronizovat"):
        sync_online()

api = st.sidebar.text_input("API klíč", type="password")

if api:
    tab1, tab2 = st.tabs(["Text", "Foto"])

    # ---------- TEXT ----------
    with tab1:
        title_input = st.text_input("Název receptu")
        text_input = st.text_area("Vložit text")
        submit_text = st.button("Čimilali")
        if submit_text:
            if text_input.strip():
                # Vždy vezme aktuální vstup z formuláře
                generated_text = analyze(text_input.strip(), api)
                st.session_state.recipes.insert(0, {
                    "title": title_input.strip() or "Bez názvu",
                    "text": generated_text,
                    "fav": False
                })
                db_save()

    # ---------- FOTO ----------
    with tab2:
        f = st.file_uploader("Foto", type=["jpg", "png"])
        title_input_photo = st.text_input("Název receptu (pro foto)")
        submit_photo = st.button("Čimilali foto")
        if f and submit_photo:
            generated_text = analyze(Image.open(f), api)
            st.session_state.recipes.insert(0, {
                "title": title_input_photo.strip() or "Bez názvu",
                "text": generated_text,
                "fav": False
            })
            db_save()

# ---------- LIST ----------
for i, r in enumerate(list(st.session_state.recipes)):
    if search and search.lower() not in r["text"].lower() and search.lower() not in r["title"].lower():
        continue

    with st.expander(f"{'⭐ ' if r['fav'] else ''}{r['title']}"):
        factor = st.number_input("Násobek porcí", 0.1, 10.0, 1.0, 0.1, key=f"scale{i}")
        scaled = scale_recipe(r["text"], factor)

        title_edit = st.text_input("Název", r["title"], key=f"title{i}")
        edited = st.text_area("Text", scaled, key=f"edit{i}", height=200)

        c1, c2, c3 = st.columns(3)
        if c1.button("💾 Uložit", key=f"s{i}"):
            st.session_state.recipes[i]["title"] = title_edit
            st.session_state.recipes[i]["text"] = edited
            db_save()

        if c2.button("⭐ Oblíbený", key=f"f{i}"):
            st.session_state.recipes[i]["fav"] = not st.session_state.recipes[i]["fav"]
            db_save()

        if c3.button("🗑 Smazat", key=f"d{i}"):
            st.session_state.recipes.pop(i)
            db_save()

# ---------- EXPORT ----------
st.divider()
if st.button("📄 Export PDF"):
    pdf = export_pdf()
    if pdf:
        st.download_button("Stáhnout PDF", pdf, "kucharka.pdf")
    else:
        st.error("Nejdřív nainstaluj knihovnu: pip install reportlab")
