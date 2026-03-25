import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import render_template_string
from app.models import Setting

EMAIL_TEMPLATE = """\
<h2>檔案掃描結果報告</h2>
<p>您好，以下是您上傳檔案的掃描結果：</p>
{% for item in results %}
<hr>
<h3>{{ item.filename }}</h3>
{% if item.get('parent') %}
<p><em>（來自壓縮檔：{{ item.parent }}）</em></p>
{% endif %}
<p>
  <b>MD5:</b> {{ item.hashes.md5 }}<br>
  <b>SHA1:</b> {{ item.hashes.sha1 }}<br>
  <b>SHA256:</b> {{ item.hashes.sha256 }}
</p>

<h4>MISP 查詢結果</h4>
{% if item.misp.get('error') %}
<p>錯誤: {{ item.misp.error }}</p>
{% elif item.misp.found %}
<p style="color:red"><b>&#9888; 在MISP中發現 {{ item.misp.events|length }} 個相關事件！</b></p>
<ul>
{% for ev in item.misp.events %}
  <li>[{{ ev.id }}] {{ ev.info }} ({{ ev.date }})</li>
{% endfor %}
</ul>
{% else %}
<p style="color:green">&#10003; MISP中未發現威脅。</p>
{% endif %}

<h4>VirusTotal 查詢結果</h4>
{% if item.vt.get('error') %}
<p>錯誤: {{ item.vt.error }}</p>
{% elif item.vt.found %}
<p>惡意偵測:
  <b style="color:{% if item.vt.malicious > 0 %}red{% else %}green{% endif %}">
    {{ item.vt.malicious }}/{{ item.vt.total }}
  </b>
  {% if item.vt.name %}（{{ item.vt.name }}）{% endif %}
</p>
{% else %}
<p>{{ item.vt.get('message', '未找到') }}</p>
{% endif %}

{% if item.get('archive_note') %}
<p><em>備註: {{ item.archive_note }}</em></p>
{% endif %}
{% endfor %}
<hr>
<p>此郵件由 Uploader4MISP 自動發送。</p>
"""


def send_results_email(app, recipient_email, filename, results):
    """Send scan results to recipient_email in a background thread.

    Silently skips if recipient_email is empty or not configured.
    """
    if not recipient_email or recipient_email.strip() == '':
        app.logger.debug('No email configured for user, skipping email notification')
        return

    def _send():
        with app.app_context():
            try:
                cfg = _get_mail_config()
                html = render_template_string(EMAIL_TEMPLATE, results=results)

                msg = MIMEMultipart('alternative')
                msg['Subject'] = f'[掃描結果] {filename}'
                msg['From'] = cfg['sender']
                msg['To'] = recipient_email
                msg.attach(MIMEText(html, 'html', 'utf-8'))

                port = cfg['port']
                host = cfg['server']

                # Choose SMTP connection type based on port:
                # port 465  → SMTP_SSL (implicit TLS)
                # port 587  → SMTP + STARTTLS
                # port 25 or other → plain SMTP (no TLS)
                if port == 465:
                    smtp = smtplib.SMTP_SSL(host, port)
                elif port == 587:
                    smtp = smtplib.SMTP(host, port)
                    smtp.starttls()
                else:
                    # port 25 (corporate SMTP) — plain SMTP, no TLS
                    smtp = smtplib.SMTP(host, port)

                if cfg['username'] and cfg['password']:
                    smtp.login(cfg['username'], cfg['password'])

                smtp.sendmail(cfg['sender'], [recipient_email], msg.as_bytes())
                smtp.quit()
                app.logger.info(f'Email sent to {recipient_email} for {filename}')
            except Exception as e:
                app.logger.error(f'Email sending failed: {e}')

    t = threading.Thread(target=_send, daemon=True)
    t.start()


def _get_mail_config():
    """Read SMTP settings from the database."""
    return {
        'server':   Setting.get('MAIL_SERVER', 'localhost'),
        'port':     int(Setting.get('MAIL_PORT', 25)),
        'username': Setting.get('MAIL_USERNAME', ''),
        'password': Setting.get('MAIL_PASSWORD', ''),
        'sender':   Setting.get('MAIL_SENDER', 'uploader4misp@localhost'),
    }
