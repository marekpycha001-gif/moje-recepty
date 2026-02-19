Moje obrovská omluva, tohle mě mrzí! Ten SyntaxError se tam vloudil kvůli tomu, že jsem do kódu přidal st.stop() (překlepl jsem se na stop()) a pár dalších drobností, které se uvnitř toho textového řetězce "pohádaly" s Pythonem.

Už jsem to opravil. Kód jsem maximálně zjednodušil, odstranil problematické části a nechal tam jen to nejdůležitější: Čimilali, autodetekci modelu, automatické promazání políčka a ukládání do tabulky.

Tady je opravená verze:

ZAČÁTEK
CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

SDB_URL = ""

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

if api:
XXXt1, t2 = st.tabs(["Text", "Foto"])
XXXwith t1:
XXXXXXwith st.form("text_form", clear_on_submit=True):
XXXXXXXXXu = st.text_area("Vloz text:")
XXXXXXXXXif st.form_submit_button("Čimilali"):
XXXXXXXXXXXXif u:
XXXXXXXXXXXXXXXr_t = analyze(u, api)
XXXXXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXXXXdb_save()
XXXXXXXXXXXXXXXst.rerun()
XXXwith t2:
XXXXXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXXXXif f and st.button("Čimilali", key="b2"):
XXXXXXXXXr_t = analyze(Image.open(f), api)
XXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
else:
XXXst.warning("Vloz klic vlevo v menu.")

for i, r in enumerate(st.session_state.recipes):
XXXif st.session_state.editing_index == i:
XXXXXXnt = st.text_area("Edit", r["text"], height=300, key=f"e_{i}")
XXXXXXc_e1, c_e2 = st.columns(2)
XXXXXXif c_e1.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
XXXXXXif c_e2.button("Zrusit", key=f"a_{i}"):
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXn = "Recept"
XXXXXXfor l in r["text"].splitlines():
XXXXXXXXXif "NAZEV:" in l.upper(): n = l.split(":", 1)[1]
XXXXXXf_i = "❤️" if r.get("fav") else "🤍"
XXXXXXwith st.expander(f"{f_i} {n}"):
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
