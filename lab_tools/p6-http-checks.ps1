$ErrorActionPreference = 'Continue'
Write-Output 'HTTP REDIRECT'
curl.exe --noproxy '*' -I http://devops.local
Write-Output 'DEFAULT CERTIFICATE VERIFICATION'
curl.exe --noproxy '*' -I https://devops.local
Write-Output "curl_exit=$LASTEXITCODE"
Write-Output 'EXPLICIT TRUST'
curl.exe --noproxy '*' --cacert "$env:USERPROFILE\devops.crt" -i https://devops.local
Write-Output "curl_exit=$LASTEXITCODE"
Write-Output 'CUSTOM 404'
curl.exe --noproxy '*' --cacert "$env:USERPROFILE\devops.crt" -i https://devops.local/no-such-page
Write-Output 'VERBOSE TLS EXCHANGE'
curl.exe --noproxy '*' -v --cacert "$env:USERPROFILE\devops.crt" https://devops.local
foreach ($devopsHttpPath in @('/','/','/','/admin','/wp-login.php','/.env')) {
  curl.exe --noproxy '*' -s --cacert "$env:USERPROFILE\devops.crt" -o NUL "https://devops.local$devopsHttpPath"
}
curl.exe --noproxy '*' -s -o NUL http://devops.local/
