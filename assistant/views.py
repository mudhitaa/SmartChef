from django.shortcuts import render
from .rag import answer_question
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import traceback  # <--- add this

# ---- AI chat page ----
def chat_page(request):
    return render(request, "assistant/chat.html")

def recipe_generator_page(request):
    return render(request, "assistant/generate_recipe.html")

@csrf_exempt
def ai_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required."}, status=400)

    try:
        data = json.loads(request.body)
        question = data.get("question", "").strip()
        if not question:
            return JsonResponse({"error": "Empty question."}, status=400)

        answer, sources = answer_question(question)
        return JsonResponse({"answer": answer, "sources": sources})

    except Exception as e:
        # Print full traceback to console for debugging
        print("Exception in ai_chat:", e)
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def generate_recipe(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    recipe_name = data.get("recipe_name", "")
    ingredients = data.get("ingredients", "")
    servings = data.get("servings", "")
    time_required = data.get("time_required", "")
    allergies = data.get("allergies", "")

    prompt = f"""
Create a fully structured recipe.

Recipe Name: {recipe_name}
Ingredients: {ingredients}
Servings: {servings}
Time Required: {time_required}
Allergies to avoid: {allergies}

Format the output EXACTLY like this:

🍽️ **Recipe Title**

---

### 📝 Ingredients
- list items

### 👩‍🍳 Steps
1. step one
2. step two
3. step three

### ⚠️ Allergy Warnings
- bullet list based on ingredients + allergies

### 🔥 Nutrition (per serving)
- Calories:
- Protein:
- Carbs:
- Fat:

### ⭐ Suggestions
- Healthy alternatives
- Flavor improvements
- Side dish ideas
"""

    answer, _ = answer_question(prompt)
    return JsonResponse({"answer": answer})