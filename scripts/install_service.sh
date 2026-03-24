#!/usr/bin/env bash
# =============================================================================
# install_service.sh — 將 Uploader4MISP 安裝為 Ubuntu systemd 服務
# 需以 root（或 sudo）執行
# =============================================================================
set -euo pipefail

INSTALL_DIR="/opt/Uploader4MISP"
SERVICE_NAME="uploader4misp"
SERVICE_FILE="${SERVICE_NAME}.service"
RUN_USER="www-data"

# --------------------------------------------------------------------------
# 1. 複製專案檔案（若尚未複製）
# --------------------------------------------------------------------------
if [ ! -d "$INSTALL_DIR" ]; then
    echo "[1/5] 建立安裝目錄 $INSTALL_DIR ..."
    mkdir -p "$INSTALL_DIR"
    cp -r . "$INSTALL_DIR"
else
    echo "[1/5] 安裝目錄已存在，跳過複製。"
fi

# --------------------------------------------------------------------------
# 2. 建立 Python 虛擬環境並安裝相依套件
# --------------------------------------------------------------------------
echo "[2/5] 建立虛擬環境並安裝相依套件 ..."
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# --------------------------------------------------------------------------
# 3. 建立必要目錄並調整擁有者
# --------------------------------------------------------------------------
echo "[3/5] 建立 instance 目錄並調整擁有者 ..."
mkdir -p "$INSTALL_DIR/instance/uploads" "$INSTALL_DIR/instance/temp" "$INSTALL_DIR/logs"
chown -R "$RUN_USER:$RUN_USER" "$INSTALL_DIR"

# --------------------------------------------------------------------------
# 4. 安裝 systemd service unit
# --------------------------------------------------------------------------
echo "[4/5] 安裝 systemd service ..."
# 將 service 檔案中的路徑替換為實際安裝路徑（若不同於預設）
sed "s|/opt/Uploader4MISP|${INSTALL_DIR}|g" \
    "$INSTALL_DIR/$SERVICE_FILE" \
    > "/etc/systemd/system/$SERVICE_FILE"

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

# --------------------------------------------------------------------------
# 5. 啟動服務
# --------------------------------------------------------------------------
echo "[5/5] 啟動 $SERVICE_NAME 服務 ..."
systemctl start "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "====================================================="
echo " 安裝完成！"
echo " 查看狀態：sudo systemctl status $SERVICE_NAME"
echo " 查看日誌：sudo journalctl -u $SERVICE_NAME -f"
echo " 停止服務：sudo systemctl stop $SERVICE_NAME"
echo " 重啟服務：sudo systemctl restart $SERVICE_NAME"
echo "====================================================="
echo ""
echo " 若需更改監聽 port，請編輯："
echo "   /etc/systemd/system/$SERVICE_FILE"
echo " 修改 Environment=\"PORT=5000\" 為所需 port，"
echo " 然後執行：sudo systemctl daemon-reload && sudo systemctl restart $SERVICE_NAME"
