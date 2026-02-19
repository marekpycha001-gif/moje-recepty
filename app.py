CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests
import pandas as pd

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

SDB_URL = ""

if 'recipes' not in st.session_state:
XXXtry:
XXXXXXres = requests.get(SDB_URL)
XXXXXXif res.status_code == 200:
XXXXXXXXXdata = res.json()
XXXXXXXXXst.session_state.recipes = [{"text": r["text"], "fav": str(r["fav"]).lower() == "true"} for r in data]
XXXXXXelse: st.session_state.recipes = []
XXXexcept: st.session_state.recipes = []

if 'editing_index' not in st.session_state:
XXXst.session_state.editing_index = None

def save_to_db():
XXXtry:
XXXXXXrequests.delete(SDB_URL + "/all")
XXXXXXif st.session_state.recipes:
XXXXXXXXXdf = pd.DataFrame(st.session_state.recipes)
XXXXXXXXXrequests.post(SDB_URL, json={"data": df.to_dict(orient='records')})
XXXexcept: pass

def analyze_recipe(content, content_type, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXmodel = genai.GenerativeModel("gemini-1.5-flash")
XXXXXXprompt = 'Jsi expert na vareni. Vsechny objemove miry prepocitej na GRAMY (g). Nekopiruj text slovo od slova. Napis postup vlastnimi slovy. Vystup: NAZEV: [Nazev], KATEGORIE: [Sladke/Slane], INGREDIENCE: - [cislo] [jednotka] [surovina], POSTUP: 1. [Krok]'
XXXXXXwith st.spinner("Zpracovavam..."):
XXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXreturn response.text
XXXexcept Exception as e: return str(e)

def adjust_portions(text, multiplier):
XXXif multiplier == 1.0: return text
XXXlines = text.splitlines()
XXXnew_lines, is_ing = [], False
XXXfor line in lines:
XXXXXXif "INGREDIENCE" in line.upper(): is_ing = True
XXXXXXif "POSTUP" in line.upper(): is_ing = False
XXXXXXif is_ing and line.strip().startswith("-"):
XXXXXXXXXwords = line.split()
XXXXXXXXXfor i, w in enumerate(words):
XXXXXXXXXXXXtry:
XXXXXXXXXXXXXXXnum = float(w.replace(",", "."))
XXXXXXXXXXXXXXXnew_num = num * multiplier
XXXXXXXXXXXXXXXwords[i] = str(int(new_num)) if new_num.is_integer() else str(round(new_num, 1))
XXXXXXXXXXXXXXXbreak
XXXXXXXXXXXXexcept: continue
XXXXXXXXXnew_lines.append(" ".join(words))
XXXXXXelse: new_lines.append(line)
XXXreturn chr(10).join(new_lines)

st.title("🍳 Můj chytrý receptář")
with st.expander("Nastaveni"):
XXXapi_key = st.text_input("API klic", type="password")
if not api_key:
XXXst.warning("Vloz klic.")
XXXst.stop()

t1, t2 = st.tabs(["Text", "Obrazek"])
with t1:
XXXu = st.text_area("Vloz text:")
XXXif st.button("Čimilali", key="b1"):
XXXXXXr = analyze_recipe(u, "text", api_key)
XXXXXXst.session_state.recipes.insert(0, {"text": r, "fav": False})
XXXXXXsave_to_db()
XXXXXXst.rerun()
with t2:
XXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXif f and st.button("Čimilali", key="b2"):
XXXXXXr = analyze_recipe(Image.open(f), "image", api_key)
XXXXXXst.session_state.recipes.insert(0, {"text": r, "fav": False})
XXXXXXsave_to_db()
XXXXXXst.rerun()

st.divider()
h = st.text_input("🔍 Hledat...").lower()
ob = st.checkbox("❤️ Jen oblibene")

for i, r in enumerate(st.session_state.recipes):
XXXif ob and not r["fav"]: continue
XXXif h and h not in r["text"].lower(): continue
XXXif st.session_state.editing_index == i:
XXXXXXnt = st.text_area("Upravit", r["text"], height=300, key=f"e_{i}")
XXXXXXif st.button("Ulozit", key=f"s_{i}"):
XXXXXXXXXst.session_state.recipes[i]["text"] = nt
XXXXXXXXXst.session_state.editing_index = None
XXXXXXXXXsave_to_db()
XXXXXXXXXst.rerun()
XXXelse:
XXXXXXnazev = "Recept"
XXXXXXfor l in r["text"].splitlines():
XXXXXXXXXif "NAZEV:" in l.upper(): nazev = l.split(":", 1)[1]
XXXXXXwith st.expander(f"{'❤️' if r.get('fav') else '🤍'} {nazev}"):
XXXXXXXXXm = st.number_input("Nasobitel", 0.5, 5.0, 1.0, 0.5, key=f"m_{i}")
XXXXXXXXXst.markdown(adjust_portions(r["text"], m))
XXXXXXXXXc1, c2, c3 = st.columns(3)
XXXXXXXXXif c1.button("❤️/💔", key=f"f_{i}"):
XXXXXXXXXXXXst.session_state.recipes[i]["fav"] = not r["fav"]
XXXXXXXXXXXXsave_to_db()
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c2.button("✏️", key=f"ed_{i}"):
XXXXXXXXXXXXst.session_state.editing_index = i
XXXXXXXXXXXXst.rerun()
XXXXXXXXXif c3.button("🗑️", key=f"d_{i}"):
XXXXXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXXXXsave_to_db()
XXXXXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
