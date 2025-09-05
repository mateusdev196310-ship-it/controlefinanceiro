# Script para instalar PostgreSQL no Windows
# Execute como Administrador

Write-Host "Baixando PostgreSQL..." -ForegroundColor Green

# URL do PostgreSQL para Windows (versão 15)
$url = "https://get.enterprisedb.com/postgresql/postgresql-15.8-1-windows-x64.exe"
$output = "$env:TEMP\postgresql-installer.exe"

# Baixar o instalador
Invoke-WebRequest -Uri $url -OutFile $output

Write-Host "Iniciando instalação do PostgreSQL..." -ForegroundColor Green
Write-Host "Durante a instalação:" -ForegroundColor Yellow
Write-Host "1. Defina a senha do usuário 'postgres' como: postgres" -ForegroundColor Yellow
Write-Host "2. Use a porta padrão: 5432" -ForegroundColor Yellow
Write-Host "3. Mantenha as configurações padrão" -ForegroundColor Yellow

# Executar o instalador
Start-Process -FilePath $output -Wait

Write-Host "Instalação concluída!" -ForegroundColor Green
Write-Host "Reinicie o terminal para usar os comandos do PostgreSQL" -ForegroundColor Yellow

# Limpar arquivo temporário
Remove-Item $output -Force