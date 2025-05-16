# LogesTechs Shipment Info Extraction API

This API is designed to extract structured shipment-related information from user messages written in Arabic or English using Google Gemini (Generative AI). It is built using Flask and integrates with Google's Vertex AI.

## 📦 Features

- Extracts structured shipment data from free-form Arabic or English text.
- Returns data in a fixed JSON structure.
- Uses Google Gemini 2.0 Flash model via Vertex AI.
- Automatically normalizes Arabic text for better consistency.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Cloud project with Vertex AI enabled
- Service account with necessary permissions
- Required Python packages (see below)

### Installation



1. **Install dependencies**
   ```bash
   pip install flask google-generativeai
   ```

1. **Set up Google credentials**
   - Authenticate your environment to use Vertex AI (e.g., via `gcloud auth` or service account JSON key).

---

## 🔧 Configuration

Update this section of the code in `extract_shipment_info()` with your Google Cloud details:

```python
client = genai.Client(
    vertexai=True,
    project="logestechs-443407",  # Replace with your GCP project ID
    location="us-west4"
)
```

---

## 🧠 API Endpoints

### `GET /`

Health check or welcome route.

**Response:**
```json
"Hello, World!"
```

---

### `POST /extract_shipment`

Extracts structured shipment info from user text.

**Request Body:**
```json
{
  "prompt": "أنا أريد توصيل طرد إلى محمد في رام الله، الوزن 2 كغم والدفع نقدي"
}
```

**Response:**
Returns structured JSON with shipment info:
```json
{
  "recipient_info": {
    "recipient_name": "محمد",
    "recipient_phone_number": null,
    "recipient_address": "رام الله",
    ...
  },
  ...
}
```

If any data isn't provided in the prompt, the fields are returned as `null`.

---

## 📌 Notes

- Handles Arabic and English inputs.
- Returns full JSON structure with missing fields set to `null`.
- Assumes messages are user-generated and may contain incomplete data.

---

## 🛠 Development

Run locally with:

```bash
python app.py
```

Access the API at: `http://127.0.0.1:5000`

---

## 🧪 Example cURL

```bash
curl -X POST http://localhost:5000/extract_shipment \
     -H "Content-Type: application/json" \
     -d '{"prompt": "الرجاء توصيل الطرد إلى خالد في نابلس"}'
```

---

## 📄 License

MIT License

