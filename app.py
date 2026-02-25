import streamlit as st
import uuid

st.set_page_config(page_title="Moje recepty", layout="centered")

# ====== CSS – menší řádkování ======
st.markdown("""
<style>
.ingredience p {
    margin: 0px;
    line-height: 1.05;
}
.nazev {
    margin-bottom: 5px;
}
.postup {
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# ====== Inicializace session ======
if "recipes" not in st.session_state:
    st.session_state.recipes = []

# ====== Přidání receptu ======
def add_recipe():
    st.subheader("➕ Přidat nový recept")

    with st.form("new_recipe_form"):
        name = st.text_input("Název receptu")
        ingredients = st.text_area("Ingredience (každá na nový řádek)")
        procedure = st.text_area("Postup")

        submitted = st.form_submit_button("Uložit recept")

        if submitted and name:
            new_recipe = {
                "id": str(uuid.uuid4()),
                "name": name,
                "ingredients": ingredients,
                "procedure": procedure
            }
            st.session_state.recipes.append(new_recipe)
            st.success("Recept uložen ✅")

# ====== Zobrazení receptů ======
def show_recipes():
    st.subheader("📖 Moje recepty")

    for r in st.session_state.recipes:
        with st.expander(r["name"], expanded=False):

            st.markdown(f"<h4 class='nazev'>{r['name']}</h4>", unsafe_allow_html=True)

            st.markdown("**Ingredience:**")
            st.markdown(
                f"<div class='ingredience'>{r['ingredients'].replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )

            st.markdown("<div class='postup'></div>", unsafe_allow_html=True)
            st.markdown("**Postup:**")
            st.write(r["procedure"])

            if st.button("❌ Smazat", key=r["id"]):
                st.session_state.recipes = [
                    recipe for recipe in st.session_state.recipes
                    if recipe["id"] != r["id"]
                ]
                st.success("Recept smazán")
                st.rerun()

# ====== Hlavní část aplikace ======
st.title("🍲 Moje recepty")

add_recipe()

st.divider()

show_recipes()
