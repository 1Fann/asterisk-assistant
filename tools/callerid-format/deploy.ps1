param(
    [string]$AdbPath='adb',
    [string]$Serial,
    [string]$PythonPath='python'
)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$wheelName='phonenumberslite-9.0.42-py2.py3-none-any.whl'
$wheel=Join-Path $repoRoot ('.work\callerid-format\'+$wheelName)
& $PythonPath (Join-Path $PSScriptRoot 'download_dependency.py')
if($LASTEXITCODE -ne 0){throw 'Dependency download or checksum verification failed'}
$target=@();if($Serial){$target=@('-s',$Serial)}
function Invoke-AdbChecked([string[]]$Arguments){
    & $AdbPath @target @Arguments
    if($LASTEXITCODE -ne 0){throw 'ADB operation failed'}
}
Invoke-AdbChecked -Arguments @('shell','mkdir -p /data/local/tmp/callerid-format-upload')
try {
    Invoke-AdbChecked -Arguments @('push',(Join-Path $PSScriptRoot 'callerid_format.py'),'/data/local/tmp/callerid-format-upload/callerid_format.py')
    Invoke-AdbChecked -Arguments @('push',$wheel,('/data/local/tmp/callerid-format-upload/'+$wheelName))
    Invoke-AdbChecked -Arguments @('shell',"su -M -c 'mkdir -p /data/adb/asterisk-app/rootfs/tmp/callerid-format-upload && cp /data/local/tmp/callerid-format-upload/callerid_format.py /data/local/tmp/callerid-format-upload/$wheelName /data/adb/asterisk-app/rootfs/tmp/callerid-format-upload/'")
    Get-Content -Raw (Join-Path $PSScriptRoot 'install_on_phone.py') | & $AdbPath @target shell "su -M -c '/data/adb/asterisk-app/enter.sh /usr/bin/python3 -'"
    if($LASTEXITCODE -ne 0){throw 'Deployment refused or failed; see the message above'}
} finally {
    & $AdbPath @target shell 'rm -f /data/local/tmp/callerid-format-upload/callerid_format.py /data/local/tmp/callerid-format-upload/phonenumberslite-9.0.42-py2.py3-none-any.whl'
    & $AdbPath @target shell 'rmdir /data/local/tmp/callerid-format-upload'
    & $AdbPath @target shell "su -M -c 'rm -f /data/adb/asterisk-app/rootfs/tmp/callerid-format-upload/callerid_format.py /data/adb/asterisk-app/rootfs/tmp/callerid-format-upload/$wheelName; rmdir /data/adb/asterisk-app/rootfs/tmp/callerid-format-upload'"
}
