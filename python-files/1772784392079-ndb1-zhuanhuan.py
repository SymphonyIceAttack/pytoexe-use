import os
import sys
import tarfile
import zipfile
import shutil

def find_base_apk(path):
    for root, dirs, files in os.walk(path):
        if "base.apk" in files:
            return os.path.join(root, "base.apk")
    return None

def find_data_dir(path):
    for root, dirs, files in os.walk(path):
        if root.endswith("data/data"):
            return root
    return None

def convert(tar_path):

    base_dir = os.path.dirname(tar_path)
    name = os.path.splitext(os.path.basename(tar_path))[0]

    work = os.path.join(base_dir, name+"_tmp")
    wb = os.path.join(work,"wb")

    if os.path.exists(work):
        shutil.rmtree(work)

    os.makedirs(wb)

    print("��ѹ TAR...")
    with tarfile.open(tar_path) as tar:
        tar.extractall(work)

    apk = find_base_apk(work)
    data = find_data_dir(work)

    if apk:
        shutil.copy(apk, os.path.join(wb,"app.apk"))
        print("�ҵ� APK")

    if data:
        shutil.copytree(data, os.path.join(wb,"data"))
        print("���� DATA")

    device = os.path.join(wb,"device.prop")

    with open(device,"w") as f:
        f.write("ro.product.brand=Xiaomi\n")
        f.write("ro.product.model=MI8\n")
        f.write("ro.build.version.release=10\n")

    wb_file = os.path.join(base_dir,name+".wb")

    print("���� WB...")

    with zipfile.ZipFile(wb_file,"w",zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(wb):
            for file in files:
                full = os.path.join(root,file)
                arc = os.path.relpath(full,wb)
                z.write(full,arc)

    shutil.rmtree(work)

    print("ת�����:",wb_file)


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("��� .tar �ļ��ϵ�����������")
        input()
    else:
        convert(sys.argv[1])