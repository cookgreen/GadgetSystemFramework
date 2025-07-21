cd gsf_framework

pyinstaller build.spec --noconfirm

$pwd = pwd

$sourceFile1 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon.ico"
$sourceFile2 = Join-Path -Path $pwd -ChildPath "gsf/assets/icon-install.ico"
$destinationFolder = Join-Path -Path $pwd -ChildPath "dist/GSF_Distribution/gsf/assets/"
$destinationServiceFolder = Join-Path -Path $pwd -ChildPath "dist/GSF_Distribution/"

if (-not (Test-Path -Path $destinationFolder)) {
    Write-Host "Creating $destinationFolder"
    New-Item -Path $destinationFolder -ItemType Directory | Out-Null
}

Copy-Item -Path $sourceFile1 -Destination $destinationFolder -Force -ErrorAction Stop
Copy-Item -Path $sourceFile2 -Destination $destinationFolder -Force -ErrorAction Stop

cd ..

$pwd = pwd

$serviceControlScript1 = Join-Path -Path $pwd -ChildPath "Scripts/service-install.bat"
$serviceControlScript2 = Join-Path -Path $pwd -ChildPath "Scripts/service-remove.bat"
$serviceControlScript3 = Join-Path -Path $pwd -ChildPath "Scripts/service-start.bat"
$serviceControlScript4 = Join-Path -Path $pwd -ChildPath "Scripts/service-debug.bat"

Copy-Item -Path $serviceControlScript1 -Destination $destinationServiceFolder -Force -ErrorAction Stop
Copy-Item -Path $serviceControlScript2 -Destination $destinationServiceFolder -Force -ErrorAction Stop
Copy-Item -Path $serviceControlScript3 -Destination $destinationServiceFolder -Force -ErrorAction Stop
Copy-Item -Path $serviceControlScript4 -Destination $destinationServiceFolder -Force -ErrorAction Stop


