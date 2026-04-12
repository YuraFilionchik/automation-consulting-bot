# Deploy script - PowerShell
# Upload project to server and deploy
# IMPORTANT: Copy deploy_windows.config.ps1.EXAMPLE to deploy_windows.config.ps1 and fill in your credentials

$ConfigFile = "$PSScriptRoot\deploy_windows.config.ps1"
if (-not (Test-Path $ConfigFile)) {
    Write-Host "ERROR: Config file not found. Copy deploy_windows.config.ps1.EXAMPLE to deploy_windows.config.ps1" -ForegroundColor Red
    exit 1
}
. $ConfigFile

Write-Host "=== Uploading project to server ===" -ForegroundColor Cyan

# Create archive
$ArchivePath = "$env:TEMP\automation-bot.zip"
Compress-Archive -Path "$ProjectDir\*" -DestinationPath $ArchivePath -Force
Write-Host "Archive created: $ArchivePath"

# Upload via SCP
Write-Host "Uploading archive..."
scp -P $Port -o StrictHostKeyChecking=no $ArchivePath "${User}@${Server}:/tmp/automation-bot.zip"

# Deploy on server
Write-Host "Deploying on server..."
$DeployCommands = @"
cd $RemoteDir 2>/dev/null || mkdir -p $RemoteDir && cd $RemoteDir
unzip -o /tmp/automation-bot.zip
rm /tmp/automation-bot.zip

# Install Python and dependencies
apt update -y
apt install -y python3 python3-venv python3-pip git

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create directories
mkdir -p data logs backups

# Setup systemd service
cat > /etc/systemd/system/automation-bot.service << 'EOF'
[Unit]
Description=Automation Consulting Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$RemoteDir
ExecStart=$RemoteDir/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=append:$RemoteDir/logs/bot.log
StandardError=append:$RemoteDir/logs/bot-error.log
RuntimeMaxSec=86400

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable automation-bot.service
systemctl restart automation-bot.service

echo ""
echo "=== Deployment complete ==="
systemctl status automation-bot.service --no-pager -l
"@

# Save and execute
$DeployCommands | Out-File -FilePath "$env:TEMP\deploy-remote.sh" -Encoding ascii

Write-Host "Commands saved. Please run manually via SSH:" -ForegroundColor Yellow
Write-Host "ssh -p $Port $User@$Server" -ForegroundColor Green
Write-Host "Then paste the commands from $env:TEMP\deploy-remote.sh" -ForegroundColor Green
