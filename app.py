CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Moje Recepty", page_icon="🍳", layout="centered")

if 'recipes' not in st.session_state:
XXXst.session_state.recipes = []

if 'editing_index' not in st.session_state:
XXXst.session_state.editing_index = None

def analyze_recipe(content, content_type, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXmodel = genai.GenerativeModel('gemini-1.5-flash')
XXXXXXprompt = "Jsi kuchař a expert na převody. Všechny objemové míry PŘEPOČÍTEJ NA GRAMY (g). ZOHLEDNI HUSTOTU SUROVIN! (olej je lehčí, med těžší). Kusy nech na kusy. VÝSTUP:\nNÁZEV: [Název]\nKATEGORIE: [Sladké/Slané]\nINGREDIENCE:\n- [g] [surovina]\nPOSTUP:\n1. [Krok]"
XXXXXXwith st.spinner("⏳ Počítám gramáže a píšu recept..."):
XXXXXXXXXif content_type == "image":
XXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXelse:
XXXXXXXXXXXXresponse = model.generate_content([prompt, f"Zdroj: {content}"])
XXXXXXreturn response.text
XXXexcept Exception as e:
XXXXXXreturn f"Chyba: {str(e)}"

st.title("🍳 Můj chytrý receptář")

with st.expander("⚙️ Nastavení (Klíč)"):
XXXapi_key = st.text_input("Vlož Google API klíč", type="password")

if not api_key:
XXXst.warning("☝️ Pro fungování vlož prosím svůj API klíč.")
XXXst.stop()

st.write("### ➕ Nový recept")
tab1, tab2 = st.tabs(["📝 Z odkazu/textu", "📸 Z obrázku"])

with tab1:
XXXurl_input = st.text_area("Vlož odkaz nebo text:", height=100)
XXXif st.button("Vysosat a přepočítat na gramy"):
XXXXXXif url_input:
XXXXXXXXXrecept = analyze_recipe(url_input, "text", api_key)
XXXXXXXXXst.session_state.recipes.insert(0, recept)
XXXXXXXXXst.success("Hotovo!")
XXXXXXXXXst.rerun()

with tab2:
XXXimg_file = st.file_uploader("Nahraj screenshot", type=["jpg", "png", "jpeg"])
XXXif img_file and st.button("Přečíst z obrázku"):
XXXXXXimage = Image.open(img_file)
XXXXXXrecept = analyze_recipe(image, "image", api_key)
XXXXXXst.session_state.recipes.insert(0, recept)
XXXXXXst.success("Hotovo!")
XXXXXXst.rerun()

st.markdown("---")
st.write("### 📚 Uložené recepty")

if not st.session_state.recipes:
XXXst.info("Zatím tu nic není. Přidej první recept!")

for i, recept_text in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXst.markdown("#### ✏️ Úprava receptu")
XXXXXXnovy_text = st.text_area("Upravit text", value=recept_text, height=350, key=f"text_{i}", label_visibility="collapsed")
XXXXXXcol1, col2 = st.columns(2)
XXXXXXif col1.button("💾 Uložit změny", key=f"save_{i}"):
XXXXXXXXXst.session_state.recipes[i] = novy_text
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXXXXif col2.button("❌ Zrušit", key=f"cancel_{i}"):
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXnazev = "Recept bez názvu"
XXXXXXlines = recept_text.split('\n')
XXXXXXfor line in lines:
XXXXXXXXXif "NÁZEV:" in line:
XXXXXXXXXXXXnazev = line.replace("NÁZEV:", "").strip()
XXXXXXXXXXXXbreak
XXXXXXwith st.expander(f"🥘 {nazev}"):
XXXXXXXXXst.markdown(recept_text)
XXXXXXXXXc1, c2 = st.columns([1, 4])
XXXXXXXXXif c1.button("✏️ Upravit", key=f"edit_btn_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c2.button("🗑️ Smazat", key=f"del_btn_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
