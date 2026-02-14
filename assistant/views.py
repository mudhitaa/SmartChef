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
    extra_requests = data.get("extra_requests", "")

    prompt = f"""
        You are a professional chef and certified nutritionist.
        Create an EXTREMELY detailed, restaurant-quality, professionally formatted recipe.
        User Requirements:
        - Recipe Name: {recipe_name}
        - Ingredients Available: {ingredients}
        - Servings: {servings}
        - Time Required: {time_required}
        - Allergies to avoid: {allergies}
        - Additional Requests: {extra_requests}

        Instructions:
        - Be highly detailed.
        - Include exact measurements in grams and cups.
        - Include cooking temperature.
        - Include pro tips.
        - Ensure nutrition section is realistic.
        - If user has additional requests alter the recipe accordingly.
        - Include macro breakdown clearly.

        Format EXACTLY like this:
        **Recipe Title**

        ---

        ### 📝 Ingredients
        - item (grams + cups)

        ### Time required
        -list the timing details into prep time, cooktime and total time in accordance to the time required.

        ### 👩‍🍳 Detailed Cooking Steps
        1. Step with temperature and technique explanation.
        2. Include timing, texture cues, and professional tips.

        ### 💡 Chef Tips
        - Professional improvements

        ### ⚠️ Allergy Warnings
        - Bullet list

        ### 🔥 Nutrition (Per Serving)
        - Calories:
        - Protein:
        - Carbohydrates:
        - Fat:
        - Fiber:

        ### 🥗 Customization Based on User Request
        - Explain how extra requests were fulfilled.
        -if there were no extra requests acknowledge that.
    """

    answer, _ = answer_question(prompt)
    return JsonResponse({"answer": answer})
