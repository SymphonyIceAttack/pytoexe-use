import os
import sys
import threading
from collections import defaultdict
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import numpy as np
import trimesh
from PIL import Image

class VoxelizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Roblox Voxelizer — Max Optimization")
        self.geometry("660x650")
        self.resizable(False, False)

        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.create_widgets()

    def create_widgets(self):
        padding_frame = ttk.Frame(self, padding="15")
        padding_frame.pack(fill=tk.BOTH, expand=True)

        # --- 1. ВЫБОР МОДЕЛИ ---
        lbl_model = ttk.Label(padding_frame, text="1. Выберите 3D-модель (.obj, .fbx):", font=('Segoe UI', 9, 'bold'))
        lbl_model.grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 2))

        self.model_path_var = tk.StringVar()
        entry_model = ttk.Entry(padding_frame, textvariable=self.model_path_var, width=60)
        entry_model.grid(row=1, column=0, sticky='we', padx=(0, 5))

        btn_model = ttk.Button(padding_frame, text="Обзор...", command=self.browse_model)
        btn_model.grid(row=1, column=1, sticky='e')

        # --- 2. ВЫБОР ТЕКСТУР ---
        lbl_tex = ttk.Label(padding_frame, text="2. Папка с текстурами (или авто из .mtl/.fbx):", font=('Segoe UI', 9, 'bold'))
        lbl_tex.grid(row=2, column=0, columnspan=2, sticky='w', pady=(10, 2))

        self.texture_dir_var = tk.StringVar()
        entry_tex = ttk.Entry(padding_frame, textvariable=self.texture_dir_var, width=60)
        entry_tex.grid(row=3, column=0, sticky='we', padx=(0, 5))

        tex_buttons_frame = ttk.Frame(padding_frame)
        tex_buttons_frame.grid(row=3, column=1, sticky='e')

        btn_tex = ttk.Button(tex_buttons_frame, text="Папка...", command=self.browse_texture_dir)
        btn_tex.pack(side=tk.LEFT, padx=(0, 2))

        btn_clear_tex = ttk.Button(tex_buttons_frame, text="✕", width=3, command=lambda: self.texture_dir_var.set(""))
        btn_clear_tex.pack(side=tk.LEFT)

        # --- 3. НАСТРОЙКИ ВОКСЕЛИЗАЦИИ И ОПТИМИЗАЦИИ ---
        lbl_settings = ttk.Label(padding_frame, text="3. Параметры сетки и слияния:", font=('Segoe UI', 9, 'bold'))
        lbl_settings.grid(row=4, column=0, columnspan=2, sticky='w', pady=(12, 2))

        settings_frame = ttk.Frame(padding_frame)
        settings_frame.grid(row=5, column=0, columnspan=2, sticky='w')

        ttk.Label(settings_frame, text="Размер вокселя:").grid(row=0, column=0, sticky='w', padx=(0, 5))
        self.voxel_size_var = tk.StringVar(value="1.0")
        entry_size = ttk.Entry(settings_frame, textvariable=self.voxel_size_var, width=8)
        entry_size.grid(row=0, column=1, sticky='w', padx=(0, 15))

        ttk.Label(settings_frame, text="Слияние деталей (Оптимизация):").grid(row=0, column=2, sticky='w', padx=(0, 5))
        self.opt_mode_var = tk.StringVar(value="Max")
        opt_combo = ttk.Combobox(
            settings_frame, 
            textvariable=self.opt_mode_var, 
            values=["Max (Стены в 1 деталь)", "Medium (Баланс)", "Exact (Точные цвета)"],
            state="readonly",
            width=24
        )
        opt_combo.grid(row=0, column=3, sticky='w')

        # --- 4. КНОПКА ЗАПУСКА И ПРОГРЕСС ---
        self.btn_start = ttk.Button(padding_frame, text="🚀 Начать максимальную вокселизацию", command=self.start_processing_thread)
        self.btn_start.grid(row=6, column=0, columnspan=2, pady=(15, 8), sticky='we')

        self.progress = ttk.Progressbar(padding_frame, mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, sticky='we', pady=(0, 10))

        # --- 5. КОНСОЛЬ ЛОГОВ ---
        lbl_log = ttk.Label(padding_frame, text="Статус и лог выполнения:", font=('Segoe UI', 9, 'bold'))
        lbl_log.grid(row=8, column=0, columnspan=2, sticky='w', pady=(5, 2))

        self.log_area = scrolledtext.ScrolledText(padding_frame, height=12, state='disabled', font=('Consolas', 9))
        self.log_area.grid(row=9, column=0, columnspan=2, sticky='we')

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def browse_model(self):
        path = filedialog.askopenfilename(
            title="Выберите 3D-модель",
            filetypes=[("3D Models", "*.obj *.fbx"), ("OBJ files", "*.obj"), ("FBX files", "*.fbx")]
        )
        if path:
            self.model_path_var.set(path)

    def browse_texture_dir(self):
        path = filedialog.askdirectory(title="Выберите папку с текстурами")
        if path:
            self.texture_dir_var.set(path)

    def start_processing_thread(self):
        model_path = self.model_path_var.get().strip()
        if not model_path or not os.path.exists(model_path):
            messagebox.showerror("Ошибка", "Выберите существующий файл 3D-модели!")
            return

        try:
            voxel_size = float(self.voxel_size_var.get().replace(',', '.'))
            if voxel_size < 0.01:
                messagebox.showerror("Ошибка", "Минимальный размер вокселя — 0.01!")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Размер вокселя должен быть числом!")
            return

        self.btn_start.config(state='disabled')
        self.progress.start(10)
        
        self.log_area.config(state='normal')
        self.log_area.delete('1.0', tk.END)
        self.log_area.config(state='disabled')

        thread = threading.Thread(
            target=self.run_voxelization, 
            args=(model_path, self.texture_dir_var.get().strip(), voxel_size, self.opt_mode_var.get()), 
            daemon=True
        )
        thread.start()

    def matrix_greedy_mesh_3d(self, grid_indices, raw_colors, opt_mode):
        """
        Агрессивный 3D Greedy Meshing на базе трехосных матриц.
        Объединяет воксели в сплошные 3D-блоки и усредняет их итоговый цвет.
        """
        min_idx = grid_indices.min(axis=0)
        max_idx = grid_indices.max(axis=0)
        dims = max_idx - min_idx + 1

        dim_x, dim_y, dim_z = dims
        
        # Определение уровня квантования цвета для объединения
        if "Max" in opt_mode:
            quant_factor = 8.0   # Очень агрессивное объединение (все стены станут едиными партами)
        elif "Medium" in opt_mode:
            quant_factor = 20.0  # Средний баланс
        else:
            quant_factor = 100.0 # Точное сохранение цветов

        # Создаем сетку идентификаторов
        color_map = {}
        color_to_id = {}
        grid = np.zeros((dim_x, dim_y, dim_z), dtype=np.int32)
        raw_colors_grid = np.zeros((dim_x, dim_y, dim_z, 3), dtype=np.float32)

        next_id = 1
        for idx, (ix, iy, iz) in enumerate(grid_indices - min_idx):
            r, g, b = raw_colors[idx]
            
            # Квантуем цвет для группы
            qr, qg, qb = round(r * quant_factor), round(g * quant_factor), round(b * quant_factor)
            key = (qr, qg, qb)

            if key not in color_to_id:
                color_to_id[key] = next_id
                next_id += 1
            
            c_id = color_to_id[key]
            grid[ix, iy, iz] = c_id
            raw_colors_grid[ix, iy, iz] = [r, g, b]

        visited = np.zeros((dim_x, dim_y, dim_z), dtype=bool)
        boxes = []

        # Трехмерное жадное объединение (3D Sweep)
        for z in range(dim_z):
            for y in range(dim_y):
                for x in range(dim_x):
                    if visited[x, y, z] or grid[x, y, z] == 0:
                        continue
                    
                    c_id = grid[x, y, z]

                    # 1. Расширение по X
                    dx = 1
                    while x + dx < dim_x and not visited[x + dx, y, z] and grid[x + dx, y, z] == c_id:
                        dx += 1

                    # 2. Расширение по Y
                    dy = 1
                    can_expand_y = True
                    while y + dy < dim_y and can_expand_y:
                        for kx in range(dx):
                            if visited[x + kx, y + dy, z] or grid[x + kx, y + dy, z] != c_id:
                                can_expand_y = False
                                break
                        if can_expand_y:
                            dy += 1

                    # 3. Расширение по Z
                    dz = 1
                    can_expand_z = True
                    while z + dz < dim_z and can_expand_z:
                        for ky in range(dy):
                            for kx in range(dx):
                                if visited[x + kx, y + ky, z + dz] or grid[x + kx, y + ky, z + dz] != c_id:
                                    can_expand_z = False
                                    break
                            if not can_expand_z:
                                break
                        if can_expand_z:
                            dz += 1

                    # Помечаем область как обработанную
                    visited[x:x+dx, y:y+dy, z:z+dz] = True

                    # Высчитываем усредненный оригинальный цвет для объединенной детали
                    sub_colors = raw_colors_grid[x:x+dx, y:y+dy, z:z+dz]
                    mask = grid[x:x+dx, y:y+dy, z:z+dz] == c_id
                    avg_color = sub_colors[mask].mean(axis=0)

                    boxes.append((
                        x + min_idx[0], x + dx - 1 + min_idx[0],
                        y + min_idx[1], y + dy - 1 + min_idx[1],
                        z + min_idx[2], z + dz - 1 + min_idx[2],
                        (avg_color[0], avg_color[1], avg_color[2])
                    ))

        return boxes

    def run_voxelization(self, model_path, texture_dir, voxel_size, opt_mode):
        try:
            model_dir = os.path.dirname(model_path)
            base_name = os.path.splitext(os.path.basename(model_path))[0]

            self.log(f"Загрузка модели: {os.path.basename(model_path)}...")
            scene_or_mesh = trimesh.load(model_path, process=False)

            if isinstance(scene_or_mesh, trimesh.Scene):
                self.log("Обнаружена комплексная сцена, объединение геометрии...")
                meshes = [geom for geom in scene_or_mesh.geometry.values() if isinstance(geom, trimesh.Trimesh)]
                mesh = trimesh.util.concatenate(meshes) if meshes else scene_or_mesh.dump(concatenate=True)
            else:
                mesh = scene_or_mesh

            # --- ЗАГРУЗКА МУЛЬТИ-ТЕКСТУР ---
            loaded_textures = {}
            if hasattr(mesh.visual, 'material') and hasattr(mesh.visual.material, 'image') and mesh.visual.material.image:
                loaded_textures['default'] = mesh.visual.material.image.convert('RGB')

            if hasattr(mesh.visual, 'materials'):
                for idx, mat in enumerate(mesh.visual.materials):
                    if hasattr(mat, 'image') and mat.image:
                        mat_name = getattr(mat, 'name', f"mat_{idx}")
                        loaded_textures[mat_name] = mat.image.convert('RGB')

            if texture_dir and os.path.exists(texture_dir):
                for filename in os.listdir(texture_dir):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        tex_path = os.path.join(texture_dir, filename)
                        tex_name = os.path.splitext(filename)[0]
                        try:
                            loaded_textures[tex_name] = Image.open(tex_path).convert('RGB')
                        except Exception:
                            pass

            self.log(f"Вокселизация сетки (размер вокселя: {voxel_size})...")
            voxel_grid = mesh.voxelized(pitch=voxel_size)
            centers = voxel_grid.points

            total_voxels = len(centers)
            if total_voxels == 0:
                self.log("Ошибка: Модель пустая или размер вокселя слишком большой!")
                return

            self.log(f"Создано исходных вокселей: {total_voxels}. Сопоставление цветов...")

            try:
                _, _, face_indices = mesh.nearest.on_surface(centers)
            except Exception:
                from scipy.spatial import KDTree
                tree = KDTree(mesh.triangles.mean(axis=1))
                _, face_indices = tree.query(centers)

            has_uvs = hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None
            face_materials = getattr(mesh.visual, 'face_materials', None)
            
            face_colors = None
            try:
                face_colors = mesh.visual.to_color().face_colors
            except Exception:
                pass

            min_pos = centers.min(axis=0)
            grid_indices = np.round((centers - min_pos) / voxel_size).astype(int)

            raw_colors = []
            for i in range(total_voxels):
                face_idx = face_indices[i]
                cr, cg, cb = 0.7, 0.7, 0.7

                active_texture = None
                if face_materials is not None and len(face_materials) > face_idx:
                    mat_idx = face_materials[face_idx]
                    if hasattr(mesh.visual, 'materials') and len(mesh.visual.materials) > mat_idx:
                        mat = mesh.visual.materials[mat_idx]
                        mat_name = getattr(mat, 'name', f"mat_{mat_idx}")
                        active_texture = loaded_textures.get(mat_name, getattr(mat, 'image', None))

                if not active_texture and len(loaded_textures) > 0:
                    active_texture = list(loaded_textures.values())[0]

                if active_texture and has_uvs:
                    try:
                        uvs = mesh.visual.uv[mesh.faces[face_idx]]
                        avg_uv = uvs.mean(axis=0)
                        img_w, img_h = active_texture.size
                        u = int(avg_uv[0] * (img_w - 1)) % img_w
                        v = int((1 - avg_uv[1]) * (img_h - 1)) % img_h
                        r, g, b = active_texture.getpixel((u, v))
                        cr, cg, cb = r / 255.0, g / 255.0, b / 255.0
                    except Exception:
                        pass
                elif face_colors is not None and len(face_colors) > face_idx:
                    r, g, b = face_colors[face_idx][:3]
                    cr, cg, cb = r / 255.0, g / 255.0, b / 255.0

                raw_colors.append((cr, cg, cb))

            # --- МАКСИМАЛЬНАЯ ОПТИМИЗАЦИЯ СЛИЯНИЯ ---
            self.log(f"Запуск 3D-оптимизации в режиме: {opt_mode}...")
            boxes = self.matrix_greedy_mesh_3d(grid_indices, raw_colors, opt_mode)
            
            reduced_count = len(boxes)
            saved_pct = round((1.0 - reduced_count / total_voxels) * 100.0, 1)
            self.log(f" Оптимизация завершена!\n Исходно вокселей: {total_voxels}\n Итого деталей в Roblox: {reduced_count}\n Сокращение: -{saved_pct}% деталей!")

            # --- ЭКСПОРТ В ROBLOX RBXMX ---
            self.log("Экспорт файла .rbxmx...")
            roblox = ET.Element("roblox", {
                "xmlns:xmime": "http://www.w3.org/2005/05/xmlmime",
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "version": "4"
            })
            
            model_item = ET.SubElement(roblox, "Item", {"class": "Model", "referent": "RBX0"})
            props = ET.SubElement(model_item, "Properties")
            ET.SubElement(props, "string", {"name": "Name"}).text = base_name + "_Optimized"

            for i, (sx, ex, sy, ey, sz, ez, color) in enumerate(boxes):
                size_x = (ex - sx + 1) * voxel_size
                size_y = (ey - sy + 1) * voxel_size
                size_z = (ez - sz + 1) * voxel_size

                cx = min_pos[0] + (sx + ex + 1) / 2.0 * voxel_size
                cy = min_pos[1] + (sy + ey + 1) / 2.0 * voxel_size
                cz = min_pos[2] + (sz + ez + 1) / 2.0 * voxel_size

                part_item = ET.SubElement(model_item, "Item", {"class": "Part", "referent": f"RBX_P_{i}"})
                p_props = ET.SubElement(part_item, "Properties")
                
                ET.SubElement(p_props, "string", {"name": "Name"}).text = "VoxelWall"
                ET.SubElement(p_props, "bool", {"name": "Anchored"}).text = "true"
                
                color_elem = ET.SubElement(p_props, "Color3", {"name": "Color"})
                ET.SubElement(color_elem, "R").text = str(round(color[0], 4))
                ET.SubElement(color_elem, "G").text = str(round(color[1], 4))
                ET.SubElement(color_elem, "B").text = str(round(color[2], 4))

                size_elem = ET.SubElement(p_props, "Vector3", {"name": "Size"})
                ET.SubElement(size_elem, "X").text = str(round(size_x, 3))
                ET.SubElement(size_elem, "Y").text = str(round(size_y, 3))
                ET.SubElement(size_elem, "Z").text = str(round(size_z, 3))

                cf_elem = ET.SubElement(p_props, "CoordinateFrame", {"name": "CFrame"})
                ET.SubElement(cf_elem, "X").text = str(round(cx, 3))
                ET.SubElement(cf_elem, "Y").text = str(round(cy, 3))
                ET.SubElement(cf_elem, "Z").text = str(round(cz, 3))
                ET.SubElement(cf_elem, "R00").text = "1"
                ET.SubElement(cf_elem, "R01").text = "0"
                ET.SubElement(cf_elem, "R02").text = "0"
                ET.SubElement(cf_elem, "R10").text = "0"
                ET.SubElement(cf_elem, "R11").text = "1"
                ET.SubElement(cf_elem, "R12").text = "0"
                ET.SubElement(cf_elem, "R20").text = "0"
                ET.SubElement(cf_elem, "R21").text = "0"
                ET.SubElement(cf_elem, "R22").text = "1"

            output_file = os.path.join(model_dir, f"{base_name}_voxels.rbxmx")
            tree = ET.ElementTree(roblox)
            tree.write(output_file, encoding="utf-8", xml_declaration=True)
            
            self.log(f"\n УСПЕШНО! Сохранено в:\n{output_file}")
            messagebox.showinfo("Готово", f"Обработка завершена!\nБыло вокселей: {total_voxels}\nИтоговых деталей: {reduced_count}\n\nФайл сохранён:\n{output_file}")

        except Exception as e:
            self.log(f"\n Ошибка: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка при обработке:\n{e}")

        finally:
            self.progress.stop()
            self.btn_start.config(state='normal')

if __name__ == "__main__":
    app = VoxelizerApp()
    app.mainloop()