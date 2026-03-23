import requests
from app.models import Setting

VT_BASE = 'https://www.virustotal.com/api/v3'


def lookup_hash(sha256):
    """Query VirusTotal for a SHA256 hash.

    Returns a structured result dict with keys:
      - found (bool)
      - malicious, suspicious, undetected, harmless, total (int, when found)
      - name, type (str, when found)
      - error (str, on failure)
      - message (str, when not found)
    """
    api_key = Setting.get('VT_API_KEY')
    if not api_key:
        return {'error': 'VirusTotal API Key未設定', 'found': False}
    try:
        resp = requests.get(
            f'{VT_BASE}/files/{sha256}',
            headers={'x-apikey': api_key},
            timeout=30,
        )
        if resp.status_code == 404:
            return {'found': False, 'message': '在VirusTotal中未找到此檔案'}
        if resp.status_code != 200:
            return {'error': f'VT API錯誤: {resp.status_code}', 'found': False}
        data = resp.json().get('data', {}).get('attributes', {})
        stats = data.get('last_analysis_stats', {})
        return {
            'found': True,
            'malicious': stats.get('malicious', 0),
            'suspicious': stats.get('suspicious', 0),
            'undetected': stats.get('undetected', 0),
            'harmless': stats.get('harmless', 0),
            'total': sum(stats.values()),
            'name': data.get('meaningful_name', ''),
            'type': data.get('type_description', ''),
        }
    except Exception as e:
        return {'error': str(e), 'found': False}
