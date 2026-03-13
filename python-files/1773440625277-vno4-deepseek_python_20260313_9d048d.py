import os
import sys
import site
import shutil
from pathlib import Path

# Путь к установленному setuptools
site_packages = site.getsitepackages()[0]
setuptools_path = Path(site_packages) / "pkg_resources"

if setuptools_path.exists():
    # Создаем резервную копию
    backup_path = Path(site_packages) / "pkg_resources_backup"
    if not backup_path.exists():
        shutil.copytree(setuptools_path, backup_path)
    
    # Патчим файл
    init_file = setuptools_path / "__init__.py"
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Заменяем ImpImporter на zipimporter
    content = content.replace('pkgutil.ImpImporter', 'pkgutil.zipimporter')
    
    with open(init_file, 'w') as f:
        f.write(content)
    
    print("Патч применен!")
else:
    print("pkg_resources не найден")

print("Теперь попробуйте собрать приложение")