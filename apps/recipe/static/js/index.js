"use strict";

// small helper
function ajax(url, method, data, cb) {
  const opt = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
  };
  if (data) opt.body = JSON.stringify(data);

  return fetch(url, opt)
    .then((r) => r.json())
    .then((j) => {
      if (j.errors?.length) {
        alert("Validation error:\n" + JSON.stringify(j.errors));
      } else if (cb) cb(j);
    })
    .catch(() => alert("Network error"));
}

// vue config
const app = {
  data() {
    return {
      // ids
      user_id: window.USER_ID || null,
      editId:  null,                 // null = new, else recipe id being edited

      // db tables
      recipes: [],
      filtered_recipes: [],
      ingredients: [],
      selected_ingredients: [],

      // search
      ingredient_search: "",

      // modal & form
      showModal: false,
      newRecipe: {
        name: "",
        type: "",
        description: "",
        instruction_steps: "",
        servings: 1,
        selected: [],
        qty: {},
        imageFile: null,
      },
    };
  },

  computed: {
    /* live calorie preview inside the modal */
    calculatedCalories() {
      if (this.newRecipe.selected.length === 0) return null;
      let perServing = 0;
      this.newRecipe.selected.forEach((id) => {
        const ing = this.ingredients.find((x) => x.id === id);
        if (ing) perServing += (this.newRecipe.qty[id] || 1) * ing.calories_per_unit;
      });
      return perServing * (this.newRecipe.servings || 1);
    },
  },

  methods: {
    // search boxes
    search() {
      const t = this.ingredient_search.toLowerCase().trim();
      this.selected_ingredients = this.ingredients.filter((i) =>
        i.name.toLowerCase().includes(t)
      );
    },
    search_recipes(txt) {
      const t = (txt || "").toLowerCase();
      this.filtered_recipes = this.recipes.filter(
        (r) => r.name.toLowerCase().includes(t) || r.type.toLowerCase().includes(t)
      );
    },
    onFileChange(evt) {
      this.newRecipe.imageFile = evt.target.files[0] || null;
    },

    // modal controls
    openModal() {
      this.editId = null;           // starting a NEW recipe
      this.resetForm();
      this.showModal = true;
    },
    closeModal() {
      this.showModal = false;
    },
    resetForm() {
      this.newRecipe = {
        name: "",
        type: "",
        description: "",
        instruction_steps: "",
        servings: 1,
        selected: [],
        qty: {},
        imageFile: null,
      };
    },

    // start editing an existing recipe
    startEdit(id) {
      ajax(`/recipe/api/recipe/${id}`, "GET", null, (res) => {
        const r = res.recipe;
        this.editId = id;
        this.newRecipe = {
          name: r.name,
          type: r.type,
          description: r.description,
          instruction_steps: r.instruction_steps,
          servings: r.servings,
          selected: res.ingredients.map((l) => l.ingredient_id),
          qty: Object.fromEntries(
            res.ingredients.map((l) => [l.ingredient_id, l.quantity_per_serving])
          ),
          imageFile: null,
        };
        this.showModal = true;
      });
    },

    // CRUD calls
    saveRecipe() {
      if (
        !this.newRecipe.name ||
        !this.newRecipe.type ||
        this.newRecipe.selected.length === 0
      ) {
        alert("Fill required fields and pick at least one ingredient.");
        return;
      }

      const fd = new FormData();
      ["name", "type", "description", "instruction_steps", "servings"].forEach((k) =>
        fd.append(k, this.newRecipe[k])
      );
      fd.append(
        "ingredients",
        JSON.stringify(
          this.newRecipe.selected.map((id) => ({
            id,
            qty: this.newRecipe.qty[id] || 1,
          }))
        )
      );
      if (this.newRecipe.imageFile) fd.append("image", this.newRecipe.imageFile);

      const method = this.editId ? "PUT" : "POST";
      if (this.editId) fd.append("id", this.editId);

      fetch("/recipe/api/recipe", {
        method,
        body: fd,
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((res) => {
          alert("Recipe saved! Total calories = " + res.total_calories);
          this.closeModal();
          this.loadRecipes();
        })
        .catch(() => alert("Network error"));
    },

    /* data loaders */
    loadRecipes() {
      ajax("/recipe/api/internalrecipes", "GET", null, (res) => {
        this.recipes = res.recipes;
        this.filtered_recipes = res.recipes;
      });
    },
    loadIngredients() {
      ajax("/recipe/api/ingredients", "GET", null, (res) => {
        this.ingredients = res.ingredients;
        this.selected_ingredients = res.ingredients;
      });
    },
  },

  // life-cycle
  mounted() {
    this.loadRecipes();
    this.loadIngredients();
  },
};

/* mount */
Vue.createApp(app).mount("#app");