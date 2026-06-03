param(
    [Parameter(Mandatory=$true)][string]$ClipsDir,
    [string]$StoreId = "ST1008"
)

$ApiUrl = $env:API_URL
if (-not $ApiUrl) {
    $ApiUrl = "http://localhost:8000"
}

$Date = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
Write-Host "[$Date] Starting pipeline for $StoreId"
Write-Host "[$Date] Clips dir: $ClipsDir"

# Since pos_transactions.csv is missing in data/, we will check if it exists, otherwise use the one in the root folder if we can find it
$PosFile = "data/pos_transactions.csv"
if (-not (Test-Path $PosFile)) {
    Write-Host "Warning: $PosFile not found. Looking for alternatives..."
    $AltPos = Get-ChildItem -Filter "*Brigade*.csv" | Select-Object -First 1
    if ($AltPos) {
        $PosFile = $AltPos.Name
        Write-Host "Using alternative POS file: $PosFile"
    } else {
        Write-Host "No POS file found, this might cause an error in detect.py"
    }
}

python pipeline/detect.py `
  --clips "$ClipsDir" `
  --store "$StoreId" `
  --layout "data/store_layout.json" `
  --pos "$PosFile" `
  --output "pipeline/output/"

$Date = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
Write-Host "[$Date] Detection complete. Replaying events to API..."

python pipeline/replay_events.py `
  --events "pipeline/output/${StoreId}_events.jsonl" `
  --api-base-url "$ApiUrl" `
  --speed 10

$Date = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
Write-Host "[$Date] Done. Check dashboard at http://localhost:3000"
