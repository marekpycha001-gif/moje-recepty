import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Moje Recepty", page_icon="🍳", layout="centered")

if 'recipes' not in st.session_state:
    st.session_state.recipes = []

if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

def analyze_recipe(content, content_type, api_key):
try:
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🍳 Můj chytrý receptář")

with st.expander("⚙️ Nastavení (Klíč)"):
api_key = st.text_input("Vlož Google API klíč", type="password")

if not api_key:
st.warning("☝️ Pro fungování vlož prosím svůj API klíč.")
st.stop()

st.write("### ➕ Nový recept")
tab1, tab2 = st.tabs(["📝 Z odkazu/textu", "📸 Z obrázku"])

with tab1:
url_input = st.text_area("Vlož odkaz (Facebook, web) nebo text:", height=100)
if st.button("Vysosat a přepočítat na gramy"):
if url_input:
recept = analyze_recipe(url_input, "text", api_key)
st.session_state.recipes.insert(0, recept)
st.success("Hotovo!")
st.rerun()

with tab2:
img_file = st.file_uploader("Nahraj screenshot", type=["jpg", "png", "jpeg"])
if img_file and st.button("Přečíst z obrázku"):
image = Image.open(img_file)
recept = analyze_recipe(image, "image", api_key)
st.session_state.recipes.insert(0, recept)
st.success("Hotovo!")
st.rerun()

st.markdown("---")
st.write("### 📚 Uložené recepty")

if not st.session_state.recipes:
st.info("Zatím tu nic není. Přidej první recept!")

for i, recept_text in enumerate(st.session_state.recipes):
if st.session_state.editing_index == i:
st.markdown(f"#### ✏️ Úprava receptu")
novy_text = st.text_area("Upravit text", value=recept_text, height=350, key=f"text_{i}", label_visibility="collapsed")
