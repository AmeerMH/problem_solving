from flask import Flask, request, jsonify
import google.generativeai as genai
import unicodedata
import os

genai.configure(api_key=os.getenv("GENAI_API_KEY"))

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text)

def extract_shipment_info(prompt: str) -> str:
    system_instruction = """
    You are a helpful assistant for LogesTechs company. Your job is to extract shipment-related information 
    from user messages written in Arabic or English.

    Your goal is to extract and return the following structured data (if mentioned). If a field is not present, set its value to null.

    Respond **only** in the following JSON format:

    {
        "recipient_info": {
            "recipient_name": null,
            "recipient_phone_number": null,
            "recipient_address": null,
            "address_description": null,
            "location_link": null,
            "national_address": null
        },
        "payment_info": {
            "payment_method": null,
            "promo_offer": null,
            "total_inclusive_of_delivery": null,
            "collection_method": null,
            "insurance_activation": null
        },
        "service_info": {
            "service_type": null,
            "shipment_number": null,
            "expected_delivery_date": null,
            "expected_collection_date": null
        },
        "package_details": {
            "item_count": null,
            "package_type": null,
            "notes": null,
            "package_contents": null,
            "package_weight": null,
            "package_height": null,
            "package_length": null,
            "package_width": null
        }
    }

    Always return this full JSON with null values for anything not mentioned in the input.
    """

    prompt = normalize_text(prompt)

    model = genai.GenerativeModel("gemini-1.0-pro")  

    response = model.generate_content([system_instruction, prompt])

    return response.text

@app.route('/extract_shipment', methods=['POST'])
def extract_shipment():
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        extracted_info = extract_shipment_info(prompt)
        return jsonify({"response": extracted_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
