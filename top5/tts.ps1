Add-Type -AssemblyName System.Speech
$lines = Get-Content -Raw -Encoding UTF8 "$PSScriptRoot\narr.json" | ConvertFrom-Json
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Heami Desktop')
$s.Rate = 3
$i = 0
foreach ($t in $lines) {
  $s.SetOutputToWaveFile("$PSScriptRoot\voice\v$i.wav")
  $s.Speak($t)
  $i++
}
$s.Dispose()
