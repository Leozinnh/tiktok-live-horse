@echo off
setlocal
chcp 65001 >nul 2>&1
title Processos - TikTok LIVE Horse

rem ---------------------------------------------------------------------------
rem  Lista os processos python/node da maquina, marca os que sao deste projeto
rem  e deixa voce ver os detalhes e encerrar - um por um ou todos de uma vez.
rem
rem  Este .bat carrega o proprio PowerShell: tudo abaixo da marca fica partido
rem  em duas strings de proposito, para o texto procurado nao aparecer antes,
rem  na parte que o cmd le.
rem ---------------------------------------------------------------------------

set "PSFILE=%TEMP%\tiktok_horse_processos.ps1"

powershell -NoProfile -ExecutionPolicy Bypass -Command "$t = Get-Content -LiteralPath '%~f0' -Raw -Encoding UTF8; $m = '#PS' + 'GO'; $i = $t.IndexOf($m); if ($i -lt 0) { Write-Host 'ERRO: marcador do PowerShell nao encontrado no .bat.' -ForegroundColor Red; exit 1 }; Set-Content -LiteralPath '%PSFILE%' -Value $t.Substring($i + 5) -Encoding UTF8"

set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
    echo.
    echo Nao consegui preparar o PowerShell ^(codigo %RC%^).
    pause
    exit /b %RC%
)

rem Passa o caminho do proprio .bat (%~f0, sem barra no fim) e o PowerShell
rem tira a pasta dali - assim a barra final nao escapa a aspa do argumento.
powershell -NoProfile -ExecutionPolicy Bypass -File "%PSFILE%" "%~f0"

del "%PSFILE%" >nul 2>&1

rem O exit /b aqui e obrigatorio: sem ele o cmd continuaria lendo o arquivo e
rem tentaria executar o PowerShell como se fosse batch.
exit /b 0

#PSGO
param([string]$CaminhoBat = '')

$ErrorActionPreference = 'SilentlyContinue'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# A pasta sai do caminho do proprio .bat, para o script continuar valendo se o
# projeto for movido de lugar.
if ($CaminhoBat -and (Test-Path -LiteralPath $CaminhoBat)) {
    $Raiz = Split-Path -Parent $CaminhoBat
} else {
    $Raiz = (Get-Location).Path
}
$Raiz = $Raiz.TrimEnd('\')

$Porta   = 8000
$LogTemp = Join-Path $env:TEMP 'horse_server.log'

$script:DonoPorta = 0

# ---------------------------------------------------------------------------
#  Descobrir quem e quem
# ---------------------------------------------------------------------------

function Get-DonoDaPorta {
    # Quem esta ESCUTANDO na porta. E a identificacao mais forte que existe:
    # no horse, o servidor e o proprio 'python main.py', e a narracao (TTS)
    # roda DENTRO dele - encerrar este PID cala a voz na hora.
    param([int]$P)
    $c = Get-NetTCPConnection -State Listen -LocalPort $P -ErrorAction SilentlyContinue |
         Select-Object -First 1
    if ($c) { return [int]$c.OwningProcess }
    # Plano B: netstat, para maquina sem o modulo NetTCPIP.
    foreach ($l in (netstat -ano | Select-String ('[:\]]' + $P + '\s'))) {
        if ($l.Line -match 'LISTENING\s+(\d+)\s*$') { return [int]$matches[1] }
    }
    return 0
}

function Get-Classificacao {
    # Nem todo processo conta a que projeto pertence: 'python main.py' e o
    # comando de mais de um projeto desta maquina. Por isso existe a marca
    # '?': ela aparece no lugar de um palpite, e quem decide e voce.
    param($Proc)
    $cmd = [string]$Proc.CommandLine
    if ($Proc.ProcessId -eq $script:DonoPorta) { return @{ Marca = 'PROJETO'; Cor = 'Green' } }
    if ($cmd -like '*tiktok-live-horse*')      { return @{ Marca = 'PROJETO'; Cor = 'Green' } }
    if ($cmd -like '*tiktok-live-*')           { return @{ Marca = 'outro';   Cor = 'Yellow' } }
    if ($cmd -match '(?i)(main\.py|index\.js|voz\.py)') { return @{ Marca = '?'; Cor = 'DarkYellow' } }
    return @{ Marca = ''; Cor = 'DarkGray' }
}

function Get-Lista {
    $script:DonoPorta = Get-DonoDaPorta $Porta
    $filtro = "Name='python.exe' OR Name='pythonw.exe' OR Name='node.exe'"
    $itens = @()
    foreach ($p in (Get-CimInstance Win32_Process -Filter $filtro)) {
        $c = Get-Classificacao $p
        $inicio = '--:--'
        if ($p.CreationDate) { $inicio = ([datetime]$p.CreationDate).ToString('HH:mm') }
        $ordem = 3
        if     ($c.Marca -eq 'PROJETO') { $ordem = 0 }
        elseif ($c.Marca -eq 'outro')   { $ordem = 1 }
        elseif ($c.Marca -eq '?')       { $ordem = 2 }
        $itens += [pscustomobject]@{
            Ordem  = $ordem
            PID    = [int]$p.ProcessId
            Nome   = ([string]$p.Name) -replace '\.exe$', ''
            MB     = [int]($p.WorkingSetSize / 1MB)
            Inicio = $inicio
            Marca  = $c.Marca
            Cor    = $c.Cor
            Cmd    = ([string]$p.CommandLine).Trim()
        }
    }
    return @($itens | Sort-Object Ordem, PID)
}

function Get-AssinaturaWeb {
    # Confirma QUAL projeto atende a porta. Nao e enfeite: mais de um projeto
    # desta maquina usa a 8000, e o titulo da pagina e o que diz qual deles
    # esta no ar agora.
    if (-not $script:DonoPorta) { return '' }
    try {
        $r = Invoke-WebRequest -Uri ("http://localhost:{0}/" -f $Porta) -UseBasicParsing -TimeoutSec 3
        if ($r.Content -match '<title>(.*?)</title>') { return $matches[1].Trim() }
    } catch {}
    return ''
}

# ---------------------------------------------------------------------------
#  Tela
# ---------------------------------------------------------------------------

function Show-Cabecalho {
    Clear-Host
    Write-Host ''
    Write-Host '  ==============================================================================' -ForegroundColor DarkCyan
    Write-Host '    PROCESSOS DO TIKTOK LIVE HORSE' -ForegroundColor Cyan
    Write-Host '  ==============================================================================' -ForegroundColor DarkCyan
    Write-Host ("    Pasta : {0}" -f $Raiz) -ForegroundColor DarkGray
    if ($script:DonoPorta) {
        Write-Host ("    Porta {0} : OCUPADA pelo PID {1}" -f $Porta, $script:DonoPorta) -ForegroundColor Green
        $ass = Get-AssinaturaWeb
        if ($ass) { Write-Host ("                responde como: {0}" -f $ass) -ForegroundColor Green }
    } else {
        Write-Host ("    Porta {0} : livre - nenhum servidor do horse no ar" -f $Porta) -ForegroundColor DarkGray
    }
}

function Show-Lista {
    param($Itens)
    Write-Host ''
    Write-Host '    MARCA      PID  PROC       MB  INICIO  COMANDO' -ForegroundColor DarkCyan
    Write-Host '    ------------------------------------------------------------------------' -ForegroundColor DarkCyan
    if (-not $Itens) {
        Write-Host '    (nenhum processo python ou node rodando)' -ForegroundColor DarkGray
    }
    foreach ($i in $Itens) {
        $cmd = $i.Cmd
        if ($cmd.Length -gt 52) { $cmd = $cmd.Substring(0, 49) + '...' }
        Write-Host ('    {0,-9} {1,5}  {2,-8} {3,4}  {4}  ' -f $i.Marca, $i.PID, $i.Nome, $i.MB, $i.Inicio) -NoNewline -ForegroundColor $i.Cor
        Write-Host $cmd -ForegroundColor DarkGray
    }
    $doProjeto = @($Itens | Where-Object { $_.Marca -eq 'PROJETO' })
    Write-Host ''
    Write-Host ("    {0} processo(s) marcado(s) PROJETO." -f $doProjeto.Count) -ForegroundColor Green
    Write-Host '    PROJETO = dono da porta ou caminho do horse na linha de comando.' -ForegroundColor DarkGray
    Write-Host '    ?       = nome de arquivo sem pasta; pode ser de outro projeto seu.' -ForegroundColor DarkYellow
}

function Show-Menu {
    Write-Host ''
    Write-Host '    [1] Atualizar a lista' -ForegroundColor White
    Write-Host '    [2] Detalhes de um processo (pelo PID)' -ForegroundColor White
    Write-Host '    [3] Encerrar um processo (pelo PID)' -ForegroundColor White
    Write-Host '    [4] Encerrar quem esta na porta 8000' -ForegroundColor White
    Write-Host '    [5] Encerrar TODOS os processos do horse' -ForegroundColor White
    Write-Host '    [6] Ver o log do servidor' -ForegroundColor White
    Write-Host '    [7] Abrir o Gerenciador de Tarefas' -ForegroundColor White
    Write-Host '    [0] Sair' -ForegroundColor White
    Write-Host ''
}

# ---------------------------------------------------------------------------
#  Detalhes e encerramento
# ---------------------------------------------------------------------------

function Show-Detalhes {
    param([int]$AlvoPid)
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$AlvoPid"
    if (-not $p) { Write-Host ("    Nao existe processo com PID {0}." -f $AlvoPid) -ForegroundColor Yellow; return }
    Write-Host ''
    Write-Host ("    PID    : {0}" -f $p.ProcessId) -ForegroundColor White
    Write-Host ("    Nome   : {0}" -f $p.Name) -ForegroundColor White
    Write-Host ("    Exec   : {0}" -f $p.ExecutablePath) -ForegroundColor DarkGray
    Write-Host ("    Inicio : {0}" -f $p.CreationDate) -ForegroundColor DarkGray
    Write-Host ("    Memoria: {0} MB" -f [int]($p.WorkingSetSize / 1MB)) -ForegroundColor DarkGray
    if ($p.ProcessId -eq $script:DonoPorta) {
        Write-Host ("    Porta  : {0} (e este quem atende)" -f $Porta) -ForegroundColor Green
    }
    $ass = Get-AssinaturaWeb
    if ($ass) { Write-Host ("    Responde: {0}" -f $ass) -ForegroundColor Green }
    Write-Host ''
    Write-Host '    Linha de comando:' -ForegroundColor DarkCyan
    Write-Host ("      {0}" -f $p.CommandLine) -ForegroundColor Gray

    # A cadeia de pais e o que explica um processo que "nao foi voce quem abriu":
    # ele fica orfao quando o terminal que o largou ja morreu.
    Write-Host ''
    Write-Host '    Quem abriu (cadeia de pais):' -ForegroundColor DarkCyan
    $atual = $p
    for ($n = 1; $n -le 3; $n++) {
        if (-not $atual.ParentProcessId -or $atual.ParentProcessId -eq 0) { break }
        $pai = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $atual.ParentProcessId)
        if (-not $pai) {
            Write-Host ("      {0}. PID {1} - ja morreu (processo ficou orfao)" -f $n, $atual.ParentProcessId) -ForegroundColor DarkYellow
            break
        }
        Write-Host ("      {0}. PID {1} {2}" -f $n, $pai.ProcessId, $pai.Name) -ForegroundColor Gray
        $cmdPai = [string]$pai.CommandLine
        if ($cmdPai.Length -gt 64) { $cmdPai = $cmdPai.Substring(0, 61) + '...' }
        Write-Host ("         {0}" -f $cmdPai) -ForegroundColor DarkGray
        $atual = $pai
    }
}

function Stop-Alvo {
    param([int]$AlvoPid, [string]$Aviso = '')
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$AlvoPid"
    if (-not $p) { Write-Host ("    Nao existe processo com PID {0}." -f $AlvoPid) -ForegroundColor Yellow; return $false }
    Write-Host ''
    Write-Host ("    Vai encerrar: PID {0}  {1}" -f $p.ProcessId, $p.Name) -ForegroundColor White
    Write-Host ("      {0}" -f $p.CommandLine) -ForegroundColor DarkGray
    if ($Aviso) { Write-Host ("    {0}" -f $Aviso) -ForegroundColor Yellow }
    if ((Read-Host '    Confirma? (s/N)') -notmatch '^(s|sim|y)$') {
        Write-Host '    Cancelado.' -ForegroundColor DarkGray
        return $false
    }
    Stop-Process -Id $AlvoPid -Force
    Start-Sleep -Milliseconds 500
    if (Get-Process -Id $AlvoPid -ErrorAction SilentlyContinue) {
        Write-Host '    NAO consegui encerrar. Tente rodar este .bat como Administrador.' -ForegroundColor Red
        return $false
    }
    Write-Host '    Encerrado.' -ForegroundColor Green
    return $true
}

function Stop-Projeto {
    param($Itens)
    $alvos = @($Itens | Where-Object { $_.Marca -eq 'PROJETO' })
    if (-not $alvos) { Write-Host '    Nenhum processo do horse rodando.' -ForegroundColor DarkGray; return }
    Write-Host ''
    Write-Host '    Vao ser encerrados:' -ForegroundColor White
    foreach ($a in $alvos) {
        Write-Host ("      PID {0,-6} {1,-8} {2}" -f $a.PID, $a.Nome, $a.Cmd) -ForegroundColor Gray
    }
    Write-Host '    A narracao (TTS) para junto: ela roda dentro do processo do servidor.' -ForegroundColor DarkGray
    if ((Read-Host '    Confirma? (s/N)') -notmatch '^(s|sim|y)$') {
        Write-Host '    Cancelado.' -ForegroundColor DarkGray
        return
    }
    foreach ($a in $alvos) {
        Stop-Process -Id $a.PID -Force
        Write-Host ("    PID {0} encerrado." -f $a.PID) -ForegroundColor Green
    }
}

function Show-Log {
    if (-not (Test-Path -LiteralPath $LogTemp)) {
        Write-Host ''
        Write-Host ("    Nao achei o log em {0}" -f $LogTemp) -ForegroundColor DarkYellow
        Write-Host '    (ele so existe quando o servidor foi subido com a saida redirecionada)' -ForegroundColor DarkGray
        return
    }
    Write-Host ''
    Write-Host ("    Ultimas 30 linhas de {0}" -f $LogTemp) -ForegroundColor DarkCyan
    Write-Host '    ------------------------------------------------------------------------' -ForegroundColor DarkCyan
    # -Encoding UTF8 e obrigatorio: o jogo reconfigura o stdout para UTF-8, e
    # sem isto o PowerShell le como cp1252 e imprime 'ParabÃ©ns' no lugar de
    # 'Parabens' - acentuacao e emoji viram lixo.
    Get-Content -LiteralPath $LogTemp -Tail 30 -Encoding UTF8 |
        ForEach-Object { Write-Host ("    {0}" -f $_) -ForegroundColor Gray }
}

# ---------------------------------------------------------------------------
#  Laco principal
# ---------------------------------------------------------------------------

function Show-Tela {
    # A lista vem ANTES do cabecalho de proposito: e ela que descobre quem
    # esta na porta, e o cabecalho mostra esse dado. Na ordem inversa o
    # cabecalho anunciaria a porta livre com o servidor vivo logo abaixo.
    $script:Lista = Get-Lista
    Show-Cabecalho
    Show-Lista $script:Lista
}

Show-Tela

# Uma bandeira, e nao 'break': dentro de um switch o break sai do switch, nao
# do while - o menu fecharia a tela e voltaria a perguntar.
$sair = $false
while (-not $sair) {
    Show-Menu
    $opcao = (Read-Host '    Opcao').Trim()

    switch ($opcao) {
        '1' { Show-Tela }
        '2' {
            $t = (Read-Host '    PID').Trim()
            if ($t -match '^\d+$') { Show-Detalhes ([int]$t) }
            else { Write-Host '    Digite so o numero do PID.' -ForegroundColor Yellow }
        }
        '3' {
            $t = (Read-Host '    PID').Trim()
            if ($t -match '^\d+$') {
                $aviso = ''
                if ([int]$t -eq $script:DonoPorta) { $aviso = 'Este e o servidor: a narracao para junto.' }
                Stop-Alvo ([int]$t) $aviso
            } else {
                Write-Host '    Digite so o numero do PID.' -ForegroundColor Yellow
            }
        }
        '4' {
            if (-not $script:DonoPorta) {
                Write-Host ("    A porta {0} esta livre - nao ha servidor para encerrar." -f $Porta) -ForegroundColor DarkGray
            } else {
                $ass = Get-AssinaturaWeb
                if ($ass) { Write-Host ("    Quem atende a porta: {0}" -f $ass) -ForegroundColor Gray }
                Stop-Alvo $script:DonoPorta 'Este e o servidor: a narracao para junto.' | Out-Null
            }
        }
        '5' {
            Show-Tela
            Stop-Projeto $script:Lista
        }
        '6' { Show-Log }
        '7' {
            Start-Process taskmgr.exe
            Write-Host '    Gerenciador de Tarefas aberto.' -ForegroundColor Green
        }
        '0' { $sair = $true }
        default { Write-Host '    Opcao invalida.' -ForegroundColor Yellow }
    }
}

Write-Host ''
Write-Host '    Ate a proxima.' -ForegroundColor DarkGray
