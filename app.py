CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

SDB_URL = ""

Inicializace stavu
if 'recipes' not in st.session_state:
XXXtry:
XXXXXXr = requests.get(SDB_URL, timeout=5)
XXXXXXif r.status_code == 200:
XXXXXXXXXst.session_state.recipes = [{"text": x.get("text", ""), "fav": str(x.get("fav", "")).lower() == "true"} for x in r.json()]
XXXXXXelse: st.session_state.recipes = []
XXXexcept: st.session_state.recipes = []

if 'editing_index' not in st.session_state:
XXXst.session_state.editing_index = None

def db_save():
XXXtry:
XXXXXXrequests.delete(SDB_URL + "/all")
XXXXXXif st.session_state.recipes:
XXXXXXXXXdata = [{"text": r["text"], "fav": str(r["fav"]).lower()} for r in st.session_state.recipes]
XXXXXXXXXrequests.post(SDB_URL, json={"data": data})
XXXexcept: pass

def analyze(content, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXmodels = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
XXXXXXm_name = next((m for m in models if "flash" in m), models[0])
XXXXXXmodel = genai.GenerativeModel(m_name)
XXXXXXp = "Jsi expert na vareni. Vsechny miry dej na gramy (g). Napis vlastnimi slovy. Format: NAZEV: [Nazev], INGREDIENCE: - [cislo] [jednotka] [surovina], POSTUP: 1. [Krok]"
XXXXXXwith st.spinner("Čimilali maka..."):
XXXXXXXXXres = model.generate_content([p, content])
XXXXXXXXXreturn res.text
XXXexcept Exception as e: return str(e)

st.title("🍳 Můj chytrý receptář")
api = st.sidebar.text_input("API klic", type="password")

if not api:
XXXst.warning("Vloz klic vlevo v menu.")
XXXst.stop()

t1, t2 = st.tabs(["Text", "Foto"])
with t1:
XXXwith st.form("text_form", clear_on_submit=True):
XXXXXXu = st.text_area("Vloz text:")
XXXXXXif st.form_submit_button("Čimilali"):
XXXXXXXXXif u:
XXXXXXXXXXXXr_t = analyze(u, api)
XXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()

with t2:
XXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXif f and st.button("Čimilali", key="c2"):
XXXXXXr_t = analyze(Image.open(f), api)
XXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXdb_save()
XXXXXXst.rerun()

for i, r in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXnt = st.text_area("Edit", r["text"], height=300, key=f"e_{i}")
XXXXXXc_edit1, c_edit2 = st.columns(2)
XXXXXXif c_edit1.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
XXXXXXif c_edit2.button("Zrusit", key=f"a_{i}"):
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXn = "Recept"
XXXXXXfor l in r["text"].splitlines():
XXXXXXXXXif "NAZEV:" in l.upper(): n = l.split(":", 1)[1]
XXXXXXfav_i = "❤️" if r.get("fav") else "🤍"
XXXXXXwith st.expander(f"{fav_i} {n}"):
XXXXXXXXXst.markdown(r["text"])
XXXXXXXXXc1, c2, c3 = st.columns(3)
XXXXXXXXXif c1.button("❤️", key=f"f_{i}"):
XXXXXXXXXXXXst.session_state.recipes[i]["fav"] = not r.get("fav")
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c2.button("✏️", key=f"ed_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c3.button("🗑️", key=f"d_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
