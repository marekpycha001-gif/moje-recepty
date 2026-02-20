import { useState } from "react";

export default function App() {
  const [recipes, setRecipes] = useState([
    {
      id: 1,
      name: "Palačinky",
      ingredients: ["mléko", "mouka", "vejce"],
      text: "Smíchat a usmažit",
      fav: false
    }
  ]);

  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState(null);

  // SEARCH
  const filtered = recipes.filter(r => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();

    return (
      r.name.toLowerCase().includes(q) ||
      r.text.toLowerCase().includes(q) ||
      r.ingredients.some(i => i.toLowerCase().includes(q))
    );
  });

  // ADD
  function addRecipe() {
    const id = Date.now();
    setRecipes([
      ...recipes,
      { id, name: "Nový recept", ingredients: [], text: "", fav: false }
    ]);
    setOpenId(id);
  }

  // DELETE
  function del(id) {
    setRecipes(recipes.filter(r => r.id !== id));
  }

  // UPDATE
  function update(id, field, value) {
    setRecipes(recipes.map(r => (r.id === id ? { ...r, [field]: value } : r)));
  }

  // INGREDIENT UPDATE
  function updateIng(id, index, value) {
    setRecipes(
      recipes.map(r => {
        if (r.id !== id) return r;
        const arr = [...r.ingredients];
        arr[index] = value;
        return { ...r, ingredients: arr };
      })
    );
  }

  function addIng(id) {
    setRecipes(
      recipes.map(r =>
        r.id === id ? { ...r, ingredients: [...r.ingredients, ""] } : r
      )
    );
  }

  // FAVORITE
  function toggleFav(id) {
    setRecipes(
      recipes.map(r =>
        r.id === id ? { ...r, fav: !r.fav } : r
      )
    );
  }

  // HIGHLIGHT TEXT
  function highlight(text) {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, "gi"));
    return parts.map((p, i) =>
      p.toLowerCase() === query.toLowerCase() ? (
        <mark key={i}>{p}</mark>
      ) : (
        p
      )
    );
  }

  return (
    <div style={styles.app}>
      
      {/* TOP BAR */}
      <div style={styles.top}>
        <div style={styles.icons}>
          <button onClick={addRecipe}>＋</button>
          <button onClick={() => setQuery("")}>⟳</button>
          <button>🔍</button>
          <button>🔑</button>
        </div>

        <h1 style={styles.title}>Márova kuchařka</h1>

        <input
          style={styles.search}
          placeholder="Hledat recept nebo ingredienci..."
          value={query}
          onChange={e => setQuery(e.target.value)}
        />

        <div style={styles.count}>
          {filtered.length} receptů
        </div>
      </div>

      {/* LIST */}
      <div>
        {filtered.map(r => (
          <div
            key={r.id}
            style={{
              ...styles.card,
              animation: "fade .25s"
            }}
          >
            {/* HEADER */}
            <div style={styles.row}>
              <b onClick={() => setOpenId(openId === r.id ? null : r.id)}>
                {highlight(r.name)}
              </b>

              <div>
                <button onClick={() => toggleFav(r.id)}>
                  {r.fav ? "⭐" : "☆"}
                </button>

                <button onClick={() => del(r.id)}>🗑</button>
              </div>
            </div>

            {/* DETAIL */}
            {openId === r.id && (
              <div style={styles.detail}>
                <input
                  style={styles.input}
                  value={r.name}
                  onChange={e => update(r.id, "name", e.target.value)}
                />

                {r.ingredients.map((ing, i) => (
                  <input
                    key={i}
                    style={styles.input}
                    value={ing}
                    onChange={e => updateIng(r.id, i, e.target.value)}
                    placeholder="Ingredience"
                  />
                ))}

                <button onClick={() => addIng(r.id)}>+ ingredience</button>

                <textarea
                  style={styles.textarea}
                  value={r.text}
                  onChange={e => update(r.id, "text", e.target.value)}
                  placeholder="Postup"
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <style>{`
        @keyframes fade {
          from {opacity:0; transform:translateY(6px)}
          to {opacity:1; transform:translateY(0)}
        }
      `}</style>
    </div>
  );
}

const styles = {
  app: {
    fontFamily: "sans-serif",
    padding: 15,
    background: "linear-gradient(160deg,#0b1d3a,#133a7c)",
    minHeight: "100vh",
    color: "white"
  },

  top: { textAlign: "center" },

  icons: {
    display: "flex",
    justifyContent: "center",
    gap: 6,
    marginBottom: 5
  },

  title: {
    fontFamily: "Dancing Script",
    fontSize: "1.8rem",
    margin: 4
  },

  search: {
    padding: 6,
    borderRadius: 8,
    border: "none",
    marginTop: 4
  },

  count: {
    opacity: 0.7,
    fontSize: 13,
    marginTop: 3
  },

  card: {
    background: "#1e3a8a",
    padding: 12,
    borderRadius: 14,
    marginTop: 10
  },

  row: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center"
  },

  detail: {
    marginTop: 10,
    display: "flex",
    flexDirection: "column",
    gap: 6
  },

  input: {
    padding: 6,
    borderRadius: 6,
    border: "none"
  },

  textarea: {
    padding: 6,
    borderRadius: 6,
    border: "none"
  }
};
