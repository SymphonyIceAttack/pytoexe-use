import os

def rename_files_with_prefix(folder_path):
    """
    ��������������� ��� ����� � �����, �������� ������� � ������� (1_, 2_, ...).
    """
    # ���������, ���������� �� ��������� �����
    if not os.path.isdir(folder_path):
        print("������: ��������� ����� �� ����������.")
        return

    # �������� ������ ���� ��������� � �����
    items = os.listdir(folder_path)
    # ��������� ������ ����� (��������� �����)
    files = [f for f in items if os.path.isfile(os.path.join(folder_path, f))]
    
    # ��������� ����� ��� �������������� ������� (�� ��������)
    files.sort()

    # ��������������� ������ ����
    for idx, filename in enumerate(files, start=1):
        # ��������� ����� �������
        prefix = f"{idx}_"
        new_name = prefix + filename
        old_path = os.path.join(folder_path, filename)
        new_path = os.path.join(folder_path, new_name)

        # ���������, �� ���������� �� ��� ���� � ����� ������
        if os.path.exists(new_path):
            print(f"��������������: ���� {new_name} ��� ����������. ���������� {filename}.")
            continue

        # ���������������
        os.rename(old_path, new_path)
        print(f"������������: {filename} -> {new_name}")

    print("������!")

if __name__ == "__main__":
    # ����������� ���� � ����� � ������������
    folder = input("������� ���� � �����: ").strip()
    rename_files_with_prefix(folder)