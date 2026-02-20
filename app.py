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
XXXXXXst.toast("Zkousim smazat vse...")
XXXXXXdel_res = requests.delete(SDB_URL + "/all")
XXXXXXif st.session_state.recipes:
XXXXXXXXXdata = [{"text": r["text"], "fav": str(r["fav"]).lower()} for r in st.session_state.recipes]
XXXXXXXXXpost_res = requests.post(SDB_URL, json={"data": data})
XXXXXXXXXif post_res.status_code == 201:
XXXXXXXXXXXXst.toast("Hotovo! Ulozeno do tabulky ✅")
XXXXXXXXXelse:
XXXXXXXXXXXXst.error(f"SheetDB Error {post_res.status_code}: {post_res.text}")
XXXXXXelse:
XXXXXXXXXst.info("Seznam je prazdny.")
XXXexcept Exception as e:
XXXXXXst.error(f"Kriticka chyba: {e}")

st.title("🍳 Muj chytry receptar")

TESTOVACI TLACITKO V SIDEBARU
if st.sidebar.button("🚨 NATVRDO ULOZIT TEST"):
XXXst.session_state.recipes.insert(0, {"text": "NAZEV: Testovaci recept", "fav": True})
XXXdb_save()
XXXst.rerun()

api = st.sidebar.text_input("Vlozit API klic", type="password")

def analyze(content, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXmodels = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
XXXXXXm_name = next((m for m in models if "flash" in m), models[0])
XXXXXXmodel = genai.GenerativeModel(m_name)
XXXXXXp = "Jsi expert na vareni. Format: NAZEV: [Nazev], INGREDIENCE: - [surovina], POSTUP: 1. [Krok]"
XXXXXXres = model.generate_content([p, content])
XXXXXXreturn res.text
XXXexcept Exception as e: return str(e)

if api:
XXXt1, t2 = st.tabs(["Text", "Foto"])
XXXwith t1:
XXXXXXwith st.form("t_form", clear_on_submit=True):
XXXXXXXXXu = st.text_area("Vlozit text:")
XXXXXXXXXif st.form_submit_button("Cimilali"):
XXXXXXXXXXXXif u:
XXXXXXXXXXXXXXXr_t = analyze(u, api)
XXXXXXXXXXXXXXXif "Part" not in str(r_t) and "quota" not in str(r_t).lower():
XXXXXXXXXXXXXXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXXXXXXXXXXXXXdb_save()
XXXXXXXXXXXXXXXXXXst.rerun()
XXXXXXXXXXXXXXXelse: st.error(f"Chyba Gemini: {r_t}")
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
XXXwith st.expander(f"{'❤️' if r.get('fav') else '🤍'} {str(r['text'])[:30]}..."):
XXXXXXst.markdown(r["text"])
XXXXXXif st.button("Smazat", key=f"d_{i}"):
XXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
