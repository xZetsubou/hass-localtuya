from flask import Flask, render_template_string, jsonify, request
import sys
import os
import asyncio
import json
import logging
from pathlib import Path
from threading import Thread
import subprocess

# v1.1.3 - Ensure managed devices include cloud_ip via MAC/device_id matching
VERSION = "1.1.3"

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CORE_PATH = BASE_DIR / "custom_components" / "localtuya" / "core"
LOCALTUYA_CORE_PATH = Path(
    os.environ.get("LOCALTUYA_CORE_PATH", str(DEFAULT_CORE_PATH))
).expanduser()

if str(LOCALTUYA_CORE_PATH) not in sys.path:
    sys.path.append(str(LOCALTUYA_CORE_PATH))
try:
    from pytuya import connect, TuyaListener
    from cloud_api import TuyaCloudApi
except ImportError:
    connect = None
    TuyaCloudApi = None
    print("Dependencies not found. Set LOCALTUYA_CORE_PATH to localtuya/core path.")

app = Flask(__name__)
HA_CONFIG_BASE = Path(os.environ.get("HA_CONFIG_DIR", str(BASE_DIR))).expanduser()
CONFIG_PATH = Path(
    os.environ.get("HA_CORE_CONFIG_ENTRIES_PATH", str(HA_CONFIG_BASE / ".storage" / "core.config_entries"))
).expanduser()
SETTINGS_PATH = Path(
    os.environ.get("TUYA_GUI_SETTINGS_PATH", str(HA_CONFIG_BASE / "tuya_manager_settings.json"))
).expanduser()

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
        with CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def get_devices_data():
    ha = get_ha_config()
    for e in ha.get("data", {}).get("entries", []):
        if e["domain"] == "localtuya": return e["data"]["devices"]
    return {}


def _extract_mac(val):
    if not val:
        return None
    if isinstance(val, str):
        # normalize common formats: AA:BB:CC:DD:EE:FF / AA-BB-... / AABBCCDDEEFF
        v = val.strip().lower().replace('-', ':')
        if ':' in v:
            parts = [p.zfill(2) for p in v.split(':') if p != '']
            if len(parts) == 6:
                return ':'.join(parts)
        # fallback: compact hex
        compact = ''.join(ch for ch in v if ch.isalnum())
        if len(compact) == 12:
            return ':'.join(compact[i:i+2] for i in range(0, 12, 2))
        return v
    return None


def _build_cloud_conf():
    ha_config = get_ha_config()
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            return entry.get("data")
    return None


def _lan_mac_for_ip(ip):
    """Best-effort MAC lookup for a local IPv4 address.

    Order:
    1) /proc/net/arp (fast, no extra deps)
    2) `ip neigh show <ip>` (requires iproute2)
    """
    if not ip or not isinstance(ip, str):
        return None
    ip = ip.strip()
    if not ip:
        return None

    # 1) ARP cache
    try:
        with open('/proc/net/arp', 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        for line in lines[1:]:
            parts = line.split()
            if len(parts) >= 4 and parts[0] == ip:
                mac = parts[3]
                mac_n = _extract_mac(mac)
                if mac_n and mac_n != '00:00:00:00:00:00':
                    return mac_n
    except Exception:
        pass

    # 2) ip neigh
    try:
        out = subprocess.check_output(['ip', 'neigh', 'show', ip], text=True, stderr=subprocess.DEVNULL).strip()
        # Example: "192.168.0.10 dev eth0 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
        if 'lladdr' in out:
            mac = out.split('lladdr', 1)[1].strip().split()[0]
            return _extract_mac(mac)
    except Exception:
        pass

    return None


async def _fetch_cloud_devices(cloud_conf):
    api = TuyaCloudApi(
        cloud_conf['region'],
        cloud_conf['client_id'],
        cloud_conf['client_secret'],
        cloud_conf['user_id'],
    )
    await api.async_connect()
    devs = await api.async_get_devices_list(force_update=True)
    if isinstance(devs, dict):
        return devs
    if isinstance(getattr(api, 'device_list', None), dict):
        return api.device_list
    if isinstance(getattr(api, 'devices', None), dict):
        return api.devices
    return {}

def load_settings():
    if SETTINGS_PATH.exists():
        try:
            with SETTINGS_PATH.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"sort_order": "name", "usage": {}}

def save_settings(s):
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with SETTINGS_PATH.open('w', encoding='utf-8') as f:
            json.dump(s, f)
    except Exception:
        pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tuya Manager v{{ version }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, sans-serif; line-height: 1.4; color: #333; max-width: 1200px; margin: 0 auto; padding: 15px; background: #f0f2f5; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; background: #2c3e50; color: white; padding: 10px 20px; border-radius: 8px; }
        .tabs { display:flex; gap:8px; margin-bottom:10px; }
        .tab-btn { background:#6c757d; color:#fff; border:none; border-radius:6px; padding:8px 12px; cursor:pointer; font-weight:700; }
        .tab-btn.active { background:#007bff; }
        .tab-content { display:none; }
        .tab-content.active { display:flex; }
        .container { gap: 15px; height: 85vh; }
        .sidebar { flex: 1; display: flex; flex-direction: column; gap: 10px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .main { flex: 2.5; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); display: flex; flex-direction: column; overflow: hidden; }
        .list { overflow-y: auto; flex: 1; border: 1px solid #eee; }
        .item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; }
        .item:hover { background: #f8f9fa; }
        .item.active { background: #e7f1ff; border-left: 4px solid #007bff; }
        .item.dup-name { background: #fff3cd; }
        .item.dup-name:hover { background: #ffe8a1; }
        .badge { display:inline-block; padding:2px 6px; border-radius:10px; font-size:10px; font-weight:700; margin-left:6px; }
        .badge-warn { background:#856404; color:#fff; }
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
    <div class="tabs">
        <button id="tabManageBtn" class="tab-btn active" onclick="switchTab('manage')">Manage devices</button>
        <button id="tabAddBtn" class="tab-btn" onclick="switchTab('add')">Add new device</button>
    </div>

    <div id="tabManage" class="container tab-content active">
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

    <div id="tabAdd" class="container tab-content">
        <div class="sidebar">
            <label>Cloud devices not yet configured</label>
            <div style="display:flex; gap:8px; margin-bottom:8px;">
                <button class="btn-cloud" style="flex:1" onclick="loadUnaddedDevices()">Refresh Unadded</button>
            </div>
            <div class="list" id="unaddedList">Press "Refresh Unadded"</div>
        </div>
        <div class="main" id="unaddedDetails" style="display:none">
            <h3 id="unaddedName" style="margin:0"></h3>
            <p id="unaddedMeta" style="font-size:11px; color:#666; margin:5px 0"></p>
            <div class="status-area">
                <div id="unaddedLoadingOverlay" class="overlay hidden">WORKING...</div>
                <table>
                    <thead><tr><th>DP</th><th>Name</th><th>Code</th><th>Type</th><th>Values</th></tr></thead>
                    <tbody id="unaddedDpBody"></tbody>
                </table>
            </div>
            <div class="tech-logs" id="unaddedLogs">Ready.</div>
        </div>
    </div>
    <script>
        let devices = {}; let currentDps = {}; let cloudDps = {}; let selectedId = null; let currentSort = "name";
        let unaddedDevices = {}; let selectedUnaddedId = null;
        function deviceDisplayName(d, fallbackId) {
            if(!d) return fallbackId;
            return d.friendly_name || d.name || d.local_name || fallbackId;
        }
        function managedNameSet() {
            const set = new Set();
            Object.keys(devices || {}).forEach(id => {
                const n = deviceDisplayName(devices[id], id);
                if(n) set.add(String(n).trim().toLowerCase());
            });
            return set;
        }
        function switchTab(tab) {
            const isManage = tab === 'manage';
            document.getElementById('tabManage').classList.toggle('active', isManage);
            document.getElementById('tabAdd').classList.toggle('active', !isManage);
            document.getElementById('tabManageBtn').classList.toggle('active', isManage);
            document.getElementById('tabAddBtn').classList.toggle('active', !isManage);
        }
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
                    if(currentSort === 'ip') {
                        const aLocal = devices[a].local_ip || devices[a].host || '';
                        const bLocal = devices[b].local_ip || devices[b].host || '';
                        const aCloud = devices[a].cloud_ip || '';
                        const bCloud = devices[b].cloud_ip || '';
                        return (aLocal + '|' + aCloud).localeCompare(bLocal + '|' + bCloud);
                    }
                    return (devices[a].friendly_name || '').localeCompare(devices[b].friendly_name || '');
                });
                document.getElementById('deviceList').innerHTML = keys.map(k => `
                    <div class="item ${selectedId===k?'active':''}" onclick="select('${k}')">
                        <strong>${devices[k].friendly_name || k}</strong><br>
                        <small>local: ${(devices[k].local_ip || devices[k].host || 'no local ip')} | cloud: ${(devices[k].cloud_ip || 'no cloud ip')} | mac: ${(devices[k].match_mac || devices[k].mac || '-') }</small>
                    </div>
                `).join('');
            } catch(e) { console.error(e); }
        }
        function select(id) {
            selectedId = id; const d = devices[id];
            document.getElementById('details').style.display = 'flex';
            document.getElementById('name').innerText = d.friendly_name || id;
            document.getElementById('meta').innerText = `ID: ${id} | Local IP: ${(d.local_ip || d.host || 'N/A')} | Cloud IP: ${(d.cloud_ip || 'N/A')} | MAC: ${(d.match_mac || d.mac || 'N/A')}`;
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

        async function loadUnaddedDevices() {
            const list = document.getElementById('unaddedList');
            const logs = document.getElementById('unaddedLogs');
            list.innerHTML = 'Loading...';
            logs.innerText = 'Querying cloud devices...';
            try {
                const r = await fetch('/api/devices/unadded');
                const data = await r.json();
                logs.innerText = data.tech_logs || 'Done.';
                if (data.error) {
                    list.innerHTML = `<div class="item">Error: ${data.error}</div>`;
                    return;
                }
                unaddedDevices = data.devices || {};
                const mset = managedNameSet();
                const keys = Object.keys(unaddedDevices);
                if (!keys.length) {
                    list.innerHTML = '<div class="item">No unadded devices found.</div>';
                    return;
                }
                list.innerHTML = keys.map(k => {
                    const d = unaddedDevices[k] || {};
                    const localIp = d.local_ip || 'no local IP';
                    const cloudIp = d.cloud_ip || (d.ip || 'no cloud IP');
                    const mac = d.match_mac || d.mac || d.device_mac || '-';
                    const name = deviceDisplayName(d, k);
                    const isDup = mset.has(String(name).trim().toLowerCase());
                    const dupNote = 'Same name as an already managed device: it may be a different Tuya Cloud record (different deviceId/IP).';
                    return `<div class="item ${selectedUnaddedId===k?'active':''} ${isDup?'dup-name':''}" onclick="selectUnadded('${k}')">
                        <strong>${name}${isDup?'<span class="badge badge-warn">DUPLICATE NAME</span>':''}</strong><br>
                        <small>${d.product_name || d.category || '-'} | local: ${localIp} | cloud: ${cloudIp} | mac: ${mac}</small>
                        ${isDup?`<br><small style="color:#856404">${dupNote}</small>`:''}
                    </div>`;
                }).join('');
            } catch(e) {
                list.innerHTML = `<div class="item">Error: ${e}</div>`;
            }
        }

        async function selectUnadded(devId) {
            selectedUnaddedId = devId;
            document.querySelectorAll('#unaddedList .item').forEach(el => el.classList.remove('active'));
            document.getElementById('unaddedDetails').style.display = 'flex';
            const d = unaddedDevices[devId] || {};
            document.getElementById('unaddedName').innerText = d.name || d.local_name || devId;
            document.getElementById('unaddedMeta').innerText = `ID: ${devId} | Category: ${d.category || '-'} | Product: ${d.product_name || '-'} | Local IP: ${d.local_ip || 'N/A'} | Cloud IP: ${d.cloud_ip || d.ip || 'N/A'} | MAC: ${d.match_mac || d.mac || d.device_mac || 'N/A'}`;
            const overlay = document.getElementById('unaddedLoadingOverlay');
            const logs = document.getElementById('unaddedLogs');
            overlay.classList.remove('hidden');
            logs.innerText = 'Loading cloud functions...';
            try {
                const r = await fetch(`/api/device/${devId}/cloud_check`);
                const data = await r.json();
                logs.innerText = data.tech_logs || '';
                if (data.error) {
                    document.getElementById('unaddedDpBody').innerHTML = `<tr><td colspan="5">Error: ${data.error}</td></tr>`;
                    return;
                }
                const funcs = data.result || {};
                const rows = Object.keys(funcs).sort().map(dpId => {
                    const info = funcs[dpId] || {};
                    const type = info.values && info.values.type ? info.values.type : '-';
                    const values = info.values ? JSON.stringify(info.values) : '-';
                    return `<tr>
                        <td><b>${dpId}</b></td>
                        <td>${info.name || '-'}</td>
                        <td><small>${info.code || '-'}</small></td>
                        <td>${type}</td>
                        <td><small>${values}</small></td>
                    </tr>`;
                });
                document.getElementById('unaddedDpBody').innerHTML = rows.length ? rows.join('') : '<tr><td colspan="5">No DP/functions returned.</td></tr>';
            } catch(e) {
                document.getElementById('unaddedDpBody').innerHTML = `<tr><td colspan="5">Error: ${e}</td></tr>`;
            } finally {
                overlay.classList.add('hidden');
            }
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
def api_devices():
    devices = get_devices_data()

    # Enrich devices with cloud/local IP mapping via MAC.
    # - local IP: from configured device host
    # - cloud IP: from Tuya cloud device list (ip/local_ip fields)
    # Matching key: mac address (preferred), fallback to device_id.
    if TuyaCloudApi is None:
        return jsonify({"devices": devices, "usage": load_settings()["usage"]})

    cloud_conf = _build_cloud_conf()
    if not cloud_conf:
        return jsonify({"devices": devices, "usage": load_settings()["usage"]})

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger('cloud_api')
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            cloud_devices = await _fetch_cloud_devices(cloud_conf)

            cloud_by_mac = {}
            cloud_by_id = {}
            for dev_id, info in (cloud_devices or {}).items():
                if not isinstance(info, dict):
                    continue
                mac = _extract_mac(info.get('mac') or info.get('device_mac'))
                if mac:
                    cloud_by_mac[mac] = info
                cloud_by_id[dev_id] = info

            enriched = {}
            for dev_id, d in (devices or {}).items():
                d = dict(d)
                local_ip = d.get('host')
                mac = _extract_mac(d.get('mac'))

                cloud = None
                if mac and mac in cloud_by_mac:
                    cloud = cloud_by_mac.get(mac)
                if cloud is None:
                    # try common id fields
                    cloud = cloud_by_id.get(d.get('device_id')) or cloud_by_id.get(d.get('gwId')) or cloud_by_id.get(dev_id)

                cloud_ip = None
                cloud_mac = None
                if isinstance(cloud, dict):
                    cloud_ip = cloud.get('ip') or cloud.get('local_ip')
                    cloud_mac = _extract_mac(cloud.get('mac') or cloud.get('device_mac'))
                    # Also surface category/product name when available
                    d.setdefault('category', cloud.get('category'))
                    d.setdefault('product_name', cloud.get('product_name'))

                # MAC resolution order: cloud -> local config -> LAN lookup by local IP
                resolved_mac = _extract_mac(d.get('mac') or d.get('match_mac')) or cloud_mac
                if not resolved_mac:
                    resolved_mac = _lan_mac_for_ip(local_ip)

                d['local_ip'] = local_ip
                d['cloud_ip'] = cloud_ip
                d['match_mac'] = resolved_mac
                d['mac'] = resolved_mac
                enriched[dev_id] = d

            return {"devices": enriched, "usage": load_settings()["usage"], "tech_logs": "\n".join(h.records)}
        except Exception as e:
            return {"devices": devices, "usage": load_settings()["usage"], "error": str(e), "tech_logs": "\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=25))
    except Exception as e:
        return jsonify({"devices": devices, "usage": load_settings()["usage"], "error": str(e)})

@app.route('/api/devices/unadded')
def api_unadded_devices():
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503

    ha_config = get_ha_config()
    cloud_conf = None
    configured_devices = get_devices_data()
    configured_ids = set((configured_devices or {}).keys())
    for entry in ha_config.get("data", {}).get("entries", []):
        if entry.get("domain") == "localtuya":
            cloud_conf = entry.get("data")
            break

    if not cloud_conf:
        return jsonify({"error": "No cloud config"}), 404

    async def _run():
        h = ListHandler()
        cl_logger = logging.getLogger('cloud_api')
        cl_logger.addHandler(h)
        cl_logger.setLevel(logging.DEBUG)
        try:
            api = TuyaCloudApi(
                cloud_conf['region'],
                cloud_conf['client_id'],
                cloud_conf['client_secret'],
                cloud_conf['user_id'],
            )
            await api.async_connect()
            devs = await api.async_get_devices_list(force_update=True)
            cloud_devices = {}
            if isinstance(devs, dict):
                cloud_devices = devs
            elif isinstance(getattr(api, 'device_list', None), dict):
                cloud_devices = api.device_list
            elif isinstance(getattr(api, 'devices', None), dict):
                cloud_devices = api.devices

            configured_by_mac = {}
            configured_by_device_id = {}
            for d in (configured_devices or {}).values():
                if not isinstance(d, dict):
                    continue
                m = _extract_mac(d.get('mac') or d.get('match_mac'))
                if m:
                    configured_by_mac[m] = d.get('host')
                if d.get('device_id'):
                    configured_by_device_id[d.get('device_id')] = d.get('host')
                if d.get('gwId'):
                    configured_by_device_id[d.get('gwId')] = d.get('host')

            unadded = {}
            for dev_id, info in cloud_devices.items():
                if dev_id in configured_ids:
                    continue
                ip_cloud = info.get('ip') or info.get('local_ip') or ''
                mac = _extract_mac(info.get('mac') or info.get('device_mac'))

                # If cloud device matches any already-configured device, do NOT show it as unadded.
                if mac and mac in configured_by_mac:
                    continue
                if dev_id in configured_by_device_id:
                    continue
                if isinstance(info, dict) and info.get('gwId') and info.get('gwId') in configured_by_device_id:
                    continue

                local_ip = configured_by_mac.get(mac) if mac else None
                local_ip = local_ip or configured_by_device_id.get(dev_id)
                info['cloud_ip'] = ip_cloud
                info['local_ip'] = local_ip
                info['match_mac'] = mac
                unadded[dev_id] = info
            return {"devices": unadded, "tech_logs": "\n".join(h.records)}
        except Exception as e:
            return {"error": str(e), "tech_logs": "\n".join(h.records)}
        finally:
            cl_logger.removeHandler(h)

    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try:
        return jsonify(future.result(timeout=25))
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/device/<dev_id>/status')
def api_status(dev_id):
    if connect is None:
        return jsonify({"error": "LocalTuya core dependencies unavailable"}), 503
    devices = get_devices_data()
    d = devices.get(dev_id)
    if not d:
        return jsonify({"error": "Unknown device"}), 404
    t = int(request.args.get('timeout', 10))
    async def _run():
        h = ListHandler(); logging.getLogger('pytuya').addHandler(h); logging.getLogger('pytuya').setLevel(logging.DEBUG)
        p = None
        try:
            p = await asyncio.wait_for(connect(address=d['host'], device_id=d['device_id'], local_key=d['local_key'],
                protocol_version=float(d.get('protocol_version', 3.3)), enable_debug=True, timeout=t), timeout=t + 1)
            res = await p.detect_available_dps(); return {"status": res, "tech_logs": "\\n".join(h.records)}
        except Exception as e: return {"error": str(e), "tech_logs": "\\n".join(h.records)}
        finally:
            if p and p.transport:
                p.transport.close()
            logging.getLogger('pytuya').removeHandler(h)
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try: return jsonify(future.result(timeout=t+5))
    except Exception as e: return jsonify({"error": str(e)})

@app.route('/api/device/<dev_id>/cloud_check')
def api_cloud_check(dev_id):
    if TuyaCloudApi is None:
        return jsonify({"error": "LocalTuya cloud dependencies unavailable"}), 503
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
    if connect is None:
        return jsonify({"error": "LocalTuya core dependencies unavailable"}), 503
    devices = get_devices_data()
    d = devices.get(dev_id)
    if not d:
        return jsonify({"error": "Unknown device"}), 404
    req = request.json or {}
    async def _run():
        p = None
        try:
        p = await connect(address=d['host'], device_id=d['device_id'], local_key=d['local_key'], 
                          protocol_version=float(d.get('protocol_version', 3.3)), enable_debug=True, timeout=int(req.get('timeout', 10)))
            await p.detect_available_dps()
            await p.set_dps(req.get('dps', {}))
            await asyncio.sleep(0.5)
            return {"result": "ok"}
        finally:
            if p and p.transport:
                p.transport.close()
    
    future = asyncio.run_coroutine_threadsafe(_run(), loop)
    try: return jsonify(future.result(timeout=15))
    except Exception as e: return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
