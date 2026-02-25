import streamlit as st
import uuid

st.set_page_config(page_title="Moje recepty", layout="centered")

# ---------- STYL ----------
st.markdown("""
<style>
.card{
    background:#1e1e1e;
    padding:18px;
    border-radius:14px;
    margin-bottom:14px;
    border:1px solid #333;
}
.title{
    font-size:22px;
    font-weight:700;
    margin-bottom:6px;
}
.ing p{
    margin:0;
    line-height:1.05;
}
.tag{
    display:inline-block;
    padding:2px 8px;
    border-radius:8px;
    font-size:12px;
    margin-right:6px;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# ---------- DATA ----------
DEFAULT_TAGS = {
    "dezert": "#e74c3c",
    "oběd": "#3498db",
    "Itálie": "#27ae60",
    "Asie": "#9b59b6",
    "slané pečivo": "#f39c12",
    "chuťovky": "#1abc9c",
    "jiné": "#7f8c8d"
}

if "recipes" not in st.session_state:
    st.session_state.recipes = []

if "tags" not in st.session_state:
    st.session_state.tags = DEFAULT_TAGS.copy()

# ---------- FORM ----------
st.title("📖 Moje recepty")

with st.expander("➕ Přidat recept", expanded=False):
    with st.form("add"):
        name = st.text_input("Název")
        ing = st.text_area("Ingredience (po řádcích)")
        proc = st.text_area("Postup")

        tag = st.selectbox("Štítek", list(st.session_state.tags.keys()))

        new_tag = st.text_input("Nový štítek (volitelné)")
        color = st.color_picker("Barva nového štítku", "#ff0000")

        ok = st.form_submit_button("Uložit")

        if ok and name:
            if new_tag:
                st.session_state.tags[new_tag] = color
                tag = new_tag

            st.session_state.recipes.append({
                "id": str(uuid.uuid4()),
                "name": name,
                "ing": ing,
                "proc": proc,
                "tag": tag
            })

            st.success("Uloženo")
            st.rerun()

# ---------- VÝPIS ----------
for r in st.session_state.recipes:

    tag_color = st.session_state.tags.get(r["tag"], "#666")

    st.markdown(f"""
    <div class="card">
        <div class="title">{r["name"]}</div>
        <span class="tag" style="background:{tag_color}">{r["tag"]}</span>
        <br><br>
        <b>Ingredience:</b>
        <div class="ing">{r["ing"].replace(chr(10), "<br>")}</div>
        <br>
        <b>Postup:</b><br>
        {r["proc"]}
    </div>
    """, unsafe_allow_html=True)

    if st.button("Smazat", key=r["id"]):
        st.session_state.recipes = [
            x for x in st.session_state.recipes if x["id"] != r["id"]
        ]
        st.rerun()
