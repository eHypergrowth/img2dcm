@echo off
:: Activar el entorno virtual
call venv\Scripts\activate

:: Instalar PyInstaller si no está instalado
pip install pyinstaller

:: Crear el ejecutable
pyinstaller --onefile ^
            --add-data "dcm4che-5.33.1;dcm4che-5.33.1" ^
            --exclude-module "*.zip" ^
            --icon "diagnocons.ico" ^
            --name "Convertidor_jpg_a_dicom" ^
            main.py

:: Confirmar que el ejecutable se creó
if exist dist\Convertidor_jpg_a_dicom.exe (
    echo El ejecutable se creó correctamente: dist\Convertidor_jpg_a_dicom.exe
) else (
    echo Error: El ejecutable no se pudo crear.
)

:: Desactivar el entorno virtual
deactivate
pause
