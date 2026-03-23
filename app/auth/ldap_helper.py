from ldap3 import Server, Connection, ALL, NTLM, SIMPLE
from app.models import Setting


def authenticate_ad(username, password):
    """Try to authenticate username/password against Active Directory.
    Returns True on success, False on failure."""
    server_addr = Setting.get('AD_SERVER')
    base_dn = Setting.get('AD_BASE_DN')
    bind_dn = Setting.get('AD_BIND_DN')
    bind_pw = Setting.get('AD_BIND_PW')
    ad_domain = Setting.get('AD_DOMAIN', '')

    if not server_addr or not base_dn:
        return False

    try:
        server = Server(server_addr, get_info=ALL)
        # Try NTLM first (DOMAIN\user), fallback to simple bind
        user_principal = f'{ad_domain}\\{username}' if ad_domain else username
        conn = Connection(
            server,
            user=user_principal,
            password=password,
            authentication=NTLM,
            auto_bind=True,
        )
        conn.unbind()
        return True
    except Exception:
        pass

    try:
        # Try UPN format user@domain
        if ad_domain:
            upn = f'{username}@{ad_domain}'
        else:
            upn = username
        server = Server(server_addr, get_info=ALL)
        conn = Connection(
            server,
            user=upn,
            password=password,
            authentication=SIMPLE,
            auto_bind=True,
        )
        conn.unbind()
        return True
    except Exception:
        return False
