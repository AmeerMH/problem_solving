from flask import Flask, request, jsonify
from chatbot import Chatbot  # assuming your class is in chatbot.py
from firebase_admin import firestore

app = Flask(__name__)
bot = Chatbot()

@app.route('/')
def hello():
    return "Hello"
@app.route('/reset', methods=['POST'])
def reset():
    data = request.get_json() or {}
    company_id = data.get("company_id", 410)  # Default to 410 if not provided
    
    # Set company ID for the chatbot
    bot.set_company_id(company_id)
    
    bot.reset_conversation()
    return jsonify({"message": "Conversation reset"})
    
@app.route('/get_conversation_history', methods=['GET'])
def get_conversation_history():
    history = bot.get_conversation_history()
    return jsonify({"history": history})

@app.route('/get_token_usage', methods=['GET'])
def get_token_usage():
    token_stats = bot.get_token_count()
    return jsonify({
        "token_usage": token_stats,
        "estimated_cost": {
            "prompt_cost": (token_stats["prompt_tokens"] * 0.00001),  # $0.01 per 1K tokens
            "completion_cost": (token_stats["completion_tokens"] * 0.00002),  # $0.02 per 1K tokens
            "total_cost": (token_stats["prompt_tokens"] * 0.00001) + (token_stats["completion_tokens"] * 0.00002)
        }
    })

@app.route('/get_token_history', methods=['GET'])
def get_token_history():
    """Get historical token usage data from Firebase or local storage"""
    try:
        limit = request.args.get('limit', 100, type=int)  # Default limit of 100 records
        days = request.args.get('days', None, type=int)  # Optional: filter by days
        company_id = request.args.get('company_id', None, type=int)  # Optional company filter
        
        data = []
        
        # Try Firebase first
        if bot.firebase_initialized:
            try:
                query = bot.db.collection("token_usage").order_by("timestamp", direction=firestore.Query.DESCENDING)
                
                # Add company filter if specified
                if company_id:
                    query = query.where("company_id", "==", company_id)
                
                if days:
                    # Filter by days if specified
                    from datetime import datetime, timedelta
                    cutoff_date = datetime.now() - timedelta(days=days)
                    query = query.where("timestamp", ">=", cutoff_date.isoformat())
                
                docs = query.limit(limit).stream()
                data = [doc.to_dict() for doc in docs]
                
                return jsonify({
                    "success": True,
                    "source": "firebase",
                    "data": data,
                    "total_records": len(data)
                })
                
            except Exception as e:
                print(f"Firebase token history retrieval failed: {e}")
        
        # Fallback to local storage
        import os
        import json
        
        filename = "training_data/token_usage.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                
            # Filter by company_id if specified
            if company_id:
                all_data = [record for record in all_data if record.get('company_id') == company_id]
                
            # Sort by timestamp (newest first)
            all_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Apply limit
            data = all_data[:limit]
            
            # Apply days filter if specified
            if days:
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=days)
                data = [record for record in data if record.get('timestamp', '') >= cutoff_date.isoformat()]
        
        return jsonify({
            "success": True,
            "source": "local",
            "data": data,
            "total_records": len(data)
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve token history: {str(e)}"}), 500

@app.route('/get_token_analytics', methods=['GET'])
def get_token_analytics():
    """Get analytics and summary of token usage"""
    try:
        days = request.args.get('days', 30, type=int)  # Default to 30 days
        company_id = request.args.get('company_id', None, type=int)  # Optional company filter
        
        # Try Firebase first
        if bot.firebase_initialized:
            try:
                from datetime import datetime, timedelta
                cutoff_date = datetime.now() - timedelta(days=days)
                
                query = bot.db.collection("token_usage").where("timestamp", ">=", cutoff_date.isoformat())
                
                # Add company filter if specified
                if company_id:
                    query = query.where("company_id", "==", company_id)
                
                docs = query.stream()
                data = [doc.to_dict() for doc in docs]
                
                analytics = calculate_token_analytics(data)
                
                return jsonify({
                    "success": True,
                    "source": "firebase",
                    "period_days": days,
                    "analytics": analytics
                })
                
            except Exception as e:
                print(f"Firebase token analytics failed: {e}")
        
        # Fallback to local storage
        import os
        import json
        
        filename = "training_data/token_usage.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                
            # Filter by company_id if specified
            if company_id:
                all_data = [record for record in all_data if record.get('company_id') == company_id]
                
            # Filter by days
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            data = [record for record in all_data if record.get('timestamp', '') >= cutoff_date.isoformat()]
            
            analytics = calculate_token_analytics(data)
            
            return jsonify({
                "success": True,
                "source": "local",
                "period_days": days,
                "analytics": analytics
            })
        
        return jsonify({
            "success": True,
            "source": "none",
            "period_days": days,
            "analytics": {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0,
                "average_tokens_per_request": 0,
                "average_cost_per_request": 0
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve token analytics: {str(e)}"}), 500

def calculate_token_analytics(data):
    """Calculate analytics from token usage data"""
    if not data:
        return {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "average_tokens_per_request": 0,
            "average_cost_per_request": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0
        }
    
    total_requests = len(data)
    total_tokens = sum(record.get('total_tokens', 0) for record in data)
    total_cost = sum(record.get('estimated_cost', {}).get('total_cost', 0) for record in data)
    total_prompt_tokens = sum(record.get('prompt_tokens', 0) for record in data)
    total_completion_tokens = sum(record.get('completion_tokens', 0) for record in data)
    
    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost": round(total_cost, 6),
        "average_tokens_per_request": round(total_tokens / total_requests, 2) if total_requests > 0 else 0,
        "average_cost_per_request": round(total_cost / total_requests, 6) if total_requests > 0 else 0,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "prompt_completion_ratio": round(total_prompt_tokens / total_completion_tokens, 2) if total_completion_tokens > 0 else 0
    }

@app.route('/get_training_data', methods=['GET'])
def get_training_data():
    """Get collected training data from Firebase or local storage"""
    try:
        stage = request.args.get('stage', 'all')  # Default to 'all' stages
        limit = request.args.get('limit', 100, type=int)  # Default limit of 100 records
        company_id = request.args.get('company_id', None, type=int)  # Optional company filter
        
        data = {}
        
        # Try Firebase first
        if bot.firebase_initialized:
            try:
                if stage == 'all':
                    # Get data from all stages
                    stages = ['extract_intent', 'extract_intent_stage_one', 'extract_tracking_number']
                    for stage_name in stages:
                        collection_name = f"training_data_{stage_name}"
                        query = bot.db.collection(collection_name)
                        
                        # Add company filter if specified
                        if company_id:
                            query = query.where("company_id", "==", company_id)
                        
                        docs = query.limit(limit).stream()
                        data[stage_name] = [doc.to_dict() for doc in docs]
                else:
                    # Get data from specific stage
                    collection_name = f"training_data_{stage}"
                    query = bot.db.collection(collection_name)
                    
                    # Add company filter if specified
                    if company_id:
                        query = query.where("company_id", "==", company_id)
                    
                    docs = query.limit(limit).stream()
                    data[stage] = [doc.to_dict() for doc in docs]
                
                return jsonify({
                    "success": True,
                    "source": "firebase",
                    "data": data,
                    "total_records": sum(len(records) for records in data.values())
                })
                
            except Exception as e:
                print(f"Firebase retrieval failed: {e}")
        
        # Fallback to local storage
        import os
        import json
        
        if stage == 'all':
            stages = ['extract_intent', 'extract_intent_stage_one', 'extract_tracking_number']
            for stage_name in stages:
                filename = f"training_data/training_data_{stage_name}.json"
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        stage_data = json.load(f)
                        
                        # Filter by company_id if specified
                        if company_id:
                            stage_data = [record for record in stage_data if record.get('company_id') == company_id]
                        
                        data[stage_name] = stage_data[:limit]  # Apply limit
                else:
                    data[stage_name] = []
        else:
            filename = f"training_data/training_data_{stage}.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    stage_data = json.load(f)
                    
                    # Filter by company_id if specified
                    if company_id:
                        stage_data = [record for record in stage_data if record.get('company_id') == company_id]
                    
                    data[stage] = stage_data[:limit]  # Apply limit
            else:
                data[stage] = []
        
        return jsonify({
            "success": True,
            "source": "local",
            "data": data,
            "total_records": sum(len(records) for records in data.values())
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve training data: {str(e)}"}), 500

@app.route('/export_training_data', methods=['GET'])
def export_training_data():
    """Export training data as JSON file"""
    try:
        stage = request.args.get('stage', 'all')
        
        data = {}
        source = "unknown"
        
        # Try Firebase first
        if bot.firebase_initialized:
            try:
                if stage == 'all':
                    stages = ['extract_intent', 'extract_intent_stage_one', 'extract_tracking_number']
                    for stage_name in stages:
                        collection_name = f"training_data_{stage_name}"
                        docs = bot.db.collection(collection_name).stream()
                        data[stage_name] = [doc.to_dict() for doc in docs]
                else:
                    collection_name = f"training_data_{stage}"
                    docs = bot.db.collection(collection_name).stream()
                    data[stage] = [doc.to_dict() for doc in docs]
                
                source = "firebase"
                
            except Exception as e:
                print(f"Firebase export failed: {e}")
        
        # Fallback to local storage
        if source == "unknown":
            import os
            import json
            
            if stage == 'all':
                stages = ['extract_intent', 'extract_intent_stage_one', 'extract_tracking_number']
                for stage_name in stages:
                    filename = f"training_data/training_data_{stage_name}.json"
                    if os.path.exists(filename):
                        with open(filename, 'r', encoding='utf-8') as f:
                            data[stage_name] = json.load(f)
                    else:
                        data[stage_name] = []
            else:
                filename = f"training_data/training_data_{stage}.json"
                if os.path.exists(filename):
                    with open(filename, 'r', encoding='utf-8') as f:
                        data[stage] = json.load(f)
                else:
                    data[stage] = []
            
            source = "local"
        
        # Create filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_{stage}_{timestamp}.json"
        
        return jsonify({
            "success": True,
            "source": source,
            "filename": filename,
            "data": data,
            "total_records": sum(len(records) for records in data.values())
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to export training data: {str(e)}"}), 500

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get("prompt")
    company_id = data.get("company_id", 410)  # Default to 410 if not provided
    
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    # Set company ID for the chatbot
    bot.set_company_id(company_id)
    
    response = bot.generate_response(prompt)
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)

