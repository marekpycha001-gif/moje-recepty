CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Moje Recepty", page_icon="🍳", layout="centered")

if 'recipes' not in st.session_state:
   st.session_state.recipes = []

if 'editing_inde ' not in st.session_state:
   st.session_state.editing_inde  = None

def analyze_recipe(content, content_type, api_key):
   try:
      genai.configure(api_key=api_key)
      model = genai.GenerativeModel('gemini-1.5-flash')
      prompt = "Jsi kuchař a e pert na převody. Všechny objemové míry PŘEPOČÍTEJ NA GRAMY (g). ZOHLEDNI HUSTOTU SUROVIN! (olej je lehčí, med těžší). Kusy nech na kusy. VÝSTUP:\nNÁZEV: [Název]\nKATEGORIE: [Sladké/Slané]\nINGREDIENCE:\n- [g] [surovina]\nPOSTUP:\n1. [Krok]"
      with st.spinner("⏳ Počítám gramáže a píšu recept..."):
         if content_type == "image":
            response = model.generate_content([prompt, content])
         else:
            response = model.generate_content([prompt, f"Zdroj: {content}"])
      return response.te t
   e cept E ception as e:
      return f"Chyba: {str(e)}"

st.title("🍳 Můj chytrý receptář")

with st.e pander("⚙️ Nastavení (Klíč)"):
   api_key = st.te t_input("Vlož Google API klíč", type="password")

if not api_key:
   st.warning("☝️ Pro fungování vlož prosím svůj API klíč.")
   st.stop()

st.write("### ➕ Nový recept")
tab1, tab2 = st.tabs(["📝 Z odkazu/te tu", "📸 Z obrázku"])

with tab1:
   url_input = st.te t_area("Vlož odkaz nebo te t:", height=100)
   if st.button("Vysosat a přepočítat na gramy"):
      if url_input:
         recept = analyze_recipe(url_input, "te t", api_key)
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

for i, recept_te t in enumerate(st.session_state.recipes):
   if st.session_state.editing_inde  == i:
      st.markdown("#### ✏️ Úprava receptu")
      novy_te t = st.te t_area("Upravit te t", value=recept_te t, height=350, key=f"te t_{i}", label_visibility="collapsed")
      col1, col2 = st.columns(2)
      if col1.button("💾 Uložit změny", key=f"save_{i}"):
         st.session_state.recipes[i] = novy_te t
         st.session_state.editing_inde  = None
         st.rerun()
      if col2.button("❌ Zrušit", key=f"cancel_{i}"):
         st.session_state.editing_inde  = None
         st.rerun()
   else:
      nazev = "Recept bez názvu"
      lines = recept_te t.split('\n')
      for line in lines:
         if "NÁZEV:" in line:
            nazev = line.replace("NÁZEV:", "").strip()
            break
      with st.e pander(f"🥘 {nazev}"):
         st.markdown(recept_te t)
         c1, c2 = st.columns([1, 4])
         if c1.button("✏️ Upravit", key=f"edit_btn_{i}"):
            st.session_state.editing_inde  = i
            st.rerun()
         if c2.button("🗑️ Smazat", key=f"del_btn_{i}"):
            st.session_state.recipes.pop(i)
            st.rerun()
