param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('State', 'CloseClean', 'Reopen', 'WatchReopen', 'Replace')]
    [string] $Action,
    [Parameter(Mandatory = $true)]
    [string] $TargetPath,
    [string] $FreezeSessionId,
    [string] $DocumentId,
    [string] $TransactionId,
    [int] $OperationIndex = -1,
    [string] $FreezeTokenPath,
    [string] $StagedSource,
    [string] $ExpectedOldHash,
    [string] $ExpectedNewHash,
    [switch] $ExpectedAbsence,
    [int] $TimeoutSeconds = 30
)

$ErrorActionPreference = 'Stop'

function Get-CanonicalPath([string] $Path) {
    return [IO.Path]::GetFullPath($Path).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
}

function Get-HashOrNull([string] $Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-PowerPointApp([switch] $Create) {
    try {
        return [Runtime.InteropServices.Marshal]::GetActiveObject('PowerPoint.Application')
    } catch {
        if (-not $Create) { return $null }
        return New-Object -ComObject PowerPoint.Application
    }
}

function Find-Presentation($App, [string] $CanonicalTarget) {
    if ($null -eq $App) { return $null }
    foreach ($presentation in $App.Presentations) {
        try {
            if ([string]::Equals((Get-CanonicalPath $presentation.FullName), $CanonicalTarget, [StringComparison]::OrdinalIgnoreCase)) {
                return $presentation
            }
        } catch { }
    }
    return $null
}

function Get-State($App, [string] $CanonicalTarget) {
    $presentation = Find-Presentation $App $CanonicalTarget
    if ($null -eq $presentation) {
        return @{ status = 'closed'; targetPath = $CanonicalTarget; openPresentations = $(if ($null -eq $App) { 0 } else { $App.Presentations.Count }) }
    }
    $saved = [bool] $presentation.Saved
    return @{
        status = $(if ($saved) { 'open-saved' } else { 'open-dirty' })
        targetPath = $CanonicalTarget
        fullName = (Get-CanonicalPath $presentation.FullName)
        openPresentations = $App.Presentations.Count
    }
}

function Write-Result([hashtable] $Result) {
    $Result | ConvertTo-Json -Compress -Depth 5
}

function Test-FreezeToken {
    if (-not $FreezeSessionId -or -not $DocumentId -or -not $TransactionId -or $OperationIndex -lt 0 -or -not $FreezeTokenPath) { return $false }
    try {
        $token = Get-Content -LiteralPath $FreezeTokenPath -Raw | ConvertFrom-Json
        return ($token.documentId -eq $DocumentId -and
                $token.freezeSessionId -eq $FreezeSessionId -and
                $token.transactionId -eq $TransactionId -and
                [int] $token.operationIndex -eq $OperationIndex -and
                $token.state -eq 'committing')
    } catch { return $false }
}

function Add-Correlation([hashtable] $Result) {
    $Result.documentId = $DocumentId
    $Result.freezeSessionId = $FreezeSessionId
    $Result.transactionId = $TransactionId
    $Result.operationIndex = $OperationIndex
    return $Result
}

$target = Get-CanonicalPath $TargetPath
$app = Get-PowerPointApp

try {
    switch ($Action) {
        'State' {
            Write-Result (Get-State $app $target)
        }
        'CloseClean' {
            if (-not $FreezeSessionId) { throw 'FreezeSessionId is required.' }
            $presentation = Find-Presentation $app $target
            if ($null -eq $presentation) {
                Write-Result @{ status = 'NOT_MUTATED'; reason = 'already-closed'; freezeSessionId = $FreezeSessionId }
                break
            }
            if (-not [bool] $presentation.Saved) {
                Write-Result @{ status = 'NOT_MUTATED'; reason = 'open-dirty'; freezeSessionId = $FreezeSessionId }
                break
            }
            $presentation.Close()
            $after = Get-State $app $target
            if ($after.status -eq 'closed') {
                $after.status = 'CLOSED_CLEAN'
                $after.freezeSessionId = $FreezeSessionId
            } else {
                $after.status = 'UNKNOWN'
                $after.freezeSessionId = $FreezeSessionId
            }
            Write-Result $after
        }
        'Reopen' {
            if (-not $FreezeSessionId) { throw 'FreezeSessionId is required.' }
            if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { throw 'Target file does not exist.' }
            if ($null -eq $app) { $app = Get-PowerPointApp -Create }
            $existing = Find-Presentation $app $target
            if ($null -eq $existing) { $null = $app.Presentations.Open($target, $false, $false, $true) }
            $opened = Find-Presentation $app $target
            if ($null -eq $opened -or (Get-CanonicalPath $opened.FullName) -ne $target) {
                Write-Result @{ status = 'UNKNOWN'; freezeSessionId = $FreezeSessionId; reason = 'exact-path-reopen-not-confirmed' }
            } else {
                Write-Result @{ status = 'REOPENED'; freezeSessionId = $FreezeSessionId; fullName = (Get-CanonicalPath $opened.FullName); openPresentations = $app.Presentations.Count }
            }
        }
        'WatchReopen' {
            if (-not $FreezeSessionId) { throw 'FreezeSessionId is required.' }
            $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
            while ([DateTime]::UtcNow -lt $deadline) {
                $app = Get-PowerPointApp
                $presentation = Find-Presentation $app $target
                if ($null -ne $presentation) {
                    Write-Result @{ status = 'REOPENED'; freezeSessionId = $FreezeSessionId; fullName = (Get-CanonicalPath $presentation.FullName); openPresentations = $app.Presentations.Count }
                    break
                }
                Start-Sleep -Milliseconds 250
            }
            if ([DateTime]::UtcNow -ge $deadline) {
                Write-Result @{ status = 'NOT_MUTATED'; freezeSessionId = $FreezeSessionId; reason = 'reopen-not-observed-before-timeout' }
            }
        }
        'Replace' {
            if (-not (Test-FreezeToken)) {
                Write-Result (Add-Correlation @{ status = 'NOT_MUTATED'; reason = 'freeze-token-mismatch' })
                break
            }
            if (-not $StagedSource) { throw 'StagedSource is required.' }
            $stage = Get-CanonicalPath $StagedSource
            if (-not (Test-Path -LiteralPath $stage -PathType Leaf)) { throw 'Staged source does not exist.' }
            if ($null -ne (Find-Presentation $app $target)) {
                Write-Result @{ status = 'NOT_MUTATED'; freezeSessionId = $FreezeSessionId; reason = 'target-open-in-powerpoint' }
                break
            }
            $oldHash = Get-HashOrNull $target
            if ($ExpectedAbsence) {
                if ($null -ne $oldHash) { Write-Result @{ status = 'NOT_MUTATED'; freezeSessionId = $FreezeSessionId; reason = 'expected-absence-failed' }; break }
            } elseif (-not $ExpectedOldHash -or $oldHash -ne $ExpectedOldHash.ToLowerInvariant()) {
                Write-Result @{ status = 'NOT_MUTATED'; freezeSessionId = $FreezeSessionId; reason = 'expected-old-hash-mismatch' }
                break
            }
            $stageHash = Get-HashOrNull $stage
            if (-not $ExpectedNewHash -or $stageHash -ne $ExpectedNewHash.ToLowerInvariant()) {
                Write-Result @{ status = 'NOT_MUTATED'; freezeSessionId = $FreezeSessionId; reason = 'staged-hash-mismatch' }
                break
            }
            $targetRoot = [IO.Path]::GetPathRoot($target)
            $stageRoot = [IO.Path]::GetPathRoot($stage)
            if (-not [string]::Equals($targetRoot, $stageRoot, [StringComparison]::OrdinalIgnoreCase)) {
                Write-Result (Add-Correlation @{ status = 'NOT_MUTATED'; reason = 'cross-volume-replace-not-atomic'; oldHash = $oldHash })
                break
            }
            if (-not (Test-FreezeToken)) {
                Write-Result (Add-Correlation @{ status = 'NOT_MUTATED'; reason = 'freeze-token-invalidated-before-replace' })
                break
            }
            if ($null -ne (Find-Presentation $app $target)) {
                Write-Result (Add-Correlation @{ status = 'NOT_MUTATED'; reason = 'target-reopened-before-replace' })
                break
            }
            try {
                if ($ExpectedAbsence) {
                    [IO.File]::Move($stage, $target)
                } else {
                    [IO.File]::Replace($stage, $target, $null, $true)
                }
            } catch {
                $currentHash = Get-HashOrNull $target
                if ($currentHash -eq $ExpectedNewHash.ToLowerInvariant()) {
                    Write-Result (Add-Correlation @{ status = 'MUTATED'; resultingHash = $currentHash })
                } elseif ($currentHash -eq $oldHash) {
                    Write-Result (Add-Correlation @{ status = 'NOT_MUTATED'; reason = $_.Exception.Message })
                } else {
                    Write-Result (Add-Correlation @{ status = 'UNKNOWN'; observedHash = $currentHash; reason = $_.Exception.Message })
                }
                break
            }
            $resultingHash = Get-HashOrNull $target
            if ($resultingHash -eq $ExpectedNewHash.ToLowerInvariant()) {
                Write-Result (Add-Correlation @{ status = 'MUTATED'; resultingHash = $resultingHash })
            } else {
                Write-Result (Add-Correlation @{ status = 'UNKNOWN'; observedHash = $resultingHash })
            }
        }
    }
} catch {
    Write-Result @{ status = 'UNKNOWN'; freezeSessionId = $FreezeSessionId; error = $_.Exception.Message }
}
