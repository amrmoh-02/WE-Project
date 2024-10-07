import sqlite3
import json
from flask import Flask, request, jsonify
import google.generativeai as genai
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

genai.configure(api_key='AIzaSyDyatZawYWwez_enTAP9pUfNka9p8nTTLE')
model = genai.GenerativeModel('gemini-pro')

# Function to initialize the database and create the table if not exists
def init_db():
    conn = sqlite3.connect('business_model.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS canvas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            key_partners TEXT,
            key_activities TEXT,
            key_resources TEXT,
            value_propositions TEXT,
            customer_segments TEXT,
            channels TEXT,
            customer_relationships TEXT,
            revenue_streams TEXT,
            cost_structure TEXT,
            competitive_advantage TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database when the app starts
init_db()

@app.route('/chat', methods=['POST'])
def generate_business_model_canvas():
    description = request.form['description']

    prompt = f"""Generate a Business Model Canvas for the following business idea: {description}
    Include these sections: Key Partners, Key Activities, Key Resources, Value Propositions, 
    Customer Segments, Channels, Customer Relationships, Revenue Streams, Cost Structure, 
    Competitive Advantage"""

    # Send the prompt to the AI model and get the response
    response = model.generate_content(prompt)
    answer = response.text

    # Log the raw response for debugging purposes
    print("Raw response from the AI model:", answer)

    # Manually parse the generated response to extract each section
    sections = {}
    try:
        # Extract each section manually based on markers
        sections['key_partners'] = extract_section(answer, 'Key Partners')
        sections['key_activities'] = extract_section(answer, 'Key Activities')
        sections['key_resources'] = extract_section(answer, 'Key Resources')
        sections['value_propositions'] = extract_section(answer, 'Value Propositions')
        sections['customer_segments'] = extract_section(answer, 'Customer Segments')
        sections['channels'] = extract_section(answer, 'Channels')
        sections['customer_relationships'] = extract_section(answer, 'Customer Relationships')
        sections['revenue_streams'] = extract_section(answer, 'Revenue Streams')
        sections['cost_structure'] = extract_section(answer, 'Cost Structure')
        sections['competitive_advantage'] = extract_section(answer, 'Competitive Advantage')

        # Save to SQLite database
        conn = sqlite3.connect('business_model.db')
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO canvas (
                            description, key_partners, key_activities, key_resources,
                            value_propositions, customer_segments, channels,
                            customer_relationships, revenue_streams, cost_structure, competitive_advantage
                          ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (description, sections['key_partners'], sections['key_activities'], 
                        sections['key_resources'], sections['value_propositions'], sections['customer_segments'], 
                        sections['channels'], sections['customer_relationships'], sections['revenue_streams'], 
                        sections['cost_structure'], sections['competitive_advantage']))
        conn.commit()
        conn.close()

        return jsonify({'canvas': sections})
    
    except Exception as e:
        print("Error processing response:", e)
        return jsonify({'error': 'Failed to parse the response'}), 500


# Helper function to extract sections from the generated text
def extract_section(text, section_name):
    try:
        # Find the section and extract text until the next section starts
        start_marker = f"**{section_name}:**"
        end_marker = "**"  # The next section starts with **

        start_index = text.find(start_marker)
        if start_index == -1:
            return ''

        # Find the end of the section (next "**")
        end_index = text.find(end_marker, start_index + len(start_marker))
        if end_index == -1:
            end_index = len(text)  # If this is the last section

        return text[start_index + len(start_marker):end_index].strip()
    except Exception as e:
        print(f"Error extracting section {section_name}: {e}")
        return ''


@app.route('/canvas/<int:id>', methods=['GET'])
def get_canvas(id):
    conn = sqlite3.connect('business_model.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM canvas WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Create a dictionary from the database row
        canvas_data = {
            'description': row[1],
            'key_partners': row[2],
            'key_activities': row[3],
            'key_resources': row[4],
            'value_propositions': row[5],
            'customer_segments': row[6],
            'channels': row[7],
            'customer_relationships': row[8],
            'revenue_streams': row[9],
            'cost_structure': row[10],
            'competitive_advantage': row[11]
        }
        return jsonify({'canvas': canvas_data})
    else:
        return jsonify({'error': 'Canvas not found'}), 404


if __name__ == '__main__':
    app.run(debug=True)
