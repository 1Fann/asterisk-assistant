param([Parameter(Mandatory=$true)][string]$Server,[int]$Port=16060)
$ErrorActionPreference='Stop'
$client=[Net.Sockets.UdpClient]::new()
try {
 $client.Client.ReceiveTimeout=2500
 $client.Connect($Server,$Port)
 $local=$client.Client.LocalEndPoint
 $id=[Guid]::NewGuid().ToString('N')
 $packet="REGISTER sip:${Server}:$Port SIP/2.0`r`nVia: SIP/2.0/UDP $($local.Address):$($local.Port);branch=z9hG4bK$id;rport`r`nMax-Forwards: 70`r`nFrom: <sip:1001@$Server>;tag=$id`r`nTo: <sip:1001@$Server>`r`nCall-ID: $id`r`nCSeq: 1 REGISTER`r`nContact: <sip:1001@$($local.Address):$($local.Port)>`r`nContent-Length: 0`r`n`r`n"
 $bytes=[Text.Encoding]::ASCII.GetBytes($packet)
 $remote=[Net.IPEndPoint]::new([Net.IPAddress]::Any,0)
 $passed=$false
 foreach($attempt in 1..3){
  [void]$client.Send($bytes,$bytes.Length)
  try{$reply=[Text.Encoding]::ASCII.GetString($client.Receive([ref]$remote));$status=($reply -split "`r`n")[0];$passed=$status -match '^SIP/2.0 401 ';if($passed){break}}catch{}
 }
 if(!$passed){throw 'LAN SIP challenge probe failed'}
 Write-Output "LAN SIP probe passed: $Server`:$Port replied 401 (expected authentication challenge)."
}finally{$client.Dispose()}
