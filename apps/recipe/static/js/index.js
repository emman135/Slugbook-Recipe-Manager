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