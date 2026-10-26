$ErrorActionPreference = "Stop"

try {
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
    $inputJson = [Console]::In.ReadToEnd()
    $event = $inputJson | ConvertFrom-Json
    $prompt = [string]$event.prompt

    if ([string]::IsNullOrWhiteSpace($prompt)) {
        [Console]::Out.WriteLine("{}")
        exit 0
    }

    $timestamp = [string]$event.timestamp
    $date = if ($timestamp.Length -ge 10) { $timestamp.Substring(0, 10) } else { Get-Date -Format "yyyy-MM-dd" }
    $escapedPrompt = $prompt.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;")
    $escapedPrompt = $escapedPrompt.Replace("|", "\|").Replace("`r`n", "<br>").Replace("`n", "<br>").Replace("`r", "<br>")

    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $logPath = Join-Path $repoRoot "BITACORA_PROMPTS.md"
    $entry = "| $date | $escapedPrompt |`r`n"
    [System.IO.File]::AppendAllText($logPath, $entry, [System.Text.UTF8Encoding]::new($false))

    [Console]::Out.WriteLine("{}")
}
catch {
    [Console]::Error.WriteLine("No se pudo guardar el prompt en BITACORA_PROMPTS.md: $($_.Exception.Message)")
    exit 1
}
