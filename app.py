import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- NASTAVENÍ ---
st.set_page_config(page_title="Moje Recepty", page_icon="🍳", layout="centered")

# Zde si aplikace bude pamatovat recepty (v rámci jednoho spuštění)
if 'recipes' not in st.session_state:
    st.session_state.recipes = []

# --- FUNKCE PRO AI ---
def analyze_recipe(content, content_type, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Jsi můj osobní kuchař. Tvým úkolem je extrahovat recept z přiloženého textu nebo obrázku.
        1. Pokud jsou ingredience v hrníčkách/lžících, PŘEPOČÍTEJ JE NA GRAMY/MILILITRY (odhadem).
        2. Rozhodni, jestli je recept: "Sladké", "Slané" nebo "Ostatní".
        3. Výstup naformátuj přesně takto (nic jiného nepiš):
        
        NÁZEV: [Sem napiš název receptu]
        KATEGORIE: [Sladké/Slané/Ostatní]
        INGREDIENCE:
        - [Ingredience 1 v gramech]
        - [Ingredience 2 v gramech]
        POSTUP:
        1. [Krok 1]
        2. [Krok 2]
        """

        if content_type == "image":
            response = model.generate_content([prompt, content])
        else:
            response = model.generate_content([prompt, f"Tady je text/odkaz receptu: {content}"])
            
        return response.text
    except Exception as e:
        return f"Chyba: {str(e)}"

# --- VZHLED APLIKACE ---
st.title("🍳 Můj chytrý receptář")

# 1. ČÁST: NASTAVENÍ
with st.expander("⚙️ Nastavení (API Klíč)"):
    api_key = st.text_input("Vlož svůj Google Gemini API klíč", type="password")
    st.caption("Klíč získáš zdarma na aistudio.google.com")

if not api_key:
    st.warning("Pro fungování vlož prosím API klíč v nastavení.")
    st.stop()

# 2. ČÁST: PŘIDÁNÍ RECEPTU
st.header("➕ Přidat nový recept")
tab1, tab2 = st.tabs(["📝 Z textu/URL", "📸 Ze screenshotu"])

with tab1:
    url_text = st.text_area("Vlož odkaz nebo text receptu (FB, web):")
    if st.button("Vysosat recept z textu"):
        with st.spinner("Čtu recept a přepočítávám gramy..."):
            result = analyze_recipe(url_text, "text", api_key)
            st.session_state.recipes.append(result)
            st.success("Recept uložen!")

with tab2:
    uploaded_file = st.file_uploader("Nahraj screenshot receptu", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Nahraný obrázek', use_column_width=True)
        if st.button("Vysosat recept z obrázku"):
            with st.spinner("Dívám se na obrázek a píšu recept..."):
                result = analyze_recipe(image, "image", api_key)
                st.session_state.recipes.append(result)
                st.success("Recept uložen!")

# 3. ČÁST: MOJE KUCHAŘKA
st.markdown("---")
st.header("📚 Uložené recepty")

filter_option = st.radio("Filtrovat:", ["Vše", "Sladké", "Slané"], horizontal=True)
search_query = st.text_input("🔍 Hledat (např. 'mouka', 'bábovka')")

for i, recipe in enumerate(reversed(st.session_state.recipes)):
    # Jednoduchý filtr
    if filter_option != "Vše" and filter_option not in recipe:
        continue
    if search_query and search_query.lower() not in recipe.lower():
        continue
        
    with st.expander(f"Recept #{len(st.session_state.recipes)-i}"):
        st.markdown(recipe)
        if st.button(f"Smazat recept {len(st.session_state.recipes)-i}"):
            st.session_state.recipes.pop(len(st.session_state.recipes)-i-1)
            st.rerun()
