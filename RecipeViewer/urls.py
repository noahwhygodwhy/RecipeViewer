from django.urls import path

from . import views

urlpatterns = [
    path('', views.recipeView, name='Recipes'),
    path('ingredients/', views.ingredientView, name='Ingredients'),
    path('getRecipeInfo/', views.recipeDetails, name='recipeDetails'),
    path('getIngredientInfo/', views.ingredientDetails, name='ingredientDetails'),
    path('updateIngredientQuantity/', views.updateIngredientQuantity, name='updateIngredientQuantity'),
    path('addIngredient/', views.addIngredient, name='addIngredient'),
    path('getIngredientQuantity/', views.getIngredientQuantity, name="getIngredientQuantity"),
    path('makeRecipe/', views.makeRecipe, name="makeRecipe"),
    path('addRecipe/', views.addRecipe, name="addRecipe"),
    path('getIngredientRow/', views.getIngredientRow, name="getIngredientRow"),
    path('getIngredientExists/', views.getIngredientExists, name="getIngredientExists"),
    path('makes/', views.makeView, name='Makes'),
    #path('analytics/', views.analyticsView, name='Analytics'),
    #path('users/', views.userView, name='Users'),
] 