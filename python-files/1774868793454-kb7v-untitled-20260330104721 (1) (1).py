import os

APP_NAME = "MyApp"
APP_VERSION = "1.0"

iss_text = f"""
[Setup]
AppName={APP_NAME}
AppVersion={APP_VERSION}
DefaultDirName={{pf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir=output
OutputBaseFilename=Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Files]
Source: "dist\\{APP_NAME}.exe"; DestDir: "{{app}}"

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
"""

os.makedirs("output", exist_ok=True)

with open("installer.iss", "w", encoding="utf-8") as f:
    f.write(iss_text)

    print("Файл installer.iss создан!")