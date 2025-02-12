import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import openai

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/generate_response_text', methods=['POST'])
def generate_response_text():
    data = request.json
    input_text = data.get("text", "")
    prompt = "Imagine you're a restaurant employee, responding to the following customer inquiry:"
    
    if input_text:
        try:
            chat_completion = openai.ChatCompletion.create(
                messages=[{"role": "user", "content": prompt + input_text}],
                model="gpt-3.5-turbo",
                max_tokens=40
            )
            ai_response = chat_completion.choices[0].message.content.strip()
            return jsonify({"response_text": ai_response})
        except Exception as e:
            print("Error with AI model:", e)
            return jsonify({"error": f"AI model error: {str(e)}"}), 500
    else:
        return jsonify({"error": "No text provided"}), 400

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    data = request.json
    input_text = data.get("text", "")
    prompt = (
        "Summarize this customer's inquiry suitable for a restaurant employee's use. "
        "If it's an order, write it in an order format with a list including user's name and items names:"
    )
    
    if input_text:
        try:
            chat_completion = openai.ChatCompletion.create(
                messages=[{"role": "user", "content": prompt + input_text}],
                model="gpt-3.5-turbo",
                max_tokens=100  # Increase max tokens for a potentially longer summary
            )
            summary = chat_completion.choices[0].message.content.strip()
            return jsonify({"summary": summary})
        except Exception as e:
            print("Error with AI model:", e)
            return jsonify({"error": f"AI model error: {str(e)}"}), 500
    else:
        return jsonify({"error": "No text provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
