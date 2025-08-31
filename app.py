import re
from flask import Flask, request, jsonify, render_template_string
import os

app = Flask(__name__)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(app.root_path, "rtr1_config.txt")

# HTML for the frontend, served by Flask
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cisco Config Editor</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        .config-group { margin-bottom: 20px; border: 1px solid #ccc; padding: 10px; border-radius: 5px; }
        .config-item { margin-bottom: 10px; }
        label { font-weight: bold; display: block; margin-bottom: 5px; }
        input[type="text"] { width: 300px; padding: 5px; border-radius: 3px; border: 1px solid #ccc; }
        button { padding: 10px 15px; cursor: pointer; background-color: #007bff; color: white; border: none; border-radius: 5px; }
    </style>
</head>
<body>
    <h2>Cisco Hostname and Banner Editor</h2>
    <div id="config-ui"></div>
    <button onclick="saveConfig()">Save Changes</button>

    <script>
        async function fetchAndRenderConfig() {
            try {
                const response = await fetch('/api/get_parsed_config');
                const data = await response.json();
                renderUI(data);
            } catch (error) {
                console.error('Error fetching config:', error);
                alert('Could not load configuration file.');
            }
        }

        function renderUI(data) {
            const container = document.getElementById('config-ui');
            container.innerHTML = ''; // Clear existing UI

            // Hostname
            const hostnameDiv = document.createElement('div');
            hostnameDiv.className = 'config-group';
            hostnameDiv.innerHTML = `<h3>Hostname</h3><div class="config-item"><label for="hostname">Hostname</label><input type="text" id="hostname" value="${data.hostname}"></div>`;
            container.appendChild(hostnameDiv);

            // MOTD Banner
            const motdDiv = document.createElement('div');
            motdDiv.className = 'config-group';
            motdDiv.innerHTML = `<h3>Banner</h3><div class="config-item"><label for="motd_banner">MOTD Text</label><input type="text" id="motd_banner" value="${data.motd}"></div>`;
            container.appendChild(motdDiv);
        }

        async function saveConfig() {
            const hostname = document.getElementById('hostname').value;
            const motd_banner = document.getElementById('motd_banner').value;

            const updatedData = {
                hostname: hostname,
                motd: motd_banner
            };

            try {
                const response = await fetch('/api/save_parsed_config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                });
                if (response.ok) {
                    alert('Configuration saved successfully!');
                } else {
                    alert('Failed to save configuration.');
                }
            } catch (error) {
                console.error('Error saving config:', error);
                alert('An error occurred while saving.');
            }
        }

        window.onload = fetchAndRenderConfig;
    </script>
</body>
</html>
"""

# Regex patterns to find specific configuration lines
HOSTNAME_PATTERN = re.compile(r'^hostname (\S+)', re.MULTILINE)
MOTD_PATTERN = re.compile(r'^banner motd \^C\s*(.*?)\s*\^C', re.DOTALL | re.MULTILINE)

def parse_cisco_config(file_path):
    """Parses the config file for hostname and banner."""
    config_data = {
        "hostname": "",
        "motd": ""
    }
    
    with open(file_path, 'r') as f:
        file_content = f.read()

    match_hostname = HOSTNAME_PATTERN.search(file_content)
    if match_hostname:
        config_data['hostname'] = match_hostname.group(1).strip()
    
    match_motd = MOTD_PATTERN.search(file_content)
    if match_motd:
        config_data['motd'] = match_motd.group(1).strip()
    
    return config_data

def reassemble_cisco_config(data, original_content):
    """Reassembles the config file with updated values, replacing in place."""
    
    # Replace hostname
    new_content = HOSTNAME_PATTERN.sub(f'hostname {data["hostname"]}', original_content)
    
    # Replace banner
    new_content = MOTD_PATTERN.sub(f'banner motd ^C\n{data["motd"]}\n^C', new_content)
    
    return new_content

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/api/get_parsed_config', methods=['GET'])
def get_parsed_config():
    if not os.path.exists(CONFIG_FILE_PATH):
        return jsonify({"error": "Configuration file not found"}), 404
    parsed_data = parse_cisco_config(CONFIG_FILE_PATH)
    return jsonify(parsed_data)

@app.route('/api/save_parsed_config', methods=['POST'])
def save_parsed_config():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid request"}), 400

    try:
        original_content = ""
        if os.path.exists(CONFIG_FILE_PATH):
            with open(CONFIG_FILE_PATH, 'r') as f:
                original_content = f.read()
        
        reassembled_config = reassemble_cisco_config(data, original_content)
        
        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write(reassembled_config)
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"File '{CONFIG_FILE_PATH}' not found. Creating a default file.")
        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write("hostname rtr1\n!\n! some config\n!\nbanner motd ^C\nTest Banner\n^C\n")
            
    app.run(debug=True)