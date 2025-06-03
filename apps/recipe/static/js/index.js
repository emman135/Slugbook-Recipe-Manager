"use strict";

let app = {}
app.config = {
    data: function () {
        console.log("Mounting")
        return {
            recipes: [],
            filtered_recipes: [],
            editing: { current: null },
        };
    },
    methods: {
        search_recipes: function (input_text) {
            // console.log(input_text)
            const text = input_text.toLowerCase();
            this.filtered_recipes = this.recipes.filter(recipe => (recipe.name.toLowerCase().includes(text) | recipe.type.toLowerCase().includes(text)));
        },
    }
}

app.load_recipe_data = function () {
    const options = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    };
    fetch('/recipe/api/recipes', options)
        .then(response => response.json())
        .then(jsonResponse => {
            app.vue.recipes = jsonResponse.recipes;
            app.vue.filtered_recipes = jsonResponse.recipes;
        });
}
app.vue = Vue.createApp(app.config).mount("#app");
app.load_recipe_data();