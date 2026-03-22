import customtkinter as ctk
from tkinter import messagebox, filedialog
import pandas as pd
import os
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime, time

CONFIG_FILE = "pmc_hub_config.json"

class ProductionDataHubUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("System")  
        ctk.set_default_color_theme("blue") 
        self.title("车间排产记录汇集 (PMC Data Hub)")
        self.geometry("520x240")
        self.resizable(False, False)

        self.selected_files = []
        self.display_text = ctk.StringVar(value="请选择服务器上的排产文件...")

        self._load_memory() 
        self._build_ui()

    def _load_memory(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    saved_files = data.get("last_files", [])
                    self.selected_files = [f for f in saved_files if os.path.exists(f)]
                    if self.selected_files:
                        self.display_text.set(f"已恢复记忆：选中 {len(self.selected_files)} 个文件")
            except Exception:
                pass 

    def _save_memory(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"last_files": self.selected_files}, f, ensure_ascii=False)
        except Exception:
            pass

    def _build_ui(self):
        frame_source = ctk.CTkFrame(self, corner_radius=10)
        frame_source.pack(pady=(25, 15), padx=20, fill="x")
        
        ctk.CTkLabel(frame_source, text="1. 源文件定位 (具备记忆功能)", font=("Arial", 14, "bold")).pack(anchor="w", pady=(10, 0), padx=15)
        
        path_frame = ctk.CTkFrame(frame_source, fg_color="transparent")
        path_frame.pack(fill="x", pady=10, padx=15)
        ctk.CTkEntry(path_frame, textvariable=self.display_text, state="disabled", width=340).pack(side="left", padx=(0, 10))
        ctk.CTkButton(path_frame, text="选择文件...", width=70, command=self.select_files).pack(side="right")

        self.btn_run = ctk.CTkButton(self, text="⚡ 提取并生成智能大盘视图", 
                                     height=45, font=("Arial", 15, "bold"), 
                                     command=self.run_pipeline)
        self.btn_run.pack(pady=(10, 20), padx=20, fill="x")

    def select_files(self):
        files_selected = filedialog.askopenfilenames(
            title="请选择车间排产 Excel 文件",
            filetypes=[("Excel 文件", "*.xlsx;*.xls")]
        )
        if files_selected:
            self.selected_files = list(files_selected)
            self.display_text.set(f"当前已选中 {len(self.selected_files)} 个源文件")
            self._save_memory() 

    def extract_and_purify_data(self, file_path):
        try:
            sheet_dict = pd.read_excel(file_path, usecols="A:F, P", header=None, sheet_name=None)
            all_sheets_data = []
            
            def parse_date_smartly(val):
                if pd.isna(val): return ""
                val_str = str(val).strip()
                try:
                    if val_str.isdigit() or (isinstance(val, float) and val.is_integer()):
                        dt = pd.to_datetime(int(float(val)), origin='1899-12-30', unit='D')
                        return f"{dt.month}月{dt.day}日"
                    if hasattr(val, 'month') and hasattr(val, 'day'):
                        return f"{val.month}月{val.day}日"
                    dt = pd.to_datetime(val_str, errors='coerce')
                    if pd.notna(dt):
                        return f"{dt.month}月{dt.day}日"
                    return val_str.replace(' 00:00:00', '')
                except:
                    return val_str

            def parse_time_smartly(val):
                if pd.isna(val): return ""
                if isinstance(val, time):
                    return val.strftime("%H:%M")
                if isinstance(val, (datetime, pd.Timestamp)):
                    return val.strftime("%H:%M")
                
                val_str = str(val).strip()
                if " " in val_str and ":" in val_str:
                    time_part = val_str.split(" ")[-1] 
                    if len(time_part) >= 5: return time_part[:5]
                
                if ":" in val_str:
                    parts = val_str.split(":")
                    if len(parts) >= 2: return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
                
                try:
                    if val_str.replace('.', '', 1).isdigit():
                        fraction = float(val)
                        if 0 <= fraction < 1:
                            total_minutes = int(round(fraction * 24 * 60))
                            hours, minutes = divmod(total_minutes, 60)
                            return f"{hours:02d}:{minutes:02d}"
                except: pass
                
                return val_str

            for sheet_name, df in sheet_dict.items():
                if df.empty or len(df.columns) < 7: continue
                    
                df.columns = ['日期', '组别', '订单号', '产品型号', '皮质颜色', '数量', '排产时间']
                df = df[['日期', '排产时间', '组别', '订单号', '产品型号', '皮质颜色', '数量']]

                df_clean = df.dropna(how='all').copy()
                df_clean = df_clean[df_clean['日期'] != '日期']
                df_clean = df_clean.dropna(subset=['日期']) 

                df_clean['日期'] = df_clean['日期'].apply(parse_date_smartly)
                df_clean['排产时间'] = df_clean['排产时间'].apply(parse_time_smartly)
                df_clean['数量'] = pd.to_numeric(df_clean['数量'], errors='coerce').fillna(0)
                
                all_sheets_data.append(df_clean)

            if all_sheets_data:
                return pd.concat(all_sheets_data, ignore_index=True)
            return None
                
        except Exception:
            return None

    def format_and_export(self, df, export_path):
        writer = pd.ExcelWriter(export_path, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='排产智控总览')

        workbook  = writer.book
        worksheet = writer.sheets['排产智控总览']

        # ==========================================
        # 视觉设计生态体系 (极简网格线与精准切割边界)
        # ==========================================
        FONT_FAMILY = 'Arial'
        GRID_COLOR = '#E8EAED'           # 全局极浅灰网格线
        HEADER_BG = '#F8F9FA'            
        HEADER_FONT = '#202124'          
        HIGHLIGHT_BLUE = '#1A73E8'       # Google 决策蓝
        DIVIDER_COLOR = '#9AA0A6'        # G列与N列右侧专属切割深灰
        
        WHITE_BG = '#FFFFFF'             
        ALT_BLUE_BG = '#E8F0FE'          

        # ------------------------------------------
        # 1. 基础结构列格式 (控制空白区域的无限向下延伸网络)
        # ------------------------------------------
        base_center = workbook.add_format({'font_name': FONT_FAMILY, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'border_color': GRID_COLOR})
        base_left = workbook.add_format({'font_name': FONT_FAMILY, 'valign': 'vcenter', 'align': 'left', 'border': 1, 'border_color': GRID_COLOR})
        
        # 【核心修复点】: 基底格式直接注入 HIGHLIGHT_BLUE 与 bold=True，确保 N 列溢出的查询结果完美继承 Google 蓝！
        base_divider_qty = workbook.add_format({
            'font_name': FONT_FAMILY, 'valign': 'vcenter', 'align': 'right', 
            'border': 1, 'border_color': GRID_COLOR, 
            'right': 2, 'right_color': DIVIDER_COLOR,
            'font_color': HIGHLIGHT_BLUE, 'bold': True 
        })

        # 为全列注入基础极浅灰网络 (确保没有数据的行也具备整齐美感与蓝色基底)
        worksheet.set_column('A:A', 12, base_center) 
        worksheet.set_column('B:C', 10, base_center) 
        worksheet.set_column('D:E', 22, base_left) 
        worksheet.set_column('F:F', 15, base_left) 
        worksheet.set_column('G:G', 12, base_divider_qty) # G列右边界墙 (含Google蓝)

        worksheet.set_column('H:H', 12, base_center) 
        worksheet.set_column('I:J', 10, base_center) 
        worksheet.set_column('K:L', 22, base_left)
        worksheet.set_column('M:M', 15, base_left)
        worksheet.set_column('N:N', 12, base_divider_qty) # N列右边界墙 (含Google蓝)

        # ------------------------------------------
        # 2. 数据层画笔引擎 (斑马纹与高亮映射)
        # ------------------------------------------
        def create_fmt(align, is_qty=False, is_time=False, bg_color=WHITE_BG):
            fmt_props = {
                'font_name': FONT_FAMILY, 'valign': 'vcenter', 'align': align, 
                'border': 1, 'border_color': GRID_COLOR, 'bg_color': bg_color
            }
            if is_qty:
                fmt_props.update({'bold': True, 'font_color': HIGHLIGHT_BLUE, 'right': 2, 'right_color': DIVIDER_COLOR})
            return workbook.add_format(fmt_props)

        fmts = {
            False: { 
                'center': create_fmt('center', bg_color=WHITE_BG),
                'left': create_fmt('left', bg_color=WHITE_BG),
                'time': create_fmt('center', is_time=True, bg_color=WHITE_BG),
                'qty': create_fmt('right', is_qty=True, bg_color=WHITE_BG)
            },
            True: {  
                'center': create_fmt('center', bg_color=ALT_BLUE_BG),
                'left': create_fmt('left', bg_color=ALT_BLUE_BG),
                'time': create_fmt('center', is_time=True, bg_color=ALT_BLUE_BG),
                'qty': create_fmt('right', is_qty=True, bg_color=ALT_BLUE_BG)
            }
        }

        # ------------------------------------------
        # 3. 表头专属格式处理
        # ------------------------------------------
        header_fmt = workbook.add_format({'font_name': FONT_FAMILY, 'bold': True, 'bg_color': HEADER_BG, 'font_color': HEADER_FONT, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'border_color': GRID_COLOR})
        header_divider_fmt = workbook.add_format({'font_name': FONT_FAMILY, 'bold': True, 'bg_color': HEADER_BG, 'font_color': HEADER_FONT, 'valign': 'vcenter', 'align': 'center', 'border': 1, 'border_color': GRID_COLOR, 'right': 2, 'right_color': DIVIDER_COLOR})

        for col_num, value in enumerate(df.columns.values):
            if col_num == 6: # G列
                worksheet.write(0, col_num, value, header_divider_fmt)
            else:
                worksheet.write(0, col_num, value, header_fmt)

        current_date = None
        use_alt_color = False

        for row_idx, row_data in enumerate(df.values):
            date_val = row_data[0]
            if date_val != current_date:
                use_alt_color = not use_alt_color
                current_date = date_val
            
            current_fmts = fmts[use_alt_color]
            
            worksheet.write(row_idx + 1, 0, row_data[0], current_fmts['center'])
            worksheet.write(row_idx + 1, 1, row_data[1], current_fmts['time'])   
            worksheet.write(row_idx + 1, 2, row_data[2], current_fmts['center']) 
            worksheet.write(row_idx + 1, 3, row_data[3], current_fmts['left'])
            worksheet.write(row_idx + 1, 4, row_data[4], current_fmts['left'])
            worksheet.write(row_idx + 1, 5, row_data[5], current_fmts['left'])
            worksheet.write(row_idx + 1, 6, row_data[6], current_fmts['qty'])

        # ------------------------------------------
        # 4. 右侧大屏渲染与交互注入
        # ------------------------------------------
        search_label_fmt = workbook.add_format({'font_name': FONT_FAMILY, 'bold': True, 'align': 'right', 'valign': 'vcenter', 'font_color': '#5F6368', 'border': 1, 'border_color': GRID_COLOR})
        search_box_fmt = workbook.add_format({'font_name': FONT_FAMILY, 'bg_color': '#E8F0FE', 'border': 1, 'border_color': HIGHLIGHT_BLUE, 'bold': True, 'valign': 'vcenter'})

        worksheet.merge_range('H1:I1', '🔍 模糊搜索(订单号) ➔', search_label_fmt)
        worksheet.write('J1', '', search_box_fmt) 
        
        for col_num, value in enumerate(df.columns.values):
            if col_num == 6: # N列
                worksheet.write(2, col_num + 7, value, header_divider_fmt)
            else:
                worksheet.write(2, col_num + 7, value, header_fmt) 

        data_end_row = len(df) + 1
        formula = f'=IF(ISBLANK(J1), "👆 等待输入...", FILTER(A2:G{data_end_row}, ISNUMBER(SEARCH(J1, D2:D{data_end_row})), "∅ 未匹配到记录"))'
        worksheet.write_formula('H4', formula)

        worksheet.freeze_panes(1, 0)
        worksheet.autofilter(0, 0, data_end_row - 1, 6) 
        
        worksheet.hide_gridlines(2) 

        writer.close()

    def run_pipeline(self):
        if not self.selected_files:
            messagebox.showwarning("指引", "请先点击右侧按钮选择源文件！")
            return

        try:
            self.btn_run.configure(state="disabled", text="生态全域提纯中...")
            self.update()

            all_data = []
            for file_path in self.selected_files:
                df_clean = self.extract_and_purify_data(file_path)
                if df_clean is not None and not df_clean.empty:
                    all_data.append(df_clean)

            if not all_data:
                messagebox.showinfo("提示", "未能从选中的文件中提取到有效排产数据。")
                return

            final_df = pd.concat(all_data, ignore_index=True)

            desktop_path = Path(os.path.expanduser("~/Desktop"))
            export_folder = desktop_path / "车间排产记录"
            export_folder.mkdir(parents=True, exist_ok=True) 
            
            export_file = export_folder / f"排产智控总览_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
            
            self.format_and_export(final_df, export_file)
            
            try:
                if platform.system() == 'Windows':
                    os.startfile(export_file)
                elif platform.system() == 'Darwin': 
                    subprocess.call(['open', str(export_file)])
                else:
                    subprocess.call(['xdg-open', str(export_file)])
            except Exception as e:
                print(f"唤醒底层调用受限: {e}")

            messagebox.showinfo("流转完成", f"N列溢出已同步决策蓝！视觉生态完全闭环。\n路径：桌面/车间排产记录/{export_file.name}")

        except Exception as e:
            messagebox.showerror("系统异常", f"引擎发生意外：\n{str(e)}")
        finally:
            self.btn_run.configure(state="normal", text="⚡ 提取并生成智能大盘视图")

if __name__ == "__main__":
    app = ProductionDataHubUI()
    app.mainloop()