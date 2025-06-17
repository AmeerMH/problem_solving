# LogesTechs Chatbot API with Data Collection

This is a Flask-based API for a LogesTechs chatbot that provides shipment tracking and customer support services. The chatbot uses Google's Generative AI (Gemini) to provide intelligent responses and includes comprehensive data collection for future model training.

## Features

- **Shipment Tracking**: Track packages using tracking numbers
- **Customer Support**: Answer questions about LogesTechs services
- **Conversation History**: Maintain conversation context
- **Token Usage Tracking**: Monitor API usage and costs
- **Token Usage Analytics**: Historical analysis and cost monitoring
- **Arabic Language Support**: Full support for Arabic text
- **Data Collection**: Collect training data from three extraction stages
- **Firebase Integration**: Store data in Firebase Firestore (with local fallback)

## Data Collection Stages

The chatbot collects training data from three key stages:

### 1. `extract_intent_stage_one`
- **Purpose**: Binary classification (yes/no) to determine if user query is related to company services
- **Input**: User prompt
- **Output**: "yes" or "no"
- **Use Case**: Filter relevant vs irrelevant queries

### 2. `extract_intent`
- **Purpose**: Multi-class intent classification
- **Input**: User prompt
- **Output**: Intent category (shipment_tracking, order_status, tracking_number, etc.)
- **Use Case**: Route queries to appropriate handlers

### 3. `extract_tracking_number`
- **Purpose**: Extract tracking numbers from user messages
- **Input**: User prompt
- **Output**: Tracking number or "NO_TRACKING_NUMBER"
- **Use Case**: Identify and extract tracking information

## API Endpoints

### `GET /`
Simple health check endpoint that returns "Hello"

### `POST /chat`
Send a message to the chatbot and get a response.

**Request Body:**
```json
{
  "prompt": "Your message here",
  "company_id": 410
}
```

**Response:**
```json
{
  "response": "Chatbot response"
}
```

**Note:** `company_id` is optional and defaults to 410 if not provided.

### `GET /get_conversation_history`
Get the current conversation history.

**Response:**
```json
{
  "history": [
    {
      "role": "user",
      "parts": [{"text": "User message"}]
    },
    {
      "role": "model", 
      "parts": [{"text": "Bot response"}]
    }
  ]
}
```

### `GET /get_token_usage`
Get current token usage statistics and estimated costs.

**Response:**
```json
{
  "token_usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "estimated_cost": {
    "prompt_cost": 0.0,
    "completion_cost": 0.0,
    "total_cost": 0.0
  }
}
```

### `GET /get_token_history`
Get historical token usage data from Firebase or local storage.

**Query Parameters:**
- `limit` (optional): Maximum number of records to return (default: 100)
- `days` (optional): Filter records from last N days
- `company_id` (optional): Filter data by specific company ID

**Response:**
```json
{
  "success": true,
  "source": "firebase",
  "data": [
    {
      "prompt_tokens": 45,
      "completion_tokens": 127,
      "total_tokens": 172,
      "timestamp": "2025-06-17T08:58:51.756157",
      "company_id": 410,
      "estimated_cost": {
        "prompt_cost": 0.00045,
        "completion_cost": 0.00254,
        "total_cost": 0.00299
      },
      "model": "gemini-2.0-flash-exp",
      "session_total_tokens": 291
    }
  ],
  "total_records": 1
}
```

### `GET /get_token_analytics`
Get analytics and summary of token usage.

**Query Parameters:**
- `days` (optional): Period for analytics in days (default: 30)
- `company_id` (optional): Filter data by specific company ID

**Response:**
```json
{
  "success": true,
  "source": "firebase",
  "period_days": 7,
  "analytics": {
    "total_requests": 2,
    "total_tokens": 291,
    "total_cost": 0.00547,
    "average_tokens_per_request": 145.5,
    "average_cost_per_request": 0.002735,
    "total_prompt_tokens": 119,
    "total_completion_tokens": 172,
    "prompt_completion_ratio": 0.69
  }
}
```

### `POST /reset`
Reset the conversation history.

**Request Body (optional):**
```json
{
  "company_id": 410
}
```

**Response:**
```json
{
  "message": "Conversation reset"
}
```

**Note:** `company_id` is optional and defaults to 410 if not provided.

### `GET /get_training_data`
Get collected training data from Firebase or local storage.

**Query Parameters:**
- `stage` (optional): Specific stage to retrieve ("extract_intent", "extract_intent_stage_one", "extract_tracking_number", or "all")
- `limit` (optional): Maximum number of records to return (default: 100)
- `company_id` (optional): Filter data by specific company ID

**Response:**
```json
{
  "success": true,
  "source": "local",
  "data": {
    "extract_intent": [...],
    "extract_intent_stage_one": [...],
    "extract_tracking_number": [...]
  },
  "total_records": 8
}
```

### `GET /export_training_data`
Export training data as JSON response.

**Query Parameters:**
- `stage` (optional): Specific stage to export ("extract_intent", "extract_intent_stage_one", "extract_tracking_number", or "all")
- `company_id` (optional): Filter data by specific company ID

**Response:**
```json
{
  "success": true,
  "source": "local",
  "filename": "training_data_all_20250617_084648.json",
  "data": {...},
  "total_records": 8
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Firebase Setup (Optional):
   - Place your Firebase service account key file in the project root
   - Update the filename in `chatbot.py` if needed
   - If Firebase is not available, data will be stored locally

3. Run the application:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

## Dependencies

- `flask==2.3.3` - Web framework
- `google-generativeai==0.3.2` - Google Generative AI SDK
- `tiktoken==0.5.2` - Token counting
- `requests==2.31.0` - HTTP requests
- `gunicorn==21.2.0` - WSGI server (for production)
- `firebase-admin==6.4.0` - Firebase Admin SDK

## Data Collection Structure

Each collected data point includes:

### Training Data:
```json
{
  "stage": "extract_intent_stage_one",
  "prompt": "أريد تتبع شحنتي",
  "response": "yes",
  "timestamp": "2025-06-17T08:46:40.242822",
  "company_id": 410,
  "metadata": {
    "instruction": "System instruction used",
    "model": "gemini-2.0-flash-exp",
    "temperature": 0,
    "max_tokens": 10,
    "expected_values": ["yes", "no"]
  }
}
```

### Token Usage Data:
```json
{
  "prompt_tokens": 45,
  "completion_tokens": 127,
  "total_tokens": 172,
  "timestamp": "2025-06-17T08:58:51.756157",
  "company_id": 410,
  "estimated_cost": {
    "prompt_cost": 0.00045,
    "completion_cost": 0.00254,
    "total_cost": 0.00299
  },
  "model": "gemini-2.0-flash-exp",
  "session_total_tokens": 291
}
```

## Local Data Storage

When Firebase is not available, data is stored locally in JSON files:
- `training_data/training_data_extract_intent.json`
- `training_data/training_data_extract_intent_stage_one.json`
- `training_data/training_data_extract_tracking_number.json`

## Usage Examples

### Track a shipment:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "أريد تتبع شحنتي برقم 100298037303"}'
```

### Ask about services:
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "ما هي خدماتكم؟"}'
```

### Get training data:
```bash
curl "http://localhost:5000/get_training_data?stage=all&limit=50"
```

### Export training data:
```bash
curl "http://localhost:5000/export_training_data?stage=extract_intent"
```

## Model Training Data

The collected data can be used for:

1. **Fine-tuning existing models** on specific tasks
2. **Training custom classifiers** for intent recognition
3. **Improving tracking number extraction** accuracy
4. **Analyzing user behavior** and query patterns
5. **Creating synthetic training data** for new features

## Changes Made

This version has been updated to use Google's Generative AI API directly instead of Vertex AI:

- Removed Vertex AI dependencies
- Updated to use `google-generativeai` package
- Configured with API key authentication
- Maintained all original functionality
- Updated conversation history format to be compatible with the new API
- Added comprehensive data collection for three extraction stages
- Integrated Firebase Firestore with local fallback storage
- Added endpoints for data retrieval and export 