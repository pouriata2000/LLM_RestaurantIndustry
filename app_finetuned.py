import os
import re
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import LlamaForCausalLM, AutoTokenizer
import openai
import json
import re
import nltk
import time
from nltk.stem import WordNetLemmatizer

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

app = Flask(__name__)
CORS(app)

lemmatizer = WordNetLemmatizer()

def normalize_item_name(item_name):
    """Normalize the item name by converting it to lowercase and lemmatizing."""
    if not item_name or not isinstance(item_name, str):
        print("Invalid item name:", item_name)
        return ""
    
    try:
        # Convert to lowercase and lemmatize to handle plural forms
        normalized_name = lemmatizer.lemmatize(item_name.lower().strip())
        if not normalized_name:  # If lemmatization fails
            print(f"Lemmatization returned empty for: {item_name}")
            return item_name.lower().strip()  # Return the original, lowercase version as fallback
        return normalized_name
    except Exception as e:
        print(f"Error normalizing item name '{item_name}': {e}")
        return item_name.lower().strip()  # Return the original, lowercase version as fallback



openai.api_key = os.getenv("OPENAI_API_KEY")

# Load database.json file
DATABASE_FILE = "database.json"
if not os.path.exists(DATABASE_FILE):
    raise FileNotFoundError(f"{DATABASE_FILE} not found in the current directory.")

with open(DATABASE_FILE, "r") as f:
    database = json.load(f)

# Load the fine-tuned model and tokenizer
model_path = "./results"  # Path to your fine-tuned model
model = LlamaForCausalLM.from_pretrained(
    model_path,
    device_map="auto",  # Automatically map parts of the model to devices
    torch_dtype=torch.float16  # Use FP16 for memory efficiency
)
tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)


def clean_response(text):
    """Clean up the model's response text."""
    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    # Remove any text following specific characters (=, -, ~, ") and the characters themselves
    text = re.split(r'[=\-~"]', text)[0]
    # Remove any random sequences of uppercase letters, digits, or special characters at the end
    text = re.sub(r'[\W\d_]+$', '', text)
    # Remove extra spaces and trim the text
    return text.strip()

@app.route('/generate_response_text', methods=['POST'])
def generate_response_text():
    start_time = time.time()


    data = request.json
    input_text = data.get("text", "")
    prompt = "Imagine you're a restaurant employee, responding to the following customer inquiry: "
    full_prompt =prompt + input_text
    

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

            end_time = time.time()  # End the timer if no input is provided
            elapsed_time = end_time - start_time  # Calculate elapsed time
            print(f"Function execution time (no input): {elapsed_time:.4f} seconds")  # Log the result	
            
            return jsonify({"response_text": cleaned_response})
        except Exception as e:
            print("Error with model generation:", e)
            return jsonify({"error": f"Model generation error: {str(e)}"}), 500
    else:
       return jsonify({"error": "No text provided"}), 400
    


@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    try:
        data = request.json
        input_text = data.get("text", "")
        if not input_text:
            print("No text provided")
            return jsonify({"error": "No text provided"}), 400
        
        prompt = (
            "Summarize this customer's inquiry suitable for a restaurant employee's use. "
            "If it's an order, write it in an order format with a list including user's name and items names "
            "with quantities in json format with keys of json being 'Customer' and 'Items'."
        )
        
        # Call ChatGPT API
        chat_completion = openai.chat.completions.create(
            messages=[{"role": "user", "content": prompt + input_text}],
            model="gpt-3.5-turbo",
            max_tokens=150
        )
        summary = chat_completion.choices[0].message.content.strip()
        print("ChatGPT Response:", summary)

        # Parse ChatGPT response
        try:
            summary_json = json.loads(summary)
            print("Parsed Summary:", summary_json)

            # Validate Items
            items = summary_json.get("Items", [])
            if isinstance(items, dict):
                # Convert dictionary to list of objects
                items = [{"name": name, "quantity": quantity} for name, quantity in items.items()]
            elif not isinstance(items, list):
                print(f"Invalid Items structure: {items}")
                return jsonify({"error": "Invalid Items format in ChatGPT response."}), 500

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing or validating ChatGPT response: {e}")
            return jsonify({"error": "Failed to parse or validate ChatGPT response."}), 500

        # Extract Customer and Match Items
        customer_name = summary_json.get("Customer", "Not provided.")
        matched_items = {}
        for item in items:
            item_name = item.get("name", "")
            normalized_name = normalize_item_name(item_name)
            quantity = item.get("quantity", 1)
            print(f"Processing item: {item_name} (normalized: {normalized_name}), Quantity: {quantity}")

            # Match in the database
            if isinstance(database.get(normalized_name), dict):
                matched_items[item_name] = {
                    "quantity": quantity,
                    "price": database[normalized_name]["price"],
                    "description": database[normalized_name]["description"],
                    "total_price": quantity * database[normalized_name]["price"]
                }
            else:
                matched_items[item_name] = {
                    "quantity": quantity,
                    "price": "Not available",
                    "description": "Not found in database.",
                    "total_price": "Not available"
                }
        
        print("Matched Items:", matched_items)

        # Create response
        response = {
            "Customer": customer_name,
            "Order": matched_items
        }
        return jsonify(response)

    except Exception as e:
        print(f"Error in /generate_summary endpoint: {e}")
        return jsonify({"error": f"Internal server error: {e}"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

