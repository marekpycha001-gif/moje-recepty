CODE = """
import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Moje Recepty", page_icon="🍳")

if 'recipes' not in st.session_state:
XXXst.session_state.recipes = []

if 'editing_index' not in st.session_state:
XXXst.session_state.editing_index = None

def analyze_recipe(content, content_type, api_key):
XXXtry:
XXXXXXgenai.configure(api_key=api_key)
XXXXXXvalid_models = []
XXXXXXfor m in genai.list_models():
XXXXXXXXXif 'generateContent' in m.supported_generation_methods:
XXXXXXXXXXXXvalid_models.append(m.name)
XXXXXXmodel_name = valid_models[0]
XXXXXXfor m in valid_models:
XXXXXXXXXif 'flash' in m:
XXXXXXXXXXXXmodel_name = m
XXXXXXXXXXXXbreak
XXXXXXmodel = genai.GenerativeModel(model_name)
XXXXXXprompt = 'Jsi expert na vareni. Vsechny objemove miry prepocitej na GRAMY (g). Nekopiruj text slovo od slova. Napis postup vlastnimi slovy. Vystup: NAZEV: [Nazev], KATEGORIE: [Sladke/Slane], INGREDIENCE: - [cislo] [jednotka] [surovina], POSTUP: 1. [Krok]'
XXXXXXwith st.spinner("Zpracovavam..."):
XXXXXXXXXif content_type == "image":
XXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXelse:
XXXXXXXXXXXXresponse = model.generate_content([prompt, content])
XXXXXXXXXreturn response.text
XXXexcept Exception as e:
XXXXXXreturn str(e)

def adjust_portions(text, multiplier):
XXXif multiplier == 1.0: return text
XXXlines = text.splitlines()
XXXnew_lines = []
XXXis_ing = False
XXXfor line in lines:
XXXXXXif "INGREDIENCE" in line.upper(): is_ing = True
XXXXXXif "POSTUP" in line.upper(): is_ing = False
XXXXXXif is_ing and line.strip().startswith("-"):
XXXXXXXXXwords = line.split()
XXXXXXXXXfor i, w in enumerate(words):
XXXXXXXXXXXXw_clean = w.replace(",", ".")
XXXXXXXXXXXXtry:
XXXXXXXXXXXXXXXnum = float(w_clean)
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
XXXif st.button("Kouzlo"):
XXXXXXr = analyze_recipe(u, "text", api_key)
XXXXXXst.session_state.recipes.insert(0, {"text": r, "fav": False})
XXXXXXst.rerun()
with t2:
XXXf = st.file_uploader("Foto", type=["jpg", "png"])
XXXif f and st.button("Pridat foto"):
XXXXXXimg = Image.open(f)
XXXXXXr = analyze_recipe(img, "image", api_key)
XXXXXXst.session_state.recipes.insert(0, {"text": r, "fav": False})
XXXXXXst.rerun()

st.divider()
h = st.text_input("🔍 Hledat...").lower()
ob = st.checkbox("❤️ Jen oblibene")

for i, r in enumerate(st.session_state.recipes):
XXXif isinstance(r, str): r = {"text": r, "fav": False}
XXXif ob and not r["fav"]: continue
XXXif h and h not in r["text"].lower(): continue
XXX
XXXnazev = "Recept"
XXXfor l in r["text"].splitlines():
XXXXXXif "NAZEV:" in l.upper(): nazev = l.split(":", 1)[1]
XXX
XXXfav_icon = "❤️" if r["fav"] else "🤍"
XXXwith st.expander(f"{fav_icon} {nazev}"):
XXXXXXm = st.number_input("Nasobitel", 0.5, 5.0, 1.0, 0.5, key=f"m_{i}")
XXXXXXst.markdown(adjust_portions(r["text"], m))
XXXXXXc1, c2, c3 = st.columns(3)
XXXXXXif c1.button("❤️" if not r["fav"] else "💔", key=f"f_{i}"):
XXXXXXXXXst.session_state.recipes[i]["fav"] = not r["fav"]
XXXXXXXXXst.rerun()
XXXXXXif c2.button("✏️", key=f"e_{i}"):
XXXXXXXXXst.session_state.editing_index = i
XXXXXXif c3.button("🗑️", key=f"d_{i}"):
XXXXXXXXXst.session_state.recipes.pop(i)
XXXXXXXXXst.rerun()
"""
exec(CODE.replace("XXX", "    "))
