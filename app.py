import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")
SDB_URL = ""

if "recipes" not in st.session_state:
XXXtry:
XXXXXXr = requests.get(SDB_URL, timeout=5)
XXXXXXif r.status_code == 200:
XXXXXXXXXst.session_state.recipes = [{"text": x.get("text", ""), "fav": str(x.get("fav", "")).lower() == "true"} for x in r.json()]
XXXXXXelse:
XXXXXXXXXst.session_state.recipes = []
XXXexcept:
XXXXXXst.session_state.recipes = []

if "editing_index" not in st.session_state:
XXXst.session_state.editing_index = None

def db_save():
XXXtry:
XXXXXXrequests.delete(SDB_URL + "/all")
XXXXXXif st.session_state.recipes:
XXXXXXXXXdata = [{"text": r["text"], "fav": str(r["fav"]).lower()} for r in st.session_state.recipes]
XXXXXXXXXrequests.post(SDB_URL, json={"data": data})
XXXexcept Exception as e:
XXXXXXst.error(f"Chyba pri zapisu: {e}")

def analyze(content, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXmodel = genai.GenerativeModel("gemini-1.5-flash")
XXXXXXp = "Jsi expert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
XXXXXXwith st.spinner("Cimilali maka..."):
XXXXXXXXXres = model.generate_content([p, content])
XXXXXXXXXreturn res.text
XXXexcept Exception as e:
XXXXXXreturn str(e)

st.title("🍳 Muj chytry receptar")

st.sidebar.header("Nastaveni")
if st.sidebar.button("Zkouska spojeni"):
XXXtry:
XXXXXXtest_r = requests.get(SDB_URL + "/keys")
XXXXXXst.sidebar.info(f"Odezva: {test_r.status_code}")
XXXXXXst.sidebar.info(f"Sloupce: {test_r.text}")
XXXexcept Exception as e:
XXXXXXst.sidebar.error(f"Chyba: {e}")

api = st.sidebar.text_input("Vlozit API klic", type="password")

if api:
XXXt1, t2 = st.tabs(["Text", "Foto"])
XXXwith t1:
XXXXXXwith st.form("t_form", clear_on_submit=True):
XXXXXXXXXu = st.text_area("Vlozit text:")
XXXXXXXXXif st.form_submit_button("Cimilali"):
XXXXXXXXXXXXif u:
XXXXXXXXXXXXXXXr_t = analyze(u, api)
XXXXXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXXXXdb_save()
XXXXXXXXXXXXXXXst.rerun()
XXXwith t2:
XXXXXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXXXXif f and st.button("Cimilali", key="c2"):
XXXXXXXXXr_t = analyze(Image.open(f), api)
XXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
else:
XXXst.info("Vloz klic v menu.")

for i, r in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXnt = st.text_area("Editace", r["text"], height=300, key=f"e_{i}")
XXXXXXc1, c2 = st.columns(2)
XXXXXXif c1.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
XXXXXXif c2.button("Zrusit", key=f"a_{i}"):
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXn = "Recept"
XXXXXXlines = str(r["text"]).splitlines()
XXXXXXfor l in lines:
XXXXXXXXXif "NAZEV:" in l.upper():
XXXXXXXXXXXXn = l.split(":", 1)[1]
XXXXXXXXXXXXbreak
XXXXXXikona = "❤️" if r.get("fav") else "🤍"
XXXXXXwith st.expander(f"{ikona} {n}"):
XXXXXXXXXst.markdown(r["text"])
XXXXXXXXXb1, b2, b3 = st.columns(3)
XXXXXXXXXif b1.button("Oblibene", key=f"f_{i}"):
XXXXXXXXXXXXst.session_state.recipes[i]["fav"] = not r.get("fav")
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif b2.button("Edit", key=f"ed_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif b3.button("Smazat", key=f"d_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
