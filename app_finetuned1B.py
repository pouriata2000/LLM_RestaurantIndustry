import os
import re
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import LlamaForCausalLM, AutoTokenizer

app = Flask(__name__)
CORS(app)

# Load the fine-tuned model and tokenizer
model_path = "./results"  # Path to your fine-tuned model
# Use device_map to split the model across GPUs
model = LlamaForCausalLM.from_pretrained(
    "./results",
    device_map="auto",  # Automatically map parts of the model to available devices
    torch_dtype=torch.float16,  # Use FP16 to reduce memory usage
    offload_folder="./offload"  # Directory for CPU/disk offloading
)
tokenizer = AutoTokenizer.from_pretrained("./results", trust_remote_code=True)

def clean_response(text):
    """Clean up the model's response text."""
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove any random sequences of uppercase letters, digits, or special characters at the end
    text = re.sub(r'[\W\d_]+$', '', text)
    return text.strip()

@app.route('/generate_response_text', methods=['POST'])
def generate_response_text():
    data = request.json
    input_text = data.get("text", "")
    prompt = "Imagine you're a restaurant employee, responding to the following customer inquiry: "
    full_prompt = prompt + input_text
    
    if input_text:
        try:
            # Tokenize the input text and move it to the model's device
            inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)

            # Generate the response with controlled settings
            output = model.generate(
                **inputs,
                max_new_tokens=30,
                do_sample=True,
                top_k=50,
                top_p=0.95,
                temperature=0.7,
                repetition_penalty=1.5
            )

            # Decode and clean up the generated response
            response = tokenizer.decode(output[0], skip_special_tokens=True)
            cleaned_response = clean_response(response)

            return jsonify({"response_text": cleaned_response})
        except Exception as e:
            print("Error with model generation:", e)
            return jsonify({"error": f"Model generation error: {str(e)}"}), 500
    else:
        return jsonify({"error": "No text provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

