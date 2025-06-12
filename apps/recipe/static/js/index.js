"use strict";

let app = {}

function clone(obj) { return JSON.parse(JSON.stringify(obj)); }

function ajax(url, method, data, callback) {
    let options = {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin'
    };
    if (data) {
        options.body = JSON.stringify(data);
    }
    return fetch(url, options).then(response => { return response.json(); }).then(function(res){
        if(res.errors && res.errors.length) {
            console.log(res);
            alert("validation error " + JSON.stringify(res.errors));
        } else if (callback) {
            callback(res);
        }
    }, function(){ alert("network error"); });
}

app.empty_ingredient = { id: 0, name: "", unit: "", calories_per_unit: 0, description: "" };


app.config = {
    data: function () {
        console.log("Mounting")
        return {
            recipes: [],
            filtered_recipes: [],
            ingredients: [],
            selected_ingredients: [],
            new_ingredient: clone(app.empty_ingredient),
            ingredient_search: "",
            editing: { current: null },
        };
    },
    methods: {
        search: function() {
            const term = this.new_ingredient.name.toLowerCase();
            this.selected_ingredients = this.ingredients.filter(ing => ing.name.toLowerCase().includes(term));
        },
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

app.load_ingredient_data = function () {
    const options = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    };
    fetch('/recipe/api/ingredients', options)
        .then(response => response.json())
        .then(jsonResponse => {
            app.vue.ingredients = jsonResponse.ingredients;
            app.vue.selected_ingredients = jsonResponse.ingredients;
        });
}

app.vue = Vue.createApp(app.config).mount("#app");
app.load_recipe_data();
app.load_ingredient_data();