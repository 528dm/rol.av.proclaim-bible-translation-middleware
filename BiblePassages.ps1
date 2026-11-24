# Bible Passages - NIVUK / NVI side-by-side pairs
# Enter comma-separated passages; the app fetches each from BibleGateway and
# outputs two verses in one version, the same two verses in the other, then "---".
#
# Run:  double-click "Bible Passages.bat"
#  or:  powershell -STA -ExecutionPolicy Bypass -File BiblePassages.ps1
# Command-line test (no window):
#       powershell -ExecutionPolicy Bypass -File BiblePassages.ps1 -NoGui -Passages "John 3:16-18"

param(
    [switch]$NoGui,
    [string]$Passages
)

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ---------------------------------------------------------------- references
function Split-References([string]$text) {
    # Splits "John 3:16-18, 20, Romans 8:28; Psalm 23" into full references.
    # A part that is only numbers (e.g. "20" or "5:1-3") reuses the previous book
    # (and chapter, when it has no colon).
    $refs = @()
    $book = $null; $chapter = $null
    foreach ($raw in ($text -split '[,;\r\n]+')) {
        $p = ($raw -replace '\s+', ' ').Trim()
        if (-not $p) { continue }
        if ($p -match '^\d+(:\d+)?(\s*-\s*\d+(:\d+)?)?$') {
            if (-not $book) { $refs += $p; continue }
            if ($p -match ':' -or -not $chapter) { $refs += "$book $p" }
            else { $refs += "$book ${chapter}:$p" }
        } else {
            $refs += $p
        }
        $last = $refs[-1]
        if ($last -match '^(.*?[A-Za-z].*?)\s+(\d+)(?::\d+)?') {
            $book = $Matches[1]; $chapter = $Matches[2]
            # verse-only ranges without a colon mean whole chapters
            if ($last -notmatch ':') { $chapter = $null }
        }
    }
    return $refs
}

# ---------------------------------------------------------------- fetching
function Get-PassageHtml([string]$ref, [string]$version) {
    $url = 'https://www.biblegateway.com/passage/?search=' +
           [uri]::EscapeDataString($ref) + '&version=' + $version
    $wc = New-Object System.Net.WebClient
    $wc.Encoding = [System.Text.Encoding]::UTF8
    $wc.Headers.Add('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')
    try { return $wc.DownloadString($url) } finally { $wc.Dispose() }
}

function Get-Verses([string]$ref, [string]$version) {
    # Returns an ordered dictionary: "John-3-16" -> verse text
    $html = Get-PassageHtml $ref $version
    $start = $html.IndexOf("class='passage-content")
    if ($start -lt 0) { $start = $html.IndexOf('class="passage-content') }
    if ($start -lt 0) { throw "No passage found for '$ref' ($version)." }
    $body = $html.Substring($start)

    # cut off everything after the passage text
    foreach ($marker in @('class="footnotes"', 'class="crossrefs', 'class="full-chap-link"', 'class="passage-scroller')) {
        $i = $body.IndexOf($marker)
        if ($i -gt 0) { $body = $body.Substring(0, $i) }
    }
    $body = $body -replace '<[^>]*$', ''   # drop the half tag left by the cut

    $opt = [System.Text.RegularExpressions.RegexOptions]'Singleline, IgnoreCase'
    # remove headings, footnote/cross-ref markers, verse/chapter numbers, indent spacers
    $body = [regex]::Replace($body, '<h[1-6][^>]*>.*?</h[1-6]>', '', $opt)
    $body = [regex]::Replace($body, '<sup[^>]*class=[''"](footnote|crossreference)[''"][^>]*>.*?</sup>', '', $opt)
    $body = [regex]::Replace($body, '<sup[^>]*class=[''"]versenum[''"][^>]*>.*?</sup>', '', $opt)
    $body = [regex]::Replace($body, '<span[^>]*class=[''"]chapternum[''"][^>]*>.*?</span>', '', $opt)
    $body = [regex]::Replace($body, '<span[^>]*class=[''"]indent-\d+-breaks[''"][^>]*>.*?</span>', '', $opt)
    $body = [regex]::Replace($body, '<br\s*/?>', ' ', $opt)

    # every verse fragment starts with <span ... class="text Book-C-V">
    $verses = [ordered]@{}
    $markers = [regex]::Matches($body, '<span[^>]*class=[''"]text ([A-Za-z0-9]+-\d+-\d+)[''"][^>]*>', $opt)
    for ($k = 0; $k -lt $markers.Count; $k++) {
        $m = $markers[$k]
        $from = $m.Index + $m.Length
        $to = if ($k + 1 -lt $markers.Count) { $markers[$k + 1].Index } else { $body.Length }
        $chunk = $body.Substring($from, $to - $from)
        $chunk = [regex]::Replace($chunk, '<[^>]+>', '')
        $chunk = [System.Net.WebUtility]::HtmlDecode($chunk)
        $chunk = ($chunk -replace '[\s ]+', ' ').Trim()
        if (-not $chunk) { continue }
        $key = $m.Groups[1].Value
        if ($verses.Contains($key)) { $verses[$key] = ($verses[$key] + ' ' + $chunk).Trim() }
        else { $verses[$key] = $chunk }
    }
    if ($verses.Count -eq 0) { throw "No verses found for '$ref' ($version)." }
    return $verses
}

# ---------------------------------------------------------------- formatting
function Format-Line($keys, $verses, [bool]$numbers) {
    $parts = foreach ($k in $keys) {
        if (-not $verses.Contains($k)) { continue }
        $n = ($k -split '-')[-1]
        if ($numbers) { "$n $($verses[$k])" } else { $verses[$k] }
    }
    return ($parts -join ' ')
}

function Build-Output([string]$input_, [string]$first, [string]$second, [bool]$numbers, [scriptblock]$status) {
    $sb = New-Object System.Text.StringBuilder
    foreach ($ref in (Split-References $input_)) {
        if ($status) { & $status "Fetching $ref ..." }
        try {
            $a = Get-Verses $ref $first
            $b = Get-Verses $ref $second
        } catch {
            [void]$sb.AppendLine("[$ref] Error: $($_.Exception.Message)")
            [void]$sb.AppendLine('---')
            continue
        }
        # verse order from the first version, plus any extra verses only in the second
        $keys = @($a.Keys) + @($b.Keys | Where-Object { -not $a.Contains($_) })
        for ($i = 0; $i -lt $keys.Count; $i += 2) {
            $pair = $keys[$i..([Math]::Min($i + 1, $keys.Count - 1))]
            [void]$sb.AppendLine((Format-Line $pair $a $numbers))
            [void]$sb.AppendLine((Format-Line $pair $b $numbers))
            [void]$sb.AppendLine('---')
        }
    }
    return $sb.ToString()
}

# ---------------------------------------------------------------- command-line mode
if ($NoGui) {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Build-Output $Passages 'NIVUK' 'NVI' $true $null
    return
}

# ---------------------------------------------------------------- GUI
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Bible Passages - NIVUK / NVI'
$form.Size = New-Object System.Drawing.Size(820, 640)
$form.MinimumSize = New-Object System.Drawing.Size(560, 400)
$form.StartPosition = 'CenterScreen'
$form.Font = New-Object System.Drawing.Font('Segoe UI', 10)

$lbl = New-Object System.Windows.Forms.Label
$lbl.Text = 'Passages (comma separated), e.g.  John 3:16-18, Romans 8:28, Psalm 23'
$lbl.Location = New-Object System.Drawing.Point(12, 12)
$lbl.AutoSize = $true
$form.Controls.Add($lbl)

$txtIn = New-Object System.Windows.Forms.TextBox
$txtIn.Location = New-Object System.Drawing.Point(12, 38)
$txtIn.Size = New-Object System.Drawing.Size(680, 26)
$txtIn.Anchor = 'Top, Left, Right'
$form.Controls.Add($txtIn)

$btnGo = New-Object System.Windows.Forms.Button
$btnGo.Text = 'Get verses'
$btnGo.Location = New-Object System.Drawing.Point(700, 36)
$btnGo.Size = New-Object System.Drawing.Size(92, 30)
$btnGo.Anchor = 'Top, Right'
$form.Controls.Add($btnGo)
$form.AcceptButton = $btnGo

$lblOrder = New-Object System.Windows.Forms.Label
$lblOrder.Text = 'Show first:'
$lblOrder.Location = New-Object System.Drawing.Point(12, 76)
$lblOrder.AutoSize = $true
$form.Controls.Add($lblOrder)

$cboOrder = New-Object System.Windows.Forms.ComboBox
$cboOrder.DropDownStyle = 'DropDownList'
[void]$cboOrder.Items.AddRange(@('NIVUK (English)', 'NVI (Spanish)'))
$cboOrder.SelectedIndex = 0
$cboOrder.Location = New-Object System.Drawing.Point(90, 72)
$cboOrder.Size = New-Object System.Drawing.Size(150, 26)
$form.Controls.Add($cboOrder)

$chkNums = New-Object System.Windows.Forms.CheckBox
$chkNums.Text = 'Show verse numbers'
$chkNums.Checked = $true
$chkNums.Location = New-Object System.Drawing.Point(260, 74)
$chkNums.AutoSize = $true
$form.Controls.Add($chkNums)

$btnCopy = New-Object System.Windows.Forms.Button
$btnCopy.Text = 'Copy all'
$btnCopy.Location = New-Object System.Drawing.Point(700, 70)
$btnCopy.Size = New-Object System.Drawing.Size(92, 30)
$btnCopy.Anchor = 'Top, Right'
$form.Controls.Add($btnCopy)

$txtOut = New-Object System.Windows.Forms.TextBox
$txtOut.Multiline = $true
$txtOut.ScrollBars = 'Vertical'
$txtOut.WordWrap = $true
$txtOut.ReadOnly = $true
$txtOut.BackColor = [System.Drawing.Color]::White
$txtOut.Font = New-Object System.Drawing.Font('Segoe UI', 11)
$txtOut.Location = New-Object System.Drawing.Point(12, 110)
$txtOut.Size = New-Object System.Drawing.Size(780, 450)
$txtOut.Anchor = 'Top, Bottom, Left, Right'
$form.Controls.Add($txtOut)

$status = New-Object System.Windows.Forms.Label
$status.Text = 'Text from BibleGateway.com (internet connection required).'
$status.Location = New-Object System.Drawing.Point(12, 568)
$status.Size = New-Object System.Drawing.Size(780, 22)
$status.Anchor = 'Bottom, Left, Right'
$status.ForeColor = [System.Drawing.Color]::DimGray
$form.Controls.Add($status)

$btnGo.Add_Click({
    if (-not $txtIn.Text.Trim()) { $status.Text = 'Enter at least one passage.'; return }
    $first, $second = if ($cboOrder.SelectedIndex -eq 0) { 'NIVUK', 'NVI' } else { 'NVI', 'NIVUK' }
    $btnGo.Enabled = $false
    $form.Cursor = 'WaitCursor'
    $txtOut.Text = ''
    try {
        $setStatus = { param($m) $status.Text = $m; [System.Windows.Forms.Application]::DoEvents() }
        $result = Build-Output $txtIn.Text $first $second $chkNums.Checked $setStatus
        # Windows text boxes need CRLF line breaks
        $txtOut.Text = ($result -replace "`r?`n", "`r`n")
        $status.Text = 'Done.'
    } catch {
        $status.Text = "Error: $($_.Exception.Message)"
    } finally {
        $btnGo.Enabled = $true
        $form.Cursor = 'Default'
    }
})

$btnCopy.Add_Click({
    if ($txtOut.Text) {
        [System.Windows.Forms.Clipboard]::SetText($txtOut.Text)
        $status.Text = 'Copied to clipboard.'
    }
})

[void]$form.ShowDialog()
