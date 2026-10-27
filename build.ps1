param(
    [string]$SdkRoot=$env:ANDROID_HOME,
    [string]$JavaHome=$env:JAVA_HOME
)
$ErrorActionPreference='Stop'
if(!$SdkRoot){$SdkRoot=Join-Path $env:LOCALAPPDATA 'Android\Sdk'}
if(!$JavaHome){throw 'Set JAVA_HOME or pass -JavaHome for JDK 21.'}
$sdk=$SdkRoot
$buildTools=Join-Path $sdk 'build-tools\36.0.0'
$javaBin=Join-Path $JavaHome 'bin'
$output=Join-Path $PSScriptRoot 'out'
New-Item -ItemType Directory -Force -Path $output,(Join-Path $PSScriptRoot 'private') | Out-Null
foreach($required in @((Join-Path $javaBin 'javac.exe'),(Join-Path $buildTools 'aapt2.exe'),(Join-Path $sdk 'platforms\android-35\android.jar'))){if(!(Test-Path -LiteralPath $required)){throw "Required build component missing: $required"}}
$key=Join-Path $PSScriptRoot 'private\asterisk-manager.jks'
$passwordFile=Join-Path $PSScriptRoot 'private\signing.password'
if(!(Test-Path -LiteralPath $passwordFile)){
    $bytes=New-Object byte[] 32
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
    $value=[Convert]::ToBase64String($bytes)
    [IO.File]::WriteAllText($passwordFile,$value,[Text.UTF8Encoding]::new($false))
}
$env:ASTERISK_SIGNING_PASSWORD=[IO.File]::ReadAllText($passwordFile)
$env:JAVA_HOME=$JavaHome
try {
    if(!(Test-Path -LiteralPath $key)){
        & (Join-Path $javaBin 'keytool.exe') -genkeypair -keystore $key -storepass:env ASTERISK_SIGNING_PASSWORD -keypass:env ASTERISK_SIGNING_PASSWORD -alias asterisk-manager -keyalg RSA -keysize 3072 -validity 3650 -dname 'CN=Asterisk Assistant' -noprompt 2>&1 | Out-Null
        if($LASTEXITCODE){throw 'Signing key generation failed'}
    }
    & (Join-Path $buildTools 'aapt2.exe') link --manifest (Join-Path $PSScriptRoot 'AndroidManifest.xml') -I (Join-Path $sdk 'platforms\android-35\android.jar') -o (Join-Path $output 'unsigned.apk')
    if($LASTEXITCODE){throw 'Manifest packaging failed'}
    $classes=Join-Path $output 'classes'
    $dex=Join-Path $output 'dex'
    New-Item -ItemType Directory -Force -Path $classes,$dex | Out-Null
    $sources=@(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'src') -Recurse -Filter '*.java' | ForEach-Object {$_.FullName})
    & (Join-Path $javaBin 'javac.exe') --release 8 -encoding UTF-8 -classpath (Join-Path $sdk 'platforms\android-35\android.jar') -d $classes @sources
    if($LASTEXITCODE){throw 'Java compilation failed'}
    $compiled=@(Get-ChildItem -LiteralPath $classes -Recurse -Filter '*.class' | ForEach-Object {$_.FullName})
    & (Join-Path $buildTools 'd8.bat') --min-api 31 --lib (Join-Path $sdk 'platforms\android-35\android.jar') --output $dex @compiled
    if($LASTEXITCODE){throw 'DEX compilation failed'}
    & (Join-Path $javaBin 'jar.exe') -uf (Join-Path $output 'unsigned.apk') -C $dex classes.dex
    if($LASTEXITCODE){throw 'DEX packaging failed'}
    $assetStage=Join-Path $output ('runtime-assets-'+[Guid]::NewGuid().ToString('N'))
    $runtimeStage=Join-Path $assetStage 'assets\runtime'
    New-Item -ItemType Directory -Force -Path $runtimeStage | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'assets\runtime') -File | Where-Object {$_.Extension -in '.sh','.py'} | Copy-Item -Destination $runtimeStage
    & (Join-Path $javaBin 'jar.exe') -uf (Join-Path $output 'unsigned.apk') -C $assetStage assets
    if($LASTEXITCODE){throw 'Runtime asset packaging failed'}
    & (Join-Path $buildTools 'zipalign.exe') -f 4 (Join-Path $output 'unsigned.apk') (Join-Path $output 'aligned.apk')
    if($LASTEXITCODE){throw 'APK alignment failed'}
    & (Join-Path $buildTools 'apksigner.bat') sign --ks $key --ks-key-alias asterisk-manager --ks-pass env:ASTERISK_SIGNING_PASSWORD --key-pass env:ASTERISK_SIGNING_PASSWORD --out (Join-Path $output 'Asterisk-Assistant-1.1.1.apk') (Join-Path $output 'aligned.apk')
    if($LASTEXITCODE){throw 'APK signing failed'}
    & (Join-Path $buildTools 'apksigner.bat') verify (Join-Path $output 'Asterisk-Assistant-1.1.1.apk')
    if($LASTEXITCODE){throw 'APK verification failed'}
    & (Join-Path $buildTools 'aapt2.exe') dump permissions (Join-Path $output 'Asterisk-Assistant-1.1.1.apk')
}finally{Remove-Item Env:ASTERISK_SIGNING_PASSWORD -ErrorAction SilentlyContinue}
