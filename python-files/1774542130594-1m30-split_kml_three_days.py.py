# split_kml_three_days.py
import xml.etree.ElementTree as ET
from tkinter import Tk
from tkinter.filedialog import askopenfilename
import os

# --- 1. ����� KML-����� ---
Tk().withdraw()
file_path = askopenfilename(title="�������� KML-���� ��� ���������� �� 3 ���",
                            filetypes=[("KML files", "*.kml")])
if not file_path:
    print("���� �� ������, �����.")
    exit()

# --- 2. ��������� KML ---
tree = ET.parse(file_path)
root = tree.getroot()
ns = {'kml': 'http://www.opengis.net/kml/2.2'}

# --- 3. �������� ��� Placemark �� ����� ---
dates_dict = {}
for placemark in root.findall('.//kml:Placemark', ns):
    timestamp_elem = placemark.find('.//kml:TimeStamp/kml:when', ns)
    if timestamp_elem is not None:
        date = timestamp_elem.text.split('T')[0]  # YYYY-MM-DD
        if date not in dates_dict:
            dates_dict[date] = []
        dates_dict[date].append(placemark)

# --- 4. ��������� ���� �� ������� � ����� �� 3 ��� ---
sorted_dates = sorted(dates_dict.keys())
if len(sorted_dates) < 3:
    print("� KML ������ 3 ���������� ���, �������� ������� ������, ������� ����.")
    num_days = len(sorted_dates)
else:
    num_days = 3

# --- 5. ������� ��� ���������� KML ---
def save_kml(placemarks, filename):
    kml_elem = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    doc_elem = ET.SubElement(kml_elem, 'Document')
    for pm in placemarks:
        doc_elem.append(pm)
    ET.ElementTree(kml_elem).write(filename, encoding="utf-8", xml_declaration=True)
    print(f"�������� ����: {filename}")

# --- 6. ������ 3 ����� ---
base_dir = os.path.dirname(file_path)
for i in range(num_days):
    date = sorted_dates[i]
    day_name = f"Day{i+1}_{date}"
    save_kml(dates_dict[date], os.path.join(base_dir, f"{day_name}.kml"))

print("���������� KML ���������.")