import threading
from flask import render_template_string
from flask_mail import Message
from app import mail
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
    """Send scan results to recipient_email in a background thread."""
    if not recipient_email:
        return

    def _send():
        with app.app_context():
            try:
                _configure_mail(app)
                html = render_template_string(EMAIL_TEMPLATE, results=results)
                msg = Message(
                    subject=f'[掃描結果] {filename}',
                    recipients=[recipient_email],
                    html=html,
                )
                mail.send(msg)
            except Exception as e:
                app.logger.error(f'Email sending failed: {e}')

    t = threading.Thread(target=_send, daemon=True)
    t.start()


def _configure_mail(app):
    """Push SMTP settings from the database into Flask-Mail config."""
    app.config['MAIL_SERVER'] = Setting.get('MAIL_SERVER', 'localhost')
    app.config['MAIL_PORT'] = int(Setting.get('MAIL_PORT', 25))
    app.config['MAIL_USE_TLS'] = Setting.get('MAIL_USE_TLS', 'false').lower() == 'true'
    app.config['MAIL_USERNAME'] = Setting.get('MAIL_USERNAME', '')
    app.config['MAIL_PASSWORD'] = Setting.get('MAIL_PASSWORD', '')
    app.config['MAIL_DEFAULT_SENDER'] = Setting.get('MAIL_SENDER', 'uploader4misp@localhost')
