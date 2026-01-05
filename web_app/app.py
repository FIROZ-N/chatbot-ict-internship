"""
Updated Flask Backend with Button Support
Save as: app.py
"""

from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Rasa server URL
RASA_SERVER_URL = "http://localhost:5005/webhooks/rest/webhook"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')
        
        if not user_message:
            return jsonify({"reply": "Please enter a message."}), 400
        
        # Send message to Rasa
        payload = {
            "sender": "user",  # You can use session ID here
            "message": user_message
        }
        
        response = requests.post(RASA_SERVER_URL, json=payload, timeout=10)
        response.raise_for_status()
        
        rasa_responses = response.json()
        
        # Rasa returns a list of responses
        if isinstance(rasa_responses, list) and len(rasa_responses) > 0:
            # Format each response
            formatted_responses = []
            
            for rasa_response in rasa_responses:
                formatted_response = {}
                
                # Get text (handle both 'text' and 'reply' fields)
                if 'text' in rasa_response:
                    formatted_response['text'] = rasa_response['text']
                elif 'reply' in rasa_response:
                    formatted_response['text'] = rasa_response['reply']
                else:
                    formatted_response['text'] = ''
                
                # Get buttons if they exist
                if 'buttons' in rasa_response:
                    formatted_response['buttons'] = rasa_response['buttons']
                
                # Get images if they exist
                if 'image' in rasa_response:
                    formatted_response['image'] = rasa_response['image']
                
                # Get custom data if it exists
                if 'custom' in rasa_response:
                    formatted_response['custom'] = rasa_response['custom']
                
                formatted_responses.append(formatted_response)
            
            # Return array of responses for frontend to handle
            return jsonify(formatted_responses)
        
        else:
            return jsonify([{"text": "I didn't understand that. Could you rephrase?"}])
    
    except requests.exceptions.ConnectionError:
        return jsonify([{
            "text": "⚠️ Cannot connect to Rasa server. Please make sure Rasa is running on port 5005."
        }]), 500
    
    except requests.exceptions.Timeout:
        return jsonify([{
            "text": "⚠️ Request timed out. Please try again."
        }]), 500
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([{
            "text": "⚠️ An error occurred. Please try again."
        }]), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
