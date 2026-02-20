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
    try:
        r = requests.get(SDB_URL, timeout=3)
        if r.status_code == 200:
            recipes = [
                {
                    "title": x.get("nazev", "").strip() or "Bez názvu",
                    "text": x.get("text", "").strip(),
                    "fav": str(x.get("fav", "")).lower() == "true"
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
    return recipes

if "recipes" not in st.session_state:
    st.session_state.recipes = load_recipes()

# ---------- SAVE ----------
def db_save():
    for r in st.session_state.recipes:
        if not r.get("title") or r["title"].strip() == "":
            r["title"] = "Bez názvu"
    try:
        requests.delete(SDB_URL + "/all", timeout=3)
        requests.post(
            SDB_URL,
            json=[{"text": r["text"], "fav": "true" if r["fav"] else "false", "nazev": r["title"]} for r in st.session_state.recipes],
            timeout=3,
        )
    except:
        pass
    save_local(st.session_state.recipes)

# ---------- SCALE ----------
def scale_recipe(text, factor):
    def repl(match):
        num = float(match.group())
        scaled = round(num * factor)
        return str(scaled)
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
        db_save()
        st.success("Synchronizováno ✅")

api = st.sidebar.text_input("API klíč", type="password")

# ---------- CREATE RECIPE ----------
if api:
    tab1, tab2 = st.tabs(["Text", "Foto"])

    # Text
    with tab1:
        if "new_title_text" not in st.session_state:
            st.session_state.new_title_text = ""
        st.session_state.new_title_text = st.text_input("Název receptu", value=st.session_state.new_title_text)
        new_text = st.text_area("Vložit text")
        if st.button("Čimilali"):
            if new_text.strip():
                generated = analyze(new_text.strip(), api)
                title_final = st.session_state.new_title_text.strip() or "Bez názvu"
                st.session_state.recipes.insert(0, {
                    "title": title_final,
                    "text": generated,
                    "fav": False
                })
                db_save()
                st.session_state.new_title_text = ""

    # Foto
    with tab2:
        if "new_title_photo" not in st.session_state:
            st.session_state.new_title_photo = ""
        st.session_state.new_title_photo = st.text_input("Název receptu (pro foto)", value=st.session_state.new_title_photo)
        f = st.file_uploader("Foto", type=["jpg", "png"])
        if f and st.button("Čimilali foto"):
            generated = analyze(Image.open(f), api)
            title_final = st.session_state.new_title_photo.strip() or "Bez názvu"
            st.session_state.recipes.insert(0, {
                "title": title_final,
                "text": generated,
                "fav": False
            })
            db_save()
            st.session_state.new_title_photo = ""

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
            st.session_state.recipes[i]["title"] = title_edit.strip() or "Bez názvu"
            st.session_state.recipes[i]["text"] = edited
            db_save()  # uloží title do sloupce 'nazev'

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
