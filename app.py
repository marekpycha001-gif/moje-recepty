import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")
SDB_URL = ""

if "recipes" not in st.session_state:
   try:
      r = requests.get(SDB_URL, timeout=5)
      if r.status_code == 200:
         st.session_state.recipes = [{"te t":  .get("te t", ""), "fav": str( .get("fav", "")).lower() == "true"} for   in r.json()]
      else:
         st.session_state.recipes = []
   e cept:
      st.session_state.recipes = []

if "editing_inde " not in st.session_state:
   st.session_state.editing_inde  = None

def db_save():
   try:
      requests.delete(SDB_URL + "/all")
      if st.session_state.recipes:
         data = [{"te t": r["te t"], "fav": str(r["fav"]).lower()} for r in st.session_state.recipes]
         requests.post(SDB_URL, json={"data": data})
   e cept E ception as e:
      st.error(f"Chyba pri zapisu: {e}")

def analyze(content, api_key):
   try:
      genai.configure(api_key=api_key)
      model = genai.GenerativeModel("gemini-1.5-flash")
      p = "Jsi e pert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
      with st.spinner("Cimilali maka..."):
         res = model.generate_content([p, content])
         return res.te t
   e cept E ception as e:
      return str(e)

st.title("🍳 Muj chytry receptar")

st.sidebar.header("Nastaveni")
if st.sidebar.button("Zkouska spojeni"):
   try:
      test_r = requests.get(SDB_URL + "/keys")
      st.sidebar.info(f"Odezva: {test_r.status_code}")
      st.sidebar.info(f"Sloupce: {test_r.te t}")
   e cept E ception as e:
      st.sidebar.error(f"Chyba: {e}")

api = st.sidebar.te t_input("Vlozit API klic", type="password")

if api:
   t1, t2 = st.tabs(["Te t", "Foto"])
   with t1:
      with st.form("t_form", clear_on_submit=True):
         u = st.te t_area("Vlozit te t:")
         if st.form_submit_button("Cimilali"):
            if u:
               r_t = analyze(u, api)
               st.session_state.recipes.insert(0, {"te t": r_t, "fav": False})
               db_save()
               st.rerun()
   with t2:
      f = st.file_uploader("Foto", type=["jpg", "png"])
      if f and st.button("Cimilali", key="c2"):
         r_t = analyze(Image.open(f), api)
         st.session_state.recipes.insert(0, {"te t": r_t, "fav": False})
         db_save()
         st.rerun()
else:
   st.info("Vloz klic v menu.")

for i, r in enumerate(st.session_state.recipes):
   if st.session_state.editing_inde  == i:
      nt = st.te t_area("Editace", r["te t"], height=300, key=f"e_{i}")
      c1, c2 = st.columns(2)
      if c1.button("Ulozit", key=f"s_{i}"):
         st.session_state.recipes[i]["te t"] = nt
         st.session_state.editing_inde  = None
         db_save()
         st.rerun()
      if c2.button("Zrusit", key=f"a_{i}"):
         st.session_state.editing_inde  = None
         st.rerun()
   else:
      n = "Recept"
      lines = str(r["te t"]).splitlines()
      for l in lines:
         if "NAZEV:" in l.upper():
            n = l.split(":", 1)[1]
            break
      ikona = "❤️" if r.get("fav") else "🤍"
      with st.e pander(f"{ikona} {n}"):
         st.markdown(r["te t"])
         b1, b2, b3 = st.columns(3)
         if b1.button("Oblibene", key=f"f_{i}"):
            st.session_state.recipes[i]["fav"] = not r.get("fav")
            db_save()
            st.rerun()
         if b2.button("Edit", key=f"ed_{i}"):
            st.session_state.editing_inde  = i
            st.rerun()
         if b3.button("Smazat", key=f"d_{i}"):
            st.session_state.recipes.pop(i)
            db_save()
            st.rerun()
