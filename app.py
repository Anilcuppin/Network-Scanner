from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import sys
import os

# Add parent directory to path to import netscan
import netscan

# Configure Flask to use the templates and static folders from the netscan directory
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'netscan', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'netscan', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scans.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Model
class ScanHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    network_cidr = db.Column(db.String(50), nullable=False)
    online_hosts = db.Column(db.Text, nullable=False)  # JSON string
    total_hosts = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'network_cidr': self.network_cidr,
            'online_hosts': json.loads(self.online_hosts),
            'total_hosts': self.total_hosts
        }

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def scan():
    try:
        data = request.json
        network_input = data.get('network', None)
        
        # Parse network using netscan logic
        network = netscan.parse_network(network_input)
        
        # Perform scan
        online_hosts = netscan.scan_network(network)
        
        # Save to database
        scan_record = ScanHistory(
            network_cidr=str(network),
            online_hosts=json.dumps(online_hosts),
            total_hosts=len(online_hosts)
        )
        db.session.add(scan_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'network': str(network),
            'online_hosts': online_hosts,
            'total': len(online_hosts),
            'scan_id': scan_record.id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/history', methods=['GET'])
def history():
    try:
        scans = ScanHistory.query.order_by(ScanHistory.timestamp.desc()).limit(50).all()
        return jsonify({
            'success': True,
            'scans': [scan.to_dict() for scan in scans]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

@app.route('/api/delete/<int:scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    try:
        scan = ScanHistory.query.get_or_404(scan_id)
        db.session.delete(scan)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
