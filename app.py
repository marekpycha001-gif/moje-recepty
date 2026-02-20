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
st.session_state.recipes = [{"text": x.get("text", ""), "fav": str(x.get("fav", "")).lower() == "true"} for x in r.json()]
else:
st.session_state.recipes = []
except:
st.session_state.recipes = []

if "editing_index" not in st.session_state:
st.session_state.editing_index = None

def db_save():
try:
requests.delete(SDB_URL + "/all")
if st.session_state.recipes:
data = [{"text": r["text"], "fav": str(r["fav"]).lower()} for r in st.session_state.recipes]
requests.post(SDB_URL, json={"data": data})
except Exception as e:
st.error(f"Chyba pri zapisu: {e}")

def analyze(content, api_key):
try:
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
p = "Jsi expert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
with st.spinner("Cimilali maka..."):
res = model.generate_content([p, content])
return res.text
except Exception as e:
return str(e)

st.title("🍳 Muj chytry receptar")

st.sidebar.header("Nastaveni")
if st.sidebar.button("Zkouska spojeni"):
try:
test_r = requests.get(SDB_URL)
st.sidebar.info(f"Odezva: {test_r.status_code}")
st.sidebar.info(f"Data: {test_r.text}")
except Exception as e:
st.sidebar.error(f"Chyba: {e}")

api = st.sidebar.text_input("Vlozit API klic", type="password")

if api:
t1, t2 = st.tabs(["Text", "Foto"])
with t1:
with st.form("t_form", clear_on_submit=True):
u = st.text_area("Vlozit text:")
if st.form_submit_button("Cimilali"):
if u:
r_t = analyze(u, api)
st.session_state.recipes.insert(0, {"text": r_t, "fav": False})
db_save()
st.rerun()
with t2:
f = st.file_uploader("Foto", type=["jpg", "png"])
if f and st.button("Cimilali", key="c2"):
r_t = analyze(Image.open(f), api)
st.session_state.recipes.insert(0, {"text": r_t, "fav": False})
db_save()
st.rerun()
else:
st.info("Vloz klic v menu.")

for i, r in enumerate(st.session_state.recipes):
if st.session_state.editing_index == i:
nt = st.text_area("Editace", r["text"], height=300, key=f"e_{i}")
c1, c2 = st.columns(2)
if c1.button("Ulozit", key=f"s_{i}"):
st.session_state.recipes[i]["text"] = nt
st.session_state.editing_index = None
db_save()
st.rerun()
if c2.button("Zrusit", key=f"a_{i}"):
st.session_state.editing_index = None
st.rerun()
else:
n = "Recept"
lines = str(r["text"]).splitlines()
for l in lines:
if "NAZEV:" in l.upper():
n = l.split(":", 1)[1]
break
ikona = "❤️" if r.get("fav") else "🤍"
with st.expander(f"{ikona} {n}"):
st.markdown(r["text"])
b1, b2, b3 = st.columns(3)
if b1.button("Oblibene", key=f"f_{i}"):
st.session_state.recipes[i]["fav"] = not r.get("fav")
db_save()
st.rerun()
if b2.button("Edit", key=f"ed_{i}"):
st.session_state.editing_index = i
st.rerun()
if b3.button("Smazat", key=f"d_{i}"):
st.session_state.recipes.pop(i)
db_save()
st.rerun()
