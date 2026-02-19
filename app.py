CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

if 'recipes' not in st.session_state:
XXXst.session_state.recipes = []

if 'editing_index' not in st.session_state:
XXXst.session_state.editing_index = None

def analyze_recipe(content, content_type, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXprompt = '''Jsi expert na vaření. Všechny objemové míry přepočti na GRAMY (g) a zohledni hustotu surovin (olej/med atd.). Kusy nech na kusy.
Vypiš přesně v tomto formátu:
NÁZEV: [Název]
KATEGORIE: [Sladké/Slané]
INGREDIENCE:

[g] [surovina]
POSTUP:

[Krok]'''
XXXXXXwith st.spinner("⏳ Počítám gramy a píšu recept..."):
XXXXXXXXXtry:
XXXXXXXXXXXX# Nejprve zkusíme nový model
XXXXXXXXXXXXmodel = genai.GenerativeModel('gemini-1.5-flash')
XXXXXXXXXXXXif content_type == "image":
XXXXXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXXXXelse:
XXXXXXXXXXXXXXXresponse = model.generate_content([prompt, f"Zdroj: {content}"])
XXXXXXXXXexcept Exception:
XXXXXXXXXXXX# ZÁCHRANNÁ BRZDA: Pokud nový model není dostupný, použijeme starší, který funguje všude
XXXXXXXXXXXXif content_type == "image":
XXXXXXXXXXXXXXXmodel = genai.GenerativeModel('gemini-pro-vision')
XXXXXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXXXXelse:
XXXXXXXXXXXXXXXmodel = genai.GenerativeModel('gemini-pro')
XXXXXXXXXXXXXXXresponse = model.generate_content([prompt, f"Zdroj: {content}"])
XXXXXXreturn response.text
XXXexcept Exception as e:
XXXXXXreturn f"Chyba: {str(e)}"

st.title("🍳 Můj chytrý receptář")

with st.expander("⚙️ Nastavení (Klíč)"):
XXXapi_key = st.text_input("Vlož Google API klíč", type="password")

if not api_key:
XXXst.warning("☝️ Vlož API klíč pro oživení aplikace.")
XXXst.stop()

tab1, tab2 = st.tabs(["📝 Z textu/odkazu", "📸 Z obrázku"])

with tab1:
XXXurl_input = st.text_area("Vlož odkaz nebo text receptu:")
XXXif st.button("Vysosat a přepočítat"):
XXXXXXif url_input:
XXXXXXXXXrecept = analyze_recipe(url_input, "text", api_key)
XXXXXXXXXst.session_state.recipes.insert(0, recept)
XXXXXXXXXst.rerun()

with tab2:
XXXimg_file = st.file_uploader("Nahraj screenshot", type=["jpg", "png", "jpeg"])
XXXif img_file and st.button("Přečíst z obrázku"):
XXXXXXimage = Image.open(img_file)
XXXXXXrecept = analyze_recipe(image, "image", api_key)
XXXXXXst.session_state.recipes.insert(0, recept)
XXXXXXst.rerun()

st.markdown("---")
st.write("### 📚 Uložené recepty")

for i, recept_text in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXst.markdown("#### ✏️ Úprava")
XXXXXXnovy_text = st.text_area("Upravit text", value=recept_text, height=300, key=f"t_{i}", label_visibility="collapsed")
XXXXXXc1, c2 = st.columns(2)
XXXXXXif c1.button("💾 Uložit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i] = novy_text
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXXXXif c2.button("❌ Zrušit", key=f"c_{i}"):
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXnazev = "Recept bez názvu"
XXXXXXfor line in str(recept_text).splitlines():
XXXXXXXXXif "NÁZEV:" in line:
XXXXXXXXXXXXnazev = line.replace("NÁZEV:", "").strip()
XXXXXXXXXXXXbreak
XXXXXXwith st.expander(f"🥘 {nazev}"):
XXXXXXXXXst.markdown(recept_text)
XXXXXXXXXc1, c2 = st.columns(2)
XXXXXXXXXif c1.button("✏️ Upravit", key=f"e_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c2.button("🗑️ Smazat", key=f"d_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
