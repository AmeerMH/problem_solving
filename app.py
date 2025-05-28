from flask import Flask, request, jsonify
from vertexai.preview.language_models import TextGenerationModel
import unicodedata
import json

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text)

def extract_shipment_info(prompt: str) -> str:
    from vertexai.preview.generative_models import GenerativeModel

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

    # Configure the model
    model = GenerativeModel("gemini-1.5-pro")  # أو حسب المتاح

    response = model.generate_content(
        [system_instruction, prompt],
        generation_config={"temperature": 0.2, "max_output_tokens": 1024}
    )

    return response.text

@app.route('/extract_shipment', methods=['POST'])
def extract_shipment():
    data = request.get_json()
    if 'prompt' not in data:
        return jsonify({"error": "Prompt is required"}), 400

    prompt = data['prompt']
    extracted_info = extract_shipment_info(prompt)

    extracted_info_clean = extracted_info.strip('```json\n').strip('```').replace('\\n', '').strip()

    try:
        extracted_info_json = json.loads(extracted_info_clean)
    except json.JSONDecodeError:
        return jsonify({"error": "Failed to parse extracted information", "raw": extracted_info}), 500

    return jsonify(extracted_info_json)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
