from flask import Flask, render_template_string, jsonify, request
import sys
import os
import asyncio
import json
import logging
import time
import traceback
from datetime import datetime
from threading import Thread

# v1.0.35 - Crash-Resistant Async Handling
VERSION = "1.0.35"

sys.path.append("/config/custom_components/localtuya/core")
try:
    from pytuya import connect, TuyaListener
    from cloud_api import TuyaCloudApi
except ImportError:
    print("Dependencies not found")

app = Flask(__name__)
CONFIG_PATH = "/config/.storage/core.config_entries"
SETTINGS_PATH = "/config/tuya_manager_settings.json"

# Shared loop for background tasks
loop = asyncio.new_event_loop()
def start_loop(l):
    asyncio.set_event_loop(l)
    l.run_forever()
Thread(target=start_loop, args=(loop,), daemon=True).start()

class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__(); self.records = []
    def emit(self, record): self.records.append(self.format(record))

def get_ha_config():
    try:
        with open(CONFIG_PATH, "r") as f: return json.load(f)
    except: return {}

def get_devices_data():
    ha = get_ha_config()
    for e in ha.get("data", {}).get("entries", []):
        if e["domain"] == "localtuya": return e["data"]["devices"]
    return {}

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f: return json.load(f)
        except: pass
    return {"sort_order": "name", "usage": {}}

def save_settings(s):
    try:
        with open(SETTINGS_PATH, 'w') as f: json.dump(s, f)
    except: pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tuya Manager v{{ version }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, sans-serif; line-height: 1.4; color: #333; max-width: 1200px; margin: 0 auto; padding: 15px; background: #f0f2f5; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: #2c3e50; color: white; padding: 10px 20px; border-radius: 8px; }
        .container { display: flex; gap: 15px; height: 85vh; }
        .sidebar { flex: 1; display: flex; flex-direction: column; gap: 10px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .main { flex: 2.5; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
        .list { overflow-y: auto; flex: 1; border: 1px solid #eee; }
        .item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .item:hover { background: #f8f9fa; }
        .item.active { background: #e7f1ff; border-left: 4px solid #007bff; }
        .status-area { flex: 1; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; background: white; position: relative; }
        .overlay { position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.8); display: flex; align-items: center; justify-content: center; z-index: 10; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th { background: #f8f9fa; text-align: left; padding: 6px; border-bottom: 2px solid #dee2e6; position: sticky; top: 0; z-index: 5; }
        td { padding: 6px; border-bottom: 1px solid #eee; }
        .tech-logs { font-size: 11px; margin-top: 10px; height: 180px; overflow-y: auto; background: #1e1e1e; color: #00ff00; padding: 10px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
        .controls { margin-top: 15px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; padding-top: 15px; border-top: 1px solid #eee; }
        button { padding: 8px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; color: white; font-size: 12px; }
        .btn-refresh { background: #28a745; }
        .btn-send { background: #007bff; }
        .btn-cloud { background: #17a2b8; }
        input, select { padding: 6px; border: 1px solid #ccc; border-radius: 4px; width: 100%; box-sizing: border-box; font-size: 12px; }
        label { font-size: 10px; font-weight: bold; color: #666; display: block; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="header"><h2>Tuya Manager</h2><span>v{{ version }}</span></div>
    <div class="container">
        <div class="sidebar">
            <label>Sort</label>
            <select id="sort" onchange="updateSort(this.value)">
                <option value="name">Name</option><option value="ip">IP</option><option value="usage">Usage</option>
            </select>
            <div class="list" id="deviceList">Loading...</div>
        </div>
        <div class="main" id="details" style="display:none">
            <h3 id="name" style="margin:0"></h3>
            <p id="meta" style="font-size:11px; color:#666; margin:5px 0"></p>
            <div class="status-area">
                <div id="loadingOverlay" class="overlay hidden">WORKING...</div>
                <table id="dpTable">
                    <thead><tr><th>ID</th><th>Function</th><th>Value</th><th>Cloud Code</th></tr></thead>
                    <tbody id="dpBody"></tbody>
                </table>
            </div>
            <div class="tech-logs" id="techLogs">Ready.</div>
            <div class="controls">
                <div><label>DP ID</label><input type="number" id="dpId" onchange="updateValueInput()"></div>
                <div>
                    <label>Value</label>
                    <input type="text" id="dpValText">
                    <select id="dpValSelect" style="display:none"></select>
                </div>
                <div><label>Timeout</label><input type="number" id="timeout" value="10"></div>
                <div style="display:flex; align-items:flex-end;"><button class="btn-refresh" style="width:100%" onclick="refresh()">Refresh Local</button></div>
                <div style="grid-column: span 2;"><button class="btn-cloud" style="width:100%" onclick="cloudCheck()">Verify Cloud Response</button></div>
                <div style="grid-column: span 2;"><button class="btn-send" style="width:100%" id="sendBtn" onclick="send()">Send Command</button></div>
            </div>
        </div>
    </div>
    <script>
        let devices = {}; let currentDps = {}; let cloudDps = {}; let selectedId = null; let currentSort = "name";
        async function init() {
            const s = await (await fetch('/api/settings')).json();
            currentSort = s.sort_order || "name"; document.getElementById('sort').value = currentSort;
            loadDevices();
        }
        async function loadDevices() {
            try {
                const r = await fetch('/api/devices'); const data = await r.json();
                devices = data.devices; const usage = data.usage || {};
                const keys = Object.keys(devices).sort((a,b) => {
                    if(currentSort === 'usage') return (usage[b]||0) - (usage[a]||0);
                    if(currentSort === 'ip') return (devices[a].host || '').localeCompare(devices[b].host || '');
                    return (devices[a].friendly_name || '').localeCompare(devices[b].friendly_name || '');
                });
                document.getElementById('deviceList').innerHTML = keys.map(k => `
                    <div class="item ${selectedId===k?'active':''}" onclick="select('${k}')">
                        <strong>${devices[k].friendly_name || k}</strong><br><small>${devices[k].host || 'no ip'}</small>
                    </div>
                `).join('');
            } catch(e) { console.error(e); }
        }
        function select(id) {
            selectedId = id; const d = devices[id];
            document.getElementById('details').style.display = 'flex';
            document.getElementById('name').innerText = d.friendly_name || id;
            document.getElementById('meta').innerText = `ID: ${id} | IP: ${d.host} | Key: ${d.local_key}`;
            document.querySelectorAll('.item').forEach(el => el.classList.remove('active'));
            refresh();
        }
        async function refresh() {
            if(!selectedId) return;
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            try {
                const r = await fetch(`/api/device/${selectedId}/status?timeout=${document.getElementById('timeout').value}`);
                const data = await r.json();
                document.getElementById('techLogs').innerText = data.tech_logs || "No data.";
                if (!data.error) { currentDps = data.status || {}; renderTable(); }
                else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }
        async function cloudCheck() {
            if(!selectedId) return;
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            const logsBox = document.getElementById('techLogs');
            logsBox.innerText = "Querying Tuya Cloud...\\n";
            try {
                const r = await fetch(`/api/device/${selectedId}/cloud_check`);
                const data = await r.json();
                logsBox.innerText = data.tech_logs || "";
                if (!data.error) { 
                    cloudDps = data.result || {}; 
                    logsBox.innerText += "\\n\\n--- CLOUD JSON RESULT ---\\n" + JSON.stringify(data.result, null, 2);
                    renderTable(); 
                } else { alert(data.error); }
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }
        function renderTable() {
            const mapping = devices[selectedId].entities || [];
            const allIds = new Set([...Object.keys(currentDps), ...Object.keys(cloudDps)]);
            document.getElementById('dpBody').innerHTML = Array.from(allIds).sort((a,b)=>Number(a)-Number(b)).map(id => {
                const localVal = currentDps[id] !== undefined ? currentDps[id] : '<span style="color:#999">?</span>';
                const cloudInfo = cloudDps[id] || {};
                const entity = mapping.find(e => e.id == id);
                return `<tr onclick="onRowClick('${id}', '${currentDps[id]}')" style="cursor:pointer">
                    <td><b>${id}</b></td><td>${entity?entity.friendly_name:(cloudInfo.name || 'Unknown')}</td>
                    <td>${localVal}</td><td><small>${cloudInfo.code || '-'}</small></td>
                </tr>`;
            }).join('');
            updateValueInput();
        }
        function onRowClick(id, val) {
            document.getElementById('dpId').value = id;
            updateValueInput(val);
        }
        function updateValueInput(valOverride = null) {
            if(!selectedId) return;
            const dpId = document.getElementById('dpId').value;
            const textInput = document.getElementById('dpValText');
            const selectDiv = document.getElementById('dpValSelect');
            const cloudInfo = cloudDps[dpId] || {};
            const entity = (devices[selectedId].entities || []).find(e => e.id == dpId);
            const curVal = valOverride !== null ? valOverride : currentDps[dpId];

            let options = null;
            if(cloudInfo.values && cloudInfo.values.type === 'enum') {
                options = {}; cloudInfo.values.range.forEach(v => options[v] = v);
            } else if(cloudInfo.values && cloudInfo.values.type === 'boolean') {
                options = {"true": "ON", "false": "OFF"};
            } else if(entity && entity.select_options) {
                options = entity.select_options;
            } else if(curVal === true || curVal === false || curVal === 'true' || curVal === 'false') {
                options = {"true": "ON", "false": "OFF"};
            }

            if(options) {
                textInput.style.display = 'none'; selectDiv.style.display = 'block';
                selectDiv.innerHTML = Object.keys(options).map(k => `<option value="${k}" ${String(curVal)===String(k)?'selected':''}>${options[k]}</option>`).join('');
            } else {
                textInput.style.display = 'block'; selectDiv.style.display = 'none';
                if(valOverride !== null) textInput.value = valOverride;
            }
        }
        async function updateSort(v) { 
            currentSort = v; 
            await fetch('/api/settings', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({sort_order:v})});
            loadDevices(); 
        }
        async function send() {
            const dpId = document.getElementById('dpId').value;
            const val = document.getElementById('dpValSelect').style.display === 'none' ? document.getElementById('dpValText').value : document.getElementById('dpValSelect').value;
            let finalVal = val;
            if(val.toLowerCase()==='true') finalVal = true;
            else if(val.toLowerCase()==='false') finalVal = false;
            else if(!isNaN(val) && val.trim()!=='') finalVal = Number(val);
            const overlay = document.getElementById('loadingOverlay'); overlay.classList.remove('hidden');
            try {
                await fetch(`/api/device/${selectedId}/command`, {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({ dps:{[dpId]:finalVal}, timeout:document.getElementById('timeout').value })
                });
                refresh();
            } catch(e) { alert(e); }
            finally { overlay.classList.add('hidden'); }
        }
        init();
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE, version=VERSION)

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    s = load_settings()
    if request.method == 'POST': s.update(request.json); save_settings(s)
    return jsonify(s)

@app.route('/api/devices')
def api_devices(): return jsonify({"devices": get_devices_data(), "usage": load_settings()["usage"]})

@app.route('/api/device/<dev_id>/status')
def api_status(dev_id):
    d = get_devices_data()[dev_id]; t = int(request.args.get('timeout', 10))
    async def _run():
        h = ListHandler(); logging.getLogger('pytuya').addHandler(h); logging.getLogger('pytuya').setLevel(logging.DEBUG)
        p = None
        try:
            p = await asyncio.wait_for(connect(address=d['host'], device_id=d['device_id'], local_key=d['local_key'],
                protocol_version=float(d.get('protocol_version', 3.3)), enable_debug=True, timeout=t), timeout=t + 1)
            res = await p.detect_available_dps(); return {"status": res, "tech_logs": "\\n".join(h.records)}
        except Exception as e: return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            if p and p.transport: p.transport.close()
            logging.getLogger('pytuya').removeHandler(h)
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try: return jsonify(future.result(timeout=t+5))
    except Exception as e: return jsonify({"error": str(e)})

@app.route('/api/device/<dev_id>/cloud_check')
def api_cloud_check(dev_id):
    ha_config = get_ha_config(); cloud_conf = None
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry["domain"] == "localtuya": cloud_conf = entry["data"]; break
    if not cloud_conf: return jsonify({"error": "No cloud config"}), 404
    async def _run():
        h = ListHandler(); cl_logger = logging.getLogger('cloud_api'); cl_logger.addHandler(h); cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(cloud_conf['region'], cloud_conf['client_id'], cloud_conf['client_secret'], cloud_conf['user_id'])
            await api.async_connect(); funcs = await api.async_get_device_functions(dev_id)
            for dp in funcs:
                if 'values' in funcs[dp]: 
                    try: funcs[dp]['values'] = json.loads(funcs[dp]['values'])
                    except: pass
            return {"result": funcs, "tech_logs": "\\n".join(h.records)}
        except Exception as e: return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally: cl_logger.removeHandler(h)
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try: return jsonify(future.result(timeout=20))
    except Exception as e: return jsonify({"error": str(e)})

@app.route('/api/device/<dev_id>/command', methods=['POST'])
def api_command(dev_id):
    d = get_devices_data()[dev_id]; req = request.json
    async def _run():
        p = await connect(address=d['host'], device_id=d['device_id'], local_key=d['local_key'], 
                          protocol_version=float(d.get('protocol_version', 3.3)), enable_debug=True, timeout=int(req.get('timeout', 10)))
        await p.detect_available_dps(); await p.set_dps(req['dps']); await asyncio.sleep(0.5); return {"result": "ok"}
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try: return jsonify(future.result(timeout=15))
    except Exception as e: return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
