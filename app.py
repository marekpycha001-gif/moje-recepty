import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

# TVOJE SHEETDB API URL
SDB_URL = "https://sheetdb.io/api/v1/5ygnspqc90f9d"


def analyze(content, api_key):
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
        m_name = next((m for m in models if "flash" in m), models[0])
        model = genai.GenerativeModel(m_name)

        prompt = "Jsi expert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
        res = model.generate_content([prompt, content])
        return res.text

    except Exception as e:
        return str(e)


# Načtení receptů z databáze při startu
if "recipes" not in st.session_state:
    try:
        r = requests.get(SDB_URL, timeout=5)
        if r.status_code == 200:
            st.session_state.recipes = [
                {
                    "text": x.get("text", ""),
                    "fav": str(x.get("fav", "")).lower() == "true"
                }
                for x in r.json()
            ]
        else:
            st.session_state.recipes = []
    except:
        st.session_state.recipes = []


# Uložení do databáze
def db_save():
    try:
        st.toast("Ukládám...")
        if st.session_state.recipes:
            data = [
                {"text": r["text"], "fav": "true" if r["fav"] else "false"}
                for r in st.session_state.recipes
            ]

            res = requests.post(SDB_URL, json=data)

            if res.status_code in (200, 201):
                st.toast("Uloženo ✅")
            else:
                st.error(res.text)

    except Exception as e:
        st.error(f"Chyba spojení: {e}")


st.title("🍳 Můj chytrý receptář")

# TEST tlačítko
if st.sidebar.button("🚨 NATVRDO ULOŽIT TEST"):
    st.session_state.recipes.insert(0, {"text": "NAZEV: Test", "fav": True})
    db_save()
    st.rerun()


# API klíč
api = st.sidebar.text_input("API klíč", type="password")

if api:

    tab1, tab2 = st.tabs(["Text", "Foto"])

    # TEXT INPUT
    with tab1:
        with st.form("t_form", clear_on_submit=True):
            u = st.text_area("Vložit text:")

            if st.form_submit_button("Vytvořit recept"):
                if u:
                    r_t = analyze(u, api)
                    st.session_state.recipes.insert(0, {"text": r_t, "fav": False})
                    db_save()
                    st.rerun()

    # FOTO INPUT
    with tab2:
        f = st.file_uploader("Foto", type=["jpg", "png"])

        if f and st.button("Vytvořit recept", key="c2"):
            r_t = analyze(Image.open(f), api)
            st.session_state.recipes.insert(0, {"text": r_t, "fav": False})
            db_save()
            st.rerun()


# Výpis receptů
for i, r in enumerate(st.session_state.recipes):
    with st.expander(f"Recept {i+1}"):
        st.write(r["text"])

        if st.button("Smazat", key=f"d_{i}"):
            st.session_state.recipes.pop(i)
            db_save()
            st.rerun()
