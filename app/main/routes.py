import os
import uuid
import shutil
from flask import render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.main import main_bp
from app.main.hash_utils import compute_hashes
from app.main.archive_utils import is_archive, extract_archive
from app.main.misp_client import search_hash
from app.main.vt_client import lookup_hash
from app.main.email_utils import send_results_email


@main_bp.route('/', methods=['GET'])
@login_required
def index():
    return redirect(url_for('main.upload'))


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('請選擇檔案。', 'warning')
            return redirect(request.url)
        f = request.files['file']
        if f.filename == '':
            flash('請選擇檔案。', 'warning')
            return redirect(request.url)

        scan_id = str(uuid.uuid4())
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], scan_id)
        os.makedirs(upload_dir, exist_ok=True)

        safe_name = os.path.basename(f.filename)
        file_path = os.path.join(upload_dir, safe_name)
        f.save(file_path)

        results = []
        try:
            results = _process_file(
                file_path,
                safe_name,
                current_app.config['TEMP_FOLDER'],
                scan_id,
            )
        finally:
            # Cleanup uploaded file directory
            try:
                shutil.rmtree(upload_dir)
            except Exception:
                pass
            # Cleanup temp extraction directory
            temp_dir = os.path.join(current_app.config['TEMP_FOLDER'], scan_id)
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

        if current_user.email:
            send_results_email(
                current_app._get_current_object(),
                current_user.email,
                safe_name,
                results,
            )

        return render_template('main/results.html', results=results, filename=safe_name)

    return render_template('main/upload.html')


def _process_file(file_path, filename, temp_base, scan_id):
    """Hash the file, query MISP and VT, and if it's an archive also process inner files."""
    results = []

    hashes = compute_hashes(file_path)
    misp_result = search_hash(hashes['sha256'])
    vt_result = lookup_hash(hashes['sha256'])

    entry = {
        'filename': filename,
        'hashes': hashes,
        'misp': misp_result,
        'vt': vt_result,
        'is_archive': False,
    }
    results.append(entry)

    if is_archive(filename):
        entry['is_archive'] = True
        temp_dir = os.path.join(temp_base, scan_id)
        os.makedirs(temp_dir, exist_ok=True)

        extracted = extract_archive(file_path, temp_dir)

        if extracted is None:
            entry['archive_note'] = '壓縮檔有密碼保護或無法解壓縮，僅查詢壓縮檔本身。'
        elif len(extracted) == 0:
            entry['archive_note'] = '壓縮檔為空。'
        else:
            for ext_path in extracted:
                ext_name = os.path.relpath(ext_path, temp_dir)
                ext_hashes = compute_hashes(ext_path)
                ext_misp = search_hash(ext_hashes['sha256'])
                ext_vt = lookup_hash(ext_hashes['sha256'])
                results.append({
                    'filename': ext_name,
                    'hashes': ext_hashes,
                    'misp': ext_misp,
                    'vt': ext_vt,
                    'is_archive': False,
                    'parent': filename,
                })

    return results
