from flask import Flask, render_template_string, jsonify, request
import json
import os
from datetime import datetime
from pathlib import Path
from monitor_service import PropertyMonitor

app = Flask(__name__)

# Ensure data directory exists
Path('data').mkdir(exist_ok=True)

MOBILE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <title>🏠 Property Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding-bottom: 80px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 24px;
            color: #333;
            text-align: center;
        }
        
        .header p {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .container {
            padding: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 8px;
        }
        
        .stat-label {
            font-size: 13px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }
        
        .change-item {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 5px solid #28a745;
        }
        
        .change-date {
            font-size: 11px;
            color: #666;
            margin-bottom: 5px;
        }
        
        .change-address {
            font-weight: bold;
            color: #333;
            font-size: 16px;
            margin-bottom: 8px;
        }
        
        .change-detail {
            font-size: 13px;
            color: #555;
            margin: 3px 0;
        }
        
        .property-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 12px;
            border-left: 5px solid #667eea;
        }
        
        .property-label {
            font-weight: 600;
            color: #333;
            font-size: 15px;
        }
        
        .property-detail {
            font-size: 13px;
            color: #666;
            margin-top: 5px;
        }
        
        .no-data {
            text-align: center;
            padding: 40px 20px;
            color: #999;
            font-size: 14px;
        }
        
        .btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 16px;
            border-radius: 10px;
            width: 100%;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .btn-secondary {
            background: #667eea;
            margin-top: 10px;
        }
        
        .refresh-btn {
            background: #17a2b8;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            float: right;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏠 Property Monitor</h1>
        <p>Baton Rouge Property Tracking</p>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="totalTracked">-</div>
                <div class="stat-label">Tracking</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalChanges">-</div>
                <div class="stat-label">Changes</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">
                Recent Changes
                <button class="refresh-btn" onclick="loadData()">↻</button>
            </div>
            <div id="changesList">
                <div class="loading">
                    <div class="spinner"></div>
                    Loading...
                </div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Tracked Properties</div>
            <div id="propertiesList">
                <div class="loading">Loading...</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">Actions</div>
            <button class="btn" onclick="checkNow()">🔍 Check for Changes Now</button>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                const resp = await fetch('/api/data');
                const data = await resp.json();
                
                // Update stats
                document.getElementById('totalTracked').textContent = data.properties.length;
                document.getElementById('totalChanges').textContent = data.changes.length;
                
                // Render changes
                const changesList = document.getElementById('changesList');
                if (data.changes.length === 0) {
                    changesList.innerHTML = '<div class="no-data">No changes detected yet.<br><small>Run a check to start monitoring!</small></div>';
                } else {
                    const recentChanges = data.changes.slice(-10).reverse();
                    changesList.innerHTML = recentChanges.map(change => {
                        const date = new Date(change.detected_date).toLocaleDateString();
                        const changesText = change.changes.map(c => 
                            `<div class="change-detail"><strong>${c.field}:</strong> ${c.old_value} → ${c.new_value}</div>`
                        ).join('');
                        
                        return `
                            <div class="change-item">
                                <div class="change-date">${date}</div>
                                <div class="change-address">${change.property_address}</div>
                                ${changesText}
                            </div>
                        `;
                    }).join('');
                }
                
                // Render properties
                const propsList = document.getElementById('propertiesList');
                if (data.properties.length === 0) {
                    propsList.innerHTML = '<div class="no-data">No properties tracked yet</div>';
                } else {
                    const displayProps = data.properties.slice(0, 15);
                    propsList.innerHTML = displayProps.map(prop => {
                        const added = new Date(prop.added_date).toLocaleDateString();
                        
                        if (prop.search_type === 'zip') {
                            return `
                                <div class="property-item">
                                    <div class="property-label">ZIP Code ${prop.search_value}</div>
                                    <div class="property-detail">Monitoring entire area • Added ${added}</div>
                                </div>
                            `;
                        } else {
                            const data = prop.current_data || {};
                            return `
                                <div class="property-item">
                                    <div class="property-label">${data.PHYSICAL_ADDRESS || prop.search_value}</div>
                                    <div class="property-detail">
                                        ${data.OWNER ? 'Owner: ' + data.OWNER : ''} • Added ${added}
                                    </div>
                                </div>
                            `;
                        }
                    }).join('');
                    
                    if (data.properties.length > 15) {
                        propsList.innerHTML += `<div class="property-detail" style="text-align:center;margin-top:10px;color:#999;">And ${data.properties.length - 15} more...</div>`;
                    }
                }
                
            } catch (error) {
                console.error('Error loading data:', error);
                document.getElementById('changesList').innerHTML = '<div class="no-data">Error loading data</div>';
            }
        }
        
        async function checkNow() {
            if (!confirm('Run a property check now? This may take 1-2 minutes to check all tracked properties.')) {
                return;
            }
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner" style="width:20px;height:20px;border-width:2px;display:inline-block;margin-right:10px;"></div> Checking...';
            
            try {
                const response = await fetch('/api/check', { method: 'POST' });
                const result = await response.json();
                
                if (result.success) {
                    await loadData();
                    alert(`✅ Check complete!\n\nFound ${result.changes} change(s).`);
                } else {
                    alert('❌ Check failed. Please try again.');
                }
            } catch (error) {
                alert('Error running check. Please try again.');
                console.error(error);
            } finally {
                btn.disabled = false;
                btn.innerHTML = '🔍 Check for Changes Now';
            }
        }
        
        // Load data on startup
        loadData();
        
        // Auto-refresh every 60 seconds
        setInterval(loadData, 60000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(MOBILE_HTML)

@app.route('/api/data')
def get_data():
    """Get tracked properties and changes"""
    try:
        with open('data/tracked_properties.json', 'r') as f:
            properties = json.load(f)
    except FileNotFoundError:
        properties = []
    
    try:
        with open('data/detected_changes.json', 'r') as f:
            changes = json.load(f)
    except FileNotFoundError:
        changes = []
    
    return jsonify({
        'properties': properties,
        'changes': changes,
        'last_updated': datetime.now().isoformat()
    })

@app.route('/api/check', methods=['POST'])
def run_check():
    """Run property check"""
    try:
        monitor = PropertyMonitor()
        changes = monitor.check_all_properties()
        
        return jsonify({
            'success': True,
            'changes': len(changes),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
