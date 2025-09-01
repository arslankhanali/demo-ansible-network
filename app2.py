import re
import os
import subprocess
from flask import Flask, request, jsonify, render_template_string

# Create a Flask web application instance.
app = Flask(__name__)

# Determine the absolute path of the directory where this script is located.
# This ensures that the application can find the config file regardless of
# the working directory from which it is started.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, "rtr1_config.txt")

# HTML for the front-end, embedded directly in the Python file.
# This includes all the HTML, CSS, and JavaScript for the user interface.
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cisco Config Editor</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 40px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        h2 { text-align: center; color: #333; }
        .config-group { margin-bottom: 20px; border: 1px solid #ddd; padding: 15px; border-radius: 6px; background-color: #fafafa; }
        .config-item { margin-bottom: 15px; }
        label { font-weight: bold; display: block; margin-bottom: 8px; color: #555; }
        input[type="text"], textarea { 
            width: 100%; 
            padding: 10px; 
            border-radius: 4px; 
            border: 1px solid #ccc; 
            box-sizing: border-box;
            resize: vertical;
        }
        button { 
            display: block; 
            width: 100%; 
            padding: 12px; 
            cursor: pointer; 
            background-color: #007bff; 
            color: white; 
            border: none; 
            border-radius: 6px; 
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        button:hover { background-color: #0056b3; }
        #message-box { 
            margin-top: 20px; 
            padding: 10px; 
            border-radius: 4px; 
            text-align: center;
            font-weight: bold;
        }
        .success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Cisco Hostname and Banner Editor</h2>
        <div id="config-ui"></div>
        <button onclick="saveConfig()">Save & Push to Git</button>
        <div id="message-box"></div>
    </div>

    <script>
        // Function to display a message to the user
        function showMessage(message, type) {
            const msgBox = document.getElementById('message-box');
            msgBox.textContent = message;
            msgBox.className = type;
            msgBox.style.display = 'block';
        }

        async function fetchAndRenderConfig() {
            try {
                const response = await fetch('/api/get_parsed_config');
                const data = await response.json();
                
                if (response.ok) {
                    renderUI(data);
                } else {
                    showMessage(data.error, 'error');
                }
            } catch (error) {
                console.error('Error fetching config:', error);
                showMessage('Could not load configuration file.', 'error');
            }
        }

        function renderUI(data) {
            const container = document.getElementById('config-ui');
            container.innerHTML = ''; // Clear existing UI

            // Hostname
            const hostnameDiv = document.createElement('div');
            hostnameDiv.className = 'config-group';
            hostnameDiv.innerHTML = `
                <h3>Hostname</h3>
                <div class="config-item">
                    <label for="hostname">Hostname</label>
                    <input type="text" id="hostname" value="${data.hostname}" readonly>
                </div>`;
            container.appendChild(hostnameDiv);

            // MOTD Banner
            const motdDiv = document.createElement('div');
            motdDiv.className = 'config-group';
            motdDiv.innerHTML = `
                <h3>Banner</h3>
                <div class="config-item">
                    <label for="motd_banner">MOTD Text</label>
                    <textarea id="motd_banner" rows="5">${data.motd}</textarea>
                </div>`;
            container.appendChild(motdDiv);
        }

        async function saveConfig() {
            const motd_banner = document.getElementById('motd_banner').value;

            const updatedData = {
                motd: motd_banner
            };

            try {
                const response = await fetch('/api/save_and_push_config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updatedData)
                });
                
                const data = await response.json();
                if (response.ok) {
                    showMessage(data.status, 'success');
                } else {
                    showMessage(data.error, 'error');
                }
            } catch (error) {
                console.error('Error saving config:', error);
                showMessage('An error occurred while saving.', 'error');
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
        "hostname": "Not Found",
        "motd": ""
    }
    
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()

        match_hostname = HOSTNAME_PATTERN.search(file_content)
        if match_hostname:
            config_data['hostname'] = match_hostname.group(1).strip()
        
        match_motd = MOTD_PATTERN.search(file_content)
        if match_motd:
            config_data['motd'] = match_motd.group(1).strip()
    
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {file_path}")
        raise
    
    return config_data

def reassemble_cisco_config(data, original_content):
    """Reassembles the config file with updated values, replacing in place."""
    
    # Replace banner using the regex pattern
    new_content = MOTD_PATTERN.sub(f'banner motd ^C\n{data["motd"]}\n^C', original_content)
    
    return new_content

@app.route('/')
def index():
    """Serves the main HTML page for the application."""
    return render_template_string(HTML_CONTENT)

@app.route('/api/get_parsed_config', methods=['GET'])
def get_parsed_config():
    """API endpoint to get the parsed config data."""
    if not os.path.exists(CONFIG_FILE_PATH):
        return jsonify({"error": "Configuration file not found on the server."}), 404
    
    try:
        parsed_data = parse_cisco_config(CONFIG_FILE_PATH)
        return jsonify(parsed_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/save_and_push_config', methods=['POST'])
def save_and_push_config():
    """API endpoint to save the config and push changes to Git."""
    data = request.json
    if not data or 'motd' not in data:
        return jsonify({"error": "Invalid request: MOTD data missing."}), 400

    if not os.path.exists(CONFIG_FILE_PATH):
        return jsonify({"error": "Configuration file not found on the server."}), 404

    try:
        # Read the current content of the file
        with open(CONFIG_FILE_PATH, 'r') as f:
            original_content = f.read()
        
        # Reassemble the config with the updated MOTD
        reassembled_config = reassemble_cisco_config(data, original_content)
        
        # Write the updated content back to the file
        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write(reassembled_config)
            
        # Execute Git commands using subprocess
        # This will be done in the directory where the script is running
        
        # subprocess.run(['git', 'add', '.'], check=True, cwd=SCRIPT_DIR)
        # subprocess.run(['git', 'commit', '-m "motd changes"'], check=True, cwd=SCRIPT_DIR)
        # subprocess.run(['git', 'push'], check=True, cwd=SCRIPT_DIR)
        
        # 1. Checkout the branch
        subprocess.run(['git', 'checkout', 'update-rtr1-config'], check=True, cwd=SCRIPT_DIR)
        
        # 2. Add the file to the staging area
        subprocess.run(['git', 'add', 'rtr1_config.txt'], check=True, cwd=SCRIPT_DIR)
        
        # 3. Commit the changes
        commit_message = f"Update MOTD via web app: {data['motd']}"
        subprocess.run(['git', 'commit', '-m', commit_message], check=True, cwd=SCRIPT_DIR)
        
        # 4. Push the changes to the remote repository
        subprocess.run(['git', 'push', '-u', 'origin', 'update-rtr1-config'], check=True, cwd=SCRIPT_DIR)
            
        return jsonify({"status": "Configuration saved and pushed to Git successfully!"})
    
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return jsonify({"error": f"Git command failed. Make sure your repository is clean and correctly configured. Error: {e.stderr}"}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initial check and file creation for local testing.
    # On a live server, this file should already exist as part of the git repo.
    if not os.path.exists(CONFIG_FILE_PATH):
        print(f"File '{CONFIG_FILE_PATH}' not found. Creating a default file for testing.")
        with open(CONFIG_FILE_PATH, 'w') as f:
            f.write("hostname rtr1\n!\n! some config\n!\nbanner motd ^C\nDemo for Services Austraila\n^C\n")
            
    app.run(debug=True)
