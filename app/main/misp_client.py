from app.models import Setting


def search_hash(hash_value):
    """Search MISP for a hash value.

    Returns a dict with keys:
      - found (bool)
      - events (list of dicts)
      - error (str, only on failure)
    """
    try:
        from pymisp import PyMISP
        url = Setting.get('MISP_URL')
        key = Setting.get('MISP_KEY')
        verify = Setting.get('MISP_VERIFYCERT', 'false').lower() == 'true'
        if not url or not key:
            return {'error': 'MISP未設定', 'found': False, 'events': []}

        # --- Proxy support ---
        # PyMISP passes proxies through to the underlying requests.Session.
        proxy_url = Setting.get('HTTPS_PROXY', '').strip()
        proxies = {'http': proxy_url, 'https': proxy_url} if proxy_url else None

        misp = PyMISP(url, key, verify, proxies=proxies)
        result = misp.search(
            value=hash_value,
            type_attribute='md5|sha1|sha256|filename|md5|filename|sha1|filename|sha256',
            pythonify=True,
        )
        if result and len(result) > 0:
            events = []
            for event in result:
                events.append({
                    'id': event.id,
                    'info': event.info,
                    'threat_level': event.threat_level_id,
                    'date': str(event.date),
                })
            return {'found': True, 'events': events}
        return {'found': False, 'events': []}
    except Exception as e:
        return {'error': str(e), 'found': False, 'events': []}
