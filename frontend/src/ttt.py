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
            print(f"Function execution time (no input): {elapsed_time:.4f} seconds")  # Log the resul>
            
            return jsonify({"response_text": cleaned_response})
        except Exception as e:
            print("Error with model generation:", e)
            return jsonify({"error": f"Model generation error: {str(e)}"}), 500
    else:
       return jsonify({"error": "No text provided"}), 400
    

