cd gsf_framework

pyinstaller build.spec --noconfirm

$pwd = pwd

$sourceFile1 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon.ico"
$sourceFile2 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon-install.ico"
$destinationFolder = Join-Path -Path $pwd -ChildPath "dist/GSF_Distribution/gsf/assets/"

if (-not (Test-Path -Path $destinationFolder)) {
    Write-Host "Creating $destinationFolder"
    New-Item -Path $destinationFolder -ItemType Directory | Out-Null
}

Copy-Item -Path $sourceFile1 -Destination $destinationFolder -Force -ErrorAction Stop
Copy-Item -Path $sourceFile2 -Destination $destinationFolder -Force -ErrorAction Stop

$serviceControlScript1 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon.ico"
$serviceControlScript2 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon-install.ico"
$serviceControlScript3 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon-install.ico"
$destinationServiceFolder = Join-Path -Path $pwd -ChildPath "dist/GSF_Distribution/"

Copy-Item -Path $serviceControlScript1 -Destination $destinationServiceFolder -Force -ErrorAction Stop
Copy-Item -Path $serviceControlScript2 -Destination $destinationServiceFolder -Force -ErrorAction Stop
Copy-Item -Path $serviceControlScript3 -Destination $destinationServiceFolder -Force -ErrorAction Stop


