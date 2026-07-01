from flask import Flask, render_template, request, redirect, jsonify
import json, os

app = Flask(__name__)
DATA_FILE = 'data.json'
OWNER_ID = 1195685896050180146

# --- Pomocnicze funkcje ---

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "admins":    list(data.get("admins", [OWNER_ID])),
                "mods":      list(data.get("mods", [])),
                "whitelist": list(data.get("whitelist", [])),
                "targets":   list(data.get("targets", []))
            }
    return {"admins": [OWNER_ID], "mods": [], "whitelist": [], "targets": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

# --- Strony ---

@app.route('/')
def panel():
    data = load_data()
    return render_template('panel.html', data=data)

# Dodaj do listy (mods / admins / whitelist / targets)
@app.route('/add/<lista>', methods=['POST'])
def add(lista):
    user_id_str = request.form.get('user_id', '').strip()
    if not user_id_str.isdigit():
        return redirect('/')
    user_id = int(user_id_str)
    data = load_data()
    if lista in data and user_id not in data[lista]:
        data[lista].append(user_id)
        save_data(data)
    return redirect('/')

# Usuń z listy
@app.route('/remove/<lista>/<int:user_id>')
def remove(lista, user_id):
    data = load_data()
    if lista in data and user_id in data[lista]:
        data[lista].remove(user_id)
        save_data(data)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)