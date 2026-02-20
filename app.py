import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

CODE = """
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
XXXXXXelse: st.session_state.recipes = []
XXXexcept: st.session_state.recipes = []

if "editing_index" not in st.session_state:
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
XXXXXXp = "Jsi expert na vareni. Vsechny miry dej na gramy (g). Format: NAZEV: [Nazev], INGREDIENCE: - [cislo] [jednotka] [surovina], POSTUP: 1. [Krok]"
XXXXXXwith st.spinner("Cimilali maka..."):
XXXXXXXXXres = model.generate_content([p, content])
XXXXXXXXXreturn res.text
XXXexcept Exception as e: return str(e)

st.title("🍳 Muj chytry receptar")
api = st.sidebar.text_input("Vlozit API klic", type="password")

if api:
XXXt1, t2 = st.tabs(["Text", "Foto"])
XXXwith t1:
XXXXXXwith st.form("t_form", clear_on_submit=True):
XXXXXXXXXu = st.text_area("Vlozit text:")
XXXXXXXXXif st.form_submit_button("Cimilali"):
XXXXXXXXXXXXif u:
XXXXXXXXXXXXXXXr_t = analyze(u, api)
XXXXXXXXXXXXXXXif "quota" not in str(r_t).lower() and "429" not in str(r_t):
XXXXXXXXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXXXXXXXdb_save()
XXXXXXXXXXXXXXXXXXst.rerun()
XXXXXXXXXXXXXXXelse: st.error("Dosel denni limit nebo prilis mnoho dotazu.")
XXXwith t2:
XXXXXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXXXXif f and st.button("Cimilali", key="c2"):
XXXXXXXXXr_t = analyze(Image.open(f), api)
XXXXXXXXXif "quota" not in str(r_t).lower() and "429" not in str(r_t):
XXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
XXXXXXXXXelse: st.error("Dosel denni limit nebo prilis mnoho dotazu.")
else:
XXXst.info("Vlozit klic vlevo.")

for i, r in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXnt = st.text_area("Edit", r["text"], height=300, key=f"e_{i}")
XXXXXXif st.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXn = "Recept"
XXXXXXfor l in str(r["text"]).splitlines():
XXXXXXXXXif "NAZEV:" in l.upper(): n = l.split(":", 1)[1]
XXXXXXwith st.expander(f"{'❤️' if r.get('fav') else '🤍'} {n}"):
XXXXXXXXXst.markdown(r["text"])
XXXXXXXXXc1, c2, c3 = st.columns(3)
XXXXXXXXXif c1.button("❤️", key=f"f_{i}"):
XXXXXXXXXXXXst.session_state.recipes[i]["fav"] = not r.get("fav")
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c2.button("Upravit", key=f"ed_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c3.button("Smazat", key=f"d_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXdb_save()
XXXXXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
