import shutil
import os
import re
class Delete_:
    def __init__(self):
        self.cureent_folder = os.path.dirname(os.path.abspath(__file__))
        self.list_file = os.listdir(r'{}'.format(self.cureent_folder))
        self.pas_list = set()
        self._input_()
        if self.work == "remove":self.delete()
        else:self.move()
        print("End")
    def _input_(self):
        works = {"1":"remove",'2':"move"}
        work = input("Enter the number of files to be deleted: \nRemove: 1\nMove: 2\nEnter : ")
        self.work = works.get(work)
        if work == "2":
            self.addres = input("Enter the address of files to be move: \nAddress: ")
        else:self.addres = None
        self.link = input("Enter the link of file:(,) : ").split(",")

    def delete(self):
        for file in self.list_file:
            ext = re.search(r'\.([^.]+)$', file)
            if ext:
                extension = ext.group(1)
                if extension in self.link:
                    os.remove(os.path.join(self.cureent_folder, file))
    def move(self):
        for file in self.list_file:
            ext = re.search(r'\.([^.]+)$', file)
            if ext:
                extension = ext.group(1)
                if extension in self.link:
                    shutil.move(file, (self.addres+"/" + file))

sajad = Delete_()
