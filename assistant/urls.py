from django.urls import path
from . import views  # Import views as a module

urlpatterns = [
    #path("chat/", views.chat_page, name="assistant_chat"),              # Chat UI
    #path("ask/", views.ai_chat, name="assistant_ask"),                  # API endpoint for chat
    path("generate/", views.recipe_generator_page, name="recipe_generator_page"),  # Recipe input UI
    path("generate-recipe/", views.generate_recipe, name="generate_recipe"),       # API endpoint for generating recipe
]
