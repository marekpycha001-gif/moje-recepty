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
XXXXXXvalid_models = []
XXXXXXfor m in genai.list_models():
XXXXXXXXXif 'generateContent' in m.supported_generation_methods:
XXXXXXXXXXXXvalid_models.append(m.name)
XXXXXXif not valid_models:
XXXXXXXXXreturn "Chyba: Tvůj klíč nemá povolený žádný mozek."
XXXXXX
XXXXXXmodel_name = valid_models[0]
XXXXXXfor m in valid_models:
XXXXXXXXXif 'flash' in m:
XXXXXXXXXXXXmodel_name = m
XXXXXXXXXXXXbreak
XXXXXX
XXXXXXmodel = genai.GenerativeModel(model_name)
XXXXXX
XXXXXX# UPRAVENÝ ROZKAZ: Zákaz kopírování, nutnost přepsat vlastními slovy
XXXXXXprompt = '''Jsi expert na vaření. Všechny objemové míry přepočti na GRAMY (g) a zohledni hustotu surovin. Kusy nech na kusy.
DŮLEŽITÉ: Nekopíruj původní text slovo od slova! Napiš postup svými vlastními slovy jako úplně nový originální text, abys neporušil autorská práva.
Vypiš přesně v tomto formátu:
NÁZEV: [Název]
KATEGORIE: [Sladké/Slané]
INGREDIENCE:

[g] [surovina]
POSTUP:

[Krok]'''
XXXXXX
XXXXXXwith st.spinner(f"⏳ Počítám gramy (používám {model_name})..."):
XXXXXXXXXif content_type == "image":
XXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXelse:
XXXXXXXXXXXXresponse = model.generate_content([prompt, f"Zdroj: {content}"])
XXXXXXXXX
XXXXXXXXX# Ochrana proti pádu aplikace kvůli autorským právům
XXXXXXXXXtry:
XXXXXXXXXXXXreturn response.text
XXXXXXXXXexcept ValueError:
XXXXXXXXXXXXif response.candidates and response.candidates[0].finish_reason == 4:
XXXXXXXXXXXXXXXreturn "Chyba z obrázku: Ochrana autorských práv! AI odmítla text přečíst, protože je chráněný. Vlož ho raději jako text."
XXXXXXXXXXXXelse:
XXXXXXXXXXXXXXXreturn "Chyba AI: Odpověď byla zablokována z bezpečnostních důvodů."
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
