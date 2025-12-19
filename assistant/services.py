import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from rag import build_rag_engine

load_dotenv()

app = Flask(__name__)
CORS(app)

groq_api_key = os.environ.get("GROQ_API_KEY")
# Allow an explicit mock LLM mode useful for local dev / end-to-end UI testing
# - If MOCK_LLM is truthy and there is no GROQ_API_KEY, /ask will reply with
#   a canned response built from the retrieved RAG context instead of returning
#   a 503. This makes it easy to exercise the full frontend -> backend flow.
MOCK_LLM = os.environ.get("MOCK_LLM", "0").lower() in ("1", "true", "yes")

if not groq_api_key:
    # Allow running the backend without a Groq API key (dev mode). The
    # app will start, but /ask will return an error unless a key is provided.
    print(
        "WARNING: Missing GROQ_API_KEY — running in local dev "
        "mode (no Groq calls)."
    )
    groq_client = None
else:
    groq_client = Groq(api_key=groq_api_key)

# Parse comma-separated list of models to try in order (fallback)
GROQ_MODELS_RAW = os.environ.get(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile,llama-3.1-8b-instant"
)

GROQ_MODELS = [m.strip() for m in GROQ_MODELS_RAW.split(",") if m.strip()]
GROQ_MODEL = GROQ_MODELS[0] if GROQ_MODELS else "mixtral-8x7b-32768"

rag_engine = build_rag_engine()


@app.route("/health", methods=["GET"])
def health() -> tuple[str, int]:
    return "ok", 200


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True)
    question = (data or {}).get("question", "").strip()

    if not question:
        return jsonify({"error": "Question is required."}), 400

    chunks, sources = rag_engine.query(question)
    if chunks:
        context = "\n\n".join(chunks)
    else:
        context = "No context from the cookbook."

    prompt = (
        "You are a friendly cooking assistant. Answer using only the context "
        "if possible. If the context does not contain the answer, say you "
        "do not know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
    )

    if not groq_client:
        # If the developer explicitly enabled MOCK_LLM we return a helpful
        # canned response that includes the retrieved context so the UI
        # can be exercised without a real Groq API key.
        if MOCK_LLM:
            # If we have any chunks provide a short mock answer using the
            # first chunk plus a summarised hint. Also return the sources list
            # unchanged so the UI can display origin info.
            if chunks:
                sample = chunks[0][:400]
                mock_answer = (
                    "(MOCK) I looked through your cookbook and found relevant text "
                    f"(excerpt): {sample}"
                )
            else:
                mock_answer = "(MOCK) I could not find any context in the cookbook to answer that."

            return jsonify({"answer": mock_answer, "sources": sources}), 200

        # Otherwise behave as before and return a service-unavailable error
        return (
            jsonify(
                {
                    "error": (
                        "Missing GROQ_API_KEY — cannot forward request to LLM."
                    )
                }
            ),
            503,
        )

    try:
        # Try each model in the list until one succeeds
        last_error = None
        for model_to_try in GROQ_MODELS:
            try:
                response = groq_client.chat.completions.create(
                    model=model_to_try,
                    messages=[
                        {
                            "role": "system",
                            "content": "You help with cooking questions.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=512,
                )
                # Success! Break out of the loop
                break
            except Exception as exc:
                last_error = exc
                # If this model failed, try the next one
                continue
        else:
            # All models failed
            return (
                jsonify(
                    {"error": f"All Groq models failed. Last error: {last_error}"}
                ),
                500,
            )
    except Exception as exc:
        return jsonify({"error": f"Groq API call failed: {exc}"}), 500

    answer = response.choices[0].message.content.strip()
    return jsonify({"answer": answer, "sources": sources})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
