# 클로드 한글(HWP) 문서 키트 설치 스크립트
# '설치하기.bat' 을 더블클릭하면 이 파일이 실행됩니다.
# 하는 일: 한글·Python 확인 → 필요한 부품(pyhwpx) 설치 → 클로드 스킬 복사
#          → '문서\HWP자동화' 작업 폴더 만들기 → 시험 변환

param(
    [string]$SkillsDir = (Join-Path $env:USERPROFILE ".claude\skills"),
    [string]$WorkDir = (Join-Path ([Environment]::GetFolderPath("MyDocuments")) "HWP자동화"),
    [switch]$SkipTest,
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"
$Kit = Split-Path -Parent $MyInvocation.MyCommand.Path
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$env:PYTHONIOENCODING = "utf-8"

function Step($n, $msg) { Write-Host ""; Write-Host "[$n/6] $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "   OK  $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "   !!  $msg" -ForegroundColor Yellow }
function Fail($msg) {
    Write-Host ""
    Write-Host "   설치를 멈췄습니다: $msg" -ForegroundColor Red
    Write-Host "   가이드의 '문제 해결' 부분을 참고하거나, 이 화면을 캡처해 Claude에게 보여 주세요."
    exit 1
}

Write-Host "=============================================="
Write-Host "   클로드 한글(HWP) 문서 키트 설치"
Write-Host "=============================================="

# 인터넷에서 받은 파일 차단 해제 (스크립트 실행 경고 방지)
Get-ChildItem -Path $Kit -Recurse -File | Unblock-File -ErrorAction SilentlyContinue

# ---------------------------------------------------------------- 1. 한글
Step 1 "한컴 한글 설치 확인"
if (Test-Path "Registry::HKEY_CLASSES_ROOT\HWPFrame.HwpObject") {
    Ok "한글이 설치되어 있습니다."
} else {
    Fail "한컴 한글이 설치되어 있지 않습니다. 한글(한컴오피스)을 먼저 설치한 뒤 다시 실행해 주세요."
}

# ---------------------------------------------------------------- 2. Python
Step 2 "Python 확인"
function Find-Python {
    foreach ($cmd in @("python", "py")) {
        try {
            $v = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0 -and "$v" -match "Python 3\.(\d+)") {
                if ([int]$Matches[1] -ge 9) { return $cmd }
            }
        } catch {}
    }
    return $null
}
function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $user = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$machine;$user"
}

$py = Find-Python
if (-not $py) {
    Warn "Python이 없습니다. 지금 자동으로 설치할까요? (약 2~5분)"
    $ans = Read-Host "   설치하려면 Y 를 입력하고 Enter"
    if ($ans -notmatch "^[Yy]") { Fail "Python 설치를 건너뛰었습니다. https://www.python.org 에서 설치한 뒤 다시 실행해 주세요." }
    try {
        winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    } catch {
        Fail "자동 설치에 실패했습니다. https://www.python.org/downloads 에서 설치할 때 'Add python.exe to PATH' 에 체크해 주세요."
    }
    Refresh-Path
    $py = Find-Python
    if (-not $py) { Fail "Python을 설치했지만 아직 인식되지 않습니다. 컴퓨터를 다시 시작한 뒤 설치하기.bat 을 한 번 더 실행해 주세요." }
}
Ok ("Python 사용: " + (& $py --version 2>&1))

# ---------------------------------------------------------------- 3. 부품 설치
Step 3 "한글 자동화 부품(pyhwpx, pywin32) 설치"
& $py -m pip install --upgrade --disable-pip-version-check pyhwpx pywin32
if ($LASTEXITCODE -ne 0) { Fail "부품 설치에 실패했습니다. 인터넷 연결(학교 방화벽)을 확인해 주세요." }
& $py -c "import pyhwpx, win32com.client" 2>$null
if ($LASTEXITCODE -ne 0) { Fail "부품을 설치했지만 불러오지 못했습니다." }
Ok "부품 설치 완료"

# ---------------------------------------------------------------- 4. 스킬
Step 4 "Claude 스킬(school-hwp-docs) 설치"
$src = Join-Path $Kit "skill\school-hwp-docs"
$dst = Join-Path $SkillsDir "school-hwp-docs"
New-Item -ItemType Directory -Force $SkillsDir | Out-Null
if (Test-Path $dst) {
    $bak = "$dst.backup-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Move-Item $dst $bak
    Warn "이전 스킬은 백업했습니다: $bak"
}
Copy-Item $src $dst -Recurse
Ok "설치 위치: $dst"

# ---------------------------------------------------------------- 5. 작업 폴더
Step 5 "작업 폴더 만들기"
New-Item -ItemType Directory -Force $WorkDir | Out-Null
Copy-Item (Join-Path $src "scripts\md2hwp.py") $WorkDir -Force
$sample = Join-Path $Kit "예시\영어_기초학력_운영방안.md"
if (Test-Path $sample) { Copy-Item $sample (Join-Path $WorkDir "예시_원고.md") -Force }
Ok "작업 폴더: $WorkDir"

if (-not $NoShortcut) {
    try {
        $desk = [Environment]::GetFolderPath("Desktop")
        $lnk = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desk "HWP자동화 폴더.lnk"))
        $lnk.TargetPath = $WorkDir
        $lnk.Save()
        Ok "바탕 화면에 'HWP자동화 폴더' 바로가기를 만들었습니다."
    } catch { Warn "바탕 화면 바로가기는 만들지 못했습니다(설치에는 지장 없음)." }
}

# ---------------------------------------------------------------- 6. 시험 변환
Step 6 "시험 변환 (한글이 잠시 백그라운드로 실행됩니다)"
if ($SkipTest) {
    Warn "시험 변환을 건너뛰었습니다."
} else {
    $testMd = Join-Path $WorkDir "설치확인.md"
    $text = "# 설치 확인 문서`n`n## 1. 결과`n`n- 이 문서가 보이면 설치가 정상적으로 끝난 것입니다.`n`n| 항목 | 상태 |`n|---|---|`n| 한글 연결 | 정상 |`n| 스킬 설치 | 정상 |`n"
    [IO.File]::WriteAllText($testMd, $text, (New-Object Text.UTF8Encoding $false))
    & $py (Join-Path $dst "scripts\md2hwp.py") $testMd (Join-Path $WorkDir "설치확인.hwp")
    if ($LASTEXITCODE -ne 0) {
        Warn "시험 변환에 실패했습니다. 한글 '보안 승인' 창이 떠 있다면 '모두 허용'을 누르고 다시 실행해 보세요."
    } else {
        Ok "시험 문서 생성: $(Join-Path $WorkDir '설치확인.hwp')"
    }
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "   설치가 끝났습니다!" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host " 다음 순서:"
Write-Host "  1) Claude 데스크톱 앱을 열고 'Code' 탭을 누릅니다."
Write-Host "  2) 폴더로 '$WorkDir' 를 선택합니다."
Write-Host "  3) 이렇게 요청해 보세요:"
Write-Host "     '2027학년도 독서 동아리 운영 계획서를 3쪽 이내 한글 문서로 만들어 줘'"
Write-Host ""
