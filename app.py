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
XXXXXXst.session_state.recipes = [{"text": x.get("text", ""), "fav": str(x.get("fav", "")).lower() == "true"} for x in r.json()]
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
XXXXXXmodel = genai.GenerativeModel("gemini-1.5-flash")
XXXXXXprompt = "Jsi expert na vareni. Vsechny miry dej na gramy (g). Napis vlastnimi slovy. Format: NAZEV: [Nazev], INGREDIENCE: - [cislo] [jednotka] [surovina], POSTUP: 1. [Krok]"
XXXXXXwith st.spinner("Čimilali maka..."):
XXXXXXXXXres = model.generate_content([prompt, content])
XXXXXXXXXreturn res.text
XXXexcept Exception as e: return str(e)

def calc(text, m):
XXXif m == 1.0: return text
XXXlines = text.splitlines()
XXXnew, is_ing = [], False
XXXfor l in lines:
XXXXXXif "INGREDIENCE" in l.upper(): is_ing = True
XXXXXXif "POSTUP" in l.upper(): is_ing = False
XXXXXXif is_ing and l.strip().startswith("-"):
XXXXXXXXXw = l.split()
XXXXXXXXXfor i, word in enumerate(w):
XXXXXXXXXXXXtry:
XXXXXXXXXXXXXXXv = float(word.replace(",", ".")) * m
XXXXXXXXXXXXXXXw[i] = str(int(v)) if v.is_integer() else str(round(v, 1))
XXXXXXXXXXXXXXXbreak
XXXXXXXXXXXXexcept: continue
XXXXXXXXXnew.append(" ".join(w))
XXXXXXelse: new.append(l)
XXXreturn chr(10).join(new_lines)

st.title("🍳 Můj chytrý receptář")
api = st.sidebar.text_input("API klic", type="password")

if not api:
XXXst.warning("Vloz klic vlevo v menu.")
XXXst.stop()

t1, t2 = st.tabs(["Text", "Foto"])
with t1:
XXXu = st.text_area("Vloz text:")
XXXif st.button("Čimilali", key="c1"):
XXXXXXr_t = analyze(u, api)
XXXXXXst.session_state.recipes.insert(0, {"text": r_t, "fav": False})
XXXXXXdb_save()
XXXXXXst.rerun()
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
XXXXXXif st.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXdb_save()
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXn = "Recept"
XXXXXXfor l in r["text"].splitlines():
XXXXXXXXXif "NAZEV:" in l.upper(): n = l.split(":", 1)[1]
XXXXXXwith st.expander(f"{'❤️' if r.get('fav') else '🤍'} {n}"):
XXXXXXXXXm = st.number_input("Porce", 0.5, 5.0, 1.0, 0.5, key=f"m_{i}")
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
