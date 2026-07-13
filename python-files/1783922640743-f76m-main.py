import sys
import os
import json
import shutil
from datetime import datetime
import copy
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QGroupBox, QListWidget, QListWidgetItem,
    QRadioButton, QButtonGroup, QLabel, QLineEdit, QFileDialog,
    QMessageBox, QSplitter, QTabWidget, QProgressDialog, QInputDialog
)
from PySide6.QtCore import Qt, Signal, QThread

# --- Constants ---
IGNORE_DIRS = {'.git', '.venv', '__pycache__', '.idea', '.vscode', 'node_modules'}

class FileTable(QTableWidget):
    files_dropped = Signal(list)

    def __init__(self, rows, cols):
        super().__init__(rows, cols)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DropOnly)
        self.setDragEnabled(False)
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)
        self.handle_dropped_files = None # Will be set by main window

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept() # Try using accept() instead of acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept() # Try using accept() instead of acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = [url.toLocalFile() for url in event.mimeData().urls()]
            if self.handle_dropped_files:
                self.handle_dropped_files(urls)
            else:
                self.files_dropped.emit(urls) # Fallback if not set
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

class ProcessingWorker(QThread):
    progress_update = Signal(int, str, int) # current_index, current_file_name, current_success_count
    task_log = Signal(str, str, str, str) # action, source, target, status
    finished_report = Signal(int, int, bool) # success_count, error_count, was_cancelled
    moved_items_report = Signal(list) # List of original paths that were successfully moved

    def __init__(self, items, active_rules, selected_kws, is_move, get_unique_path_func):
        super().__init__()
        self.items = items
        self.active_rules = active_rules
        self.selected_kws = selected_kws
        self.is_move = is_move
        self.get_unique_path = get_unique_path_func
        self.is_cancelled = False

    def run(self):
        success_count = 0
        error_count = 0
        was_cancelled = False
        action_name = "转移" if self.is_move else "复制"
        moved_success_paths = [] # To store paths of successfully moved items

        for i, item in enumerate(self.items):
            if self.is_cancelled:
                was_cancelled = True
                break
                
            file_path = item["path"]
            file_name = os.path.basename(file_path)
            
            self.progress_update.emit(i, file_name, success_count)
            
            # Determine which rules to use for this item
            item_specific_rules = item.get("rules")
            rules_to_use = {}
            kws_to_match = []

            if item_specific_rules: # Independent mode rules
                rules_to_use = item_specific_rules
                kws_to_match = list(item_specific_rules.keys()) # All keywords in item's rules are considered for matching
            else: # Batch mode rules (or fallback for independent mode if no specific rules)
                rules_to_use = self.active_rules
                kws_to_match = self.selected_kws

            # Safety check: if file was deleted externally
            if not os.path.exists(file_path):
                error_count += 1
                self.task_log.emit(action_name, file_name, "-", "失败: 源文件不存在")
                continue

            matched_paths = []
            for kw in kws_to_match:
                if kw in file_name:
                    if kw in rules_to_use:
                        matched_paths.extend(rules_to_use[kw])
                        if self.is_move:
                            break
            
            if not matched_paths:
                continue
                
            try:
                if self.is_move:
                    target_path = matched_paths[0]
                    os.makedirs(target_path, exist_ok=True)
                    dest = self.get_unique_path(os.path.join(target_path, file_name))
                    shutil.move(file_path, dest)
                    self.task_log.emit(action_name, file_name, target_path, "成功")
                    success_count += 1
                    moved_success_paths.append(file_path) # Record successfully moved item
                else: # Copy
                    for target_path in matched_paths:
                        os.makedirs(target_path, exist_ok=True)
                        dest = self.get_unique_path(os.path.join(target_path, file_name))
                        if not item["is_dir"]:
                            shutil.copy2(file_path, dest)
                        else:
                            shutil.copytree(file_path, dest)
                        self.task_log.emit(action_name, file_name, target_path, "成功")
                    success_count += 1
            except Exception as e:
                error_count += 1
                self.task_log.emit(action_name, file_name, matched_paths[0] if matched_paths else "-", f"失败: {str(e)}")
        
        self.finished_report.emit(success_count, error_count, was_cancelled)
        if self.is_move and not was_cancelled:
            self.moved_items_report.emit(moved_success_paths)

    def cancel(self):
        self.is_cancelled = True

class DistributeHelper(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True) # Ensure main window accepts drops
        self.setWindowTitle("分X助手")
        self.resize(1100, 750)
        self.rules = {} # {keyword: [paths]}
        self.file_folder_items = [] # list of {"path": str, "is_dir": bool, "checked": bool, "rules": {}}
        self.config_file = "config.json"
        self.is_task_cancelled_by_user = False # New flag to track user cancellation
        self.current_rule_mode = "batch" # "batch" or "independent"
        self.temp_independent_rules = None # Temporary buffer for editing independent rules
        
        self.init_ui()
        self.setup_styles()
        self.load_config()
        self.connect_signals()
        self.on_tab_changed(self.source_tabs.currentIndex()) # Set initial button visibility

    def connect_signals(self):
        self.source_tabs.currentChanged.connect(self.on_tab_changed)
        self.item_table.files_dropped.connect(self.handle_dropped_files)
        self.item_table.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.btn_clear_items.clicked.connect(self.clear_items)

        self.cb_select_all_items.stateChanged.connect(self.toggle_all_items)
        
        self.cb_select_all_rules.stateChanged.connect(self.toggle_all_rules)
        self.btn_add_kw.clicked.connect(self.add_keyword)
        self.btn_rename_kw.clicked.connect(self.rename_keyword)
        self.btn_del_kw.clicked.connect(self.delete_keyword)
        self.kw_list.itemSelectionChanged.connect(self.on_keyword_selected)
        self.btn_add_target_path.clicked.connect(self.add_target_path)
        
        self.btn_add_prefix_to_items.clicked.connect(self.batch_add_prefix_to_items)
        self.btn_start.clicked.connect(self.start_processing)
        self.rb_independent_mode.toggled.connect(self.on_rule_mode_changed)
        self.rb_batch_mode.toggled.connect(self.on_rule_mode_changed)
        self.btn_apply_rules.clicked.connect(self.apply_independent_rules)


        self.btn_clear_history.clicked.connect(self.clear_history)

    def on_tab_changed(self, index):
        # There is only one tab now, no specific button visibility logic needed based on index
        pass

    def on_rule_mode_changed(self):
        if self.rb_independent_mode.isChecked():
            self.current_rule_mode = "independent"
            # Trigger checked change logic to initialize temp_independent_rules
            self.update_temp_rules_from_checked_items()
            self.refresh_rule_management_ui()
        elif self.rb_batch_mode.isChecked():
            self.current_rule_mode = "batch"
            self.temp_independent_rules = None
            # In batch mode, always show global rules
            self.update_rule_management_ui_state()
            self.refresh_rule_management_ui()


    def handle_dropped_files(self, paths):
        for path in paths:
            is_directory = os.path.isdir(path)
            if not any(item["path"] == path for item in self.file_folder_items):
                self.file_folder_items.append({"path": path, "is_dir": is_directory, "checked": False, "rules": {}})
        self.refresh_item_table()



    def clear_items(self):
        self.file_folder_items = []
        self.refresh_item_table()

    def remove_item(self, index): 
        if 0 <= index < len(self.file_folder_items):
            self.file_folder_items.pop(index)
        self.refresh_item_table()

    def handle_moved_items(self, moved_paths):
        # Filter out the successfully moved items from the list
        self.file_folder_items = [item for item in self.file_folder_items if item["path"] not in moved_paths]
        self.refresh_item_table()
        self.update_count_labels()

    def _get_current_rules_and_item_data(self):
        """
        Helper to get the current rule dictionary and optionally the selected item data.
        Returns (rules_dict, checked_items_data_list) or (None, None) if in independent mode
        and no items are checked.
        In batch mode, returns (self.rules, []).
        In independent mode, returns (self.temp_independent_rules, checked_items_data_list).
        """
        if self.current_rule_mode == "batch":
            return self.rules, []
        elif self.current_rule_mode == "independent":
            checked_items_data = [item for item in self.file_folder_items if item.get("checked", False)]
            
            if len(checked_items_data) == 0:
                return None, []
            
            return self.temp_independent_rules, checked_items_data
        return None, []



    def refresh_item_table(self):
        self.item_table.setRowCount(0)
        for i, item in enumerate(self.file_folder_items):
            self.item_table.insertRow(i)
            base_name = os.path.basename(item["path"])
            item_type_str = "[文件夹]" if item["is_dir"] else "[文件]"
            display_name = f"{item_type_str} {base_name}"
            cb = QCheckBox(display_name)
            cb.setChecked(item["checked"])
            cb.stateChanged.connect(lambda state, idx=i: self.on_item_check_changed(state, idx))
            self.item_table.setCellWidget(i, 0, cb)
            
            btn_del = QPushButton("删除")
            btn_del.setFlat(True)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("color: blue; text-decoration: underline; border: none; background: transparent;")
            btn_del.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(btn_del)
            self.item_table.setCellWidget(i, 1, container)
        self.update_count_labels()

    def update_temp_rules_from_checked_items(self):
        # Update temporary independent rules buffer based on checked items
        if self.current_rule_mode == "independent":
            checked_items_data = [item for item in self.file_folder_items if item.get("checked", False)]
            
            if len(checked_items_data) == 0:
                self.temp_independent_rules = None
            elif len(checked_items_data) == 1:
                self.temp_independent_rules = copy.deepcopy(checked_items_data[0].get("rules", {}))
            else:
                first_item_rules = checked_items_data[0].get("rules", {})
                all_consistent = True
                for item in checked_items_data[1:]:
                    if item.get("rules", {}) != first_item_rules:
                        all_consistent = False
                        break
                
                if all_consistent:
                    self.temp_independent_rules = copy.deepcopy(first_item_rules)
                else:
                    self.temp_independent_rules = {}

    def on_item_check_changed(self, state, index):
        self.file_folder_items[index]["checked"] = (state == Qt.Checked.value)
        self.update_count_labels()
        self.update_temp_rules_from_checked_items()
        self.refresh_rule_management_ui()

    def on_item_selection_changed(self):
        # Row selection no longer affects the rule management UI in independent mode.
        pass


    def toggle_all_items(self, state):
        checked = (state == Qt.Checked.value)
        for item in self.file_folder_items:
            item["checked"] = checked
        self.refresh_item_table()
        self.update_temp_rules_from_checked_items()
        self.refresh_rule_management_ui()

    def toggle_all_rules(self, state):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来切换规则全选状态，或切换到批量模式。")
            return

        checked = (state == Qt.Checked.value)
        for i in range(self.kw_list.count()):
            item = self.kw_list.item(i)
            cb = self.kw_list.itemWidget(item)
            if cb:
                cb.setChecked(checked)


    def update_count_labels(self):
        checked_count = sum(1 for item in self.file_folder_items if item["checked"])
        self.lbl_item_count.setText(f"已选 {checked_count} 个文件/文件夹")

    # --- Rule Management ---
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                if isinstance(config_data, dict):
                    # New format: contains both global_rules and file_folder_items
                    self.rules = config_data.get("global_rules", {})
                    self.file_folder_items = config_data.get("file_folder_items", [])
                    # Ensure each item in file_folder_items has a 'rules' field
                    for item in self.file_folder_items:
                        if "rules" not in item:
                            item["rules"] = {}
                else:
                    # Old format: config_data is just the rules dictionary
                    self.rules = config_data
                    self.file_folder_items = [] # Clear file_folder_items if loading old format

                self.refresh_rule_management_ui()
                self.refresh_item_table() # Also refresh the item table after loading
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        try:
            config_data = {
                "global_rules": self.rules,
                "file_folder_items": self.file_folder_items
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")

    def update_rule_management_ui_state(self):
        """
        根据当前规则模式和文件/文件夹选择状态，更新规则管理界面的启用/禁用状态。
        """
        is_independent_mode = (self.current_rule_mode == "independent")
        checked_count = sum(1 for item in self.file_folder_items if item.get("checked", False))
        any_item_checked = (checked_count > 0)

        # Controls for rule editing buttons and list widgets
        enable_rule_editing = False
        if is_independent_mode:
            enable_rule_editing = any_item_checked # 只要有勾选项就启用
        else: # Batch mode
            enable_rule_editing = True # Always enable in batch mode

        self.cb_select_all_rules.setEnabled(enable_rule_editing)
        self.btn_add_kw.setEnabled(enable_rule_editing)
        self.btn_rename_kw.setEnabled(enable_rule_editing)
        self.btn_del_kw.setEnabled(enable_rule_editing)
        self.kw_list.setEnabled(enable_rule_editing)
        self.path_table.setEnabled(enable_rule_editing)
        self.btn_add_target_path.setEnabled(enable_rule_editing)

        # "Apply" button visibility and enabled state
        self.btn_apply_rules.setVisible(is_independent_mode)
        self.btn_apply_rules.setEnabled(enable_rule_editing) # Only enabled if editing is possible


    def refresh_rule_management_ui(self):
        """
        根据当前规则模式和文件/文件夹选择状态，刷新规则管理界面显示。
        """
        self.kw_list.clear()
        self.path_table.setRowCount(0)

        rules_dict_to_display, selected_items_data = self._get_current_rules_and_item_data()

        if rules_dict_to_display is None: # No selection in independent mode or other error
            # Display a message if no item is selected for independent mode
            if self.current_rule_mode == "independent" and selected_items_data is not None and len(selected_items_data) == 0:
                 self.statusBar().showMessage("提示: 请选择一个或多个文件/文件夹来设置独立规则。", 5000)
            self.update_rule_management_ui_state() # Ensure UI state is correct after refresh
            return

        # Check for inconsistency message in independent mode with multiple selections
        if self.current_rule_mode == "independent" and selected_items_data is not None and len(selected_items_data) > 1:
            first_item_rules = selected_items_data[0].get("rules", {})
            all_consistent = True
            for item in selected_items_data[1:]:
                if item.get("rules", {}) != first_item_rules:
                    all_consistent = False
                    break
            if not all_consistent:
                # Display warning about inconsistent rules
                self.statusBar().showMessage("提示: 当前多选项目规则不一致，编辑后将覆盖所有选中项的独立规则。", 5000)

        # Populate keyword list with rules_dict_to_display
        self._refresh_keyword_list_internal(rules_dict_to_display)

        # If a keyword was previously selected, re-select it to show its paths
        if self.kw_list.count() > 0:
            self.kw_list.setCurrentRow(0) # Select first keyword by default

        self.update_rule_management_ui_state() # Ensure UI state is correct after refresh

    def _refresh_keyword_list_internal(self, rules_dict):
        self.kw_list.clear()
        for kw in rules_dict.keys():
            item = QListWidgetItem()
            self.kw_list.addItem(item)
            
            cb = QCheckBox(kw)
            cb.setCheckState(Qt.Unchecked)
            # Link checkbox state to logic if needed, but for now just UI
            self.kw_list.setItemWidget(item, cb)
        self.path_table.setRowCount(0)

    def add_keyword(self):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来添加关键字，或切换到批量模式。")
            return

        from PySide6.QtWidgets import QInputDialog
        kw, ok = QInputDialog.getText(self, "新增关键字", "请输入关键字:")
        if ok and kw:
            if kw not in rules_dict:
                rules_dict[kw] = []
                self.refresh_rule_management_ui() # Refresh the UI after modification
                if self.current_rule_mode == "batch": # Only save global config
                    self.save_config()
            else:
                QMessageBox.warning(self, "提示", "关键字已存在")

    def rename_keyword(self):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来重命名关键字，或切换到批量模式。")
            return

        curr_item = self.kw_list.currentItem()
        if not curr_item:
            return
        cb = self.kw_list.itemWidget(curr_item)
        if not cb:
            return
        old_kw = cb.text()
        from PySide6.QtWidgets import QInputDialog
        new_kw, ok = QInputDialog.getText(self, "重命名关键字", "请输入新名称:", text=old_kw)
        if ok and new_kw and new_kw != old_kw:
            if new_kw in rules_dict:
                QMessageBox.warning(self, "提示", "新关键字已存在")
                return
            rules_dict[new_kw] = rules_dict.pop(old_kw)
            self.refresh_rule_management_ui() # Refresh the UI after modification
            if self.current_rule_mode == "batch": # Only save global config
                self.save_config()

    def delete_keyword(self):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来删除关键字，或切换到批量模式。")
            return

        # Find all checked keywords
        checked_kws = []
        for i in range(self.kw_list.count()):
            item = self.kw_list.item(i)
            cb = self.kw_list.itemWidget(item)
            if cb and cb.isChecked():
                checked_kws.append(cb.text())

        # If none checked, try the currently selected item
        if not checked_kws:
            curr_item = self.kw_list.currentItem()
            if curr_item:
                cb = self.kw_list.itemWidget(curr_item)
                if cb:
                    checked_kws.append(cb.text())

        if not checked_kws:
            QMessageBox.warning(self, "提示", "请先勾选或选择要删除的关键字")
            return

        kw_str = ", ".join(checked_kws)
        if QMessageBox.question(self, "确认", f"确定删除关键字 '{kw_str}' 吗？") == QMessageBox.Yes:
            for kw in checked_kws:
                if kw in rules_dict:
                    del rules_dict[kw]
            self.refresh_rule_management_ui() # Refresh the UI after modification
            if self.current_rule_mode == "batch": # Only save global config
                self.save_config()
            self.statusBar().showMessage(f"已删除关键字: {kw_str}")

    def on_keyword_selected(self):
        curr_item = self.kw_list.currentItem()
        if not curr_item:
            self.path_table.setRowCount(0)
            return
        cb = self.kw_list.itemWidget(curr_item)
        if cb:
            current_rules_dict = self.rules
            if self.current_rule_mode == "independent":
                current_rules_dict = self.temp_independent_rules
                if current_rules_dict is None:
                    # No items selected or no rules, so no paths to show
                    self.path_table.setRowCount(0)
                    return
            self.refresh_path_table(cb.text(), current_rules_dict)

    def refresh_path_table(self, kw, rules_dict):
        paths = rules_dict.get(kw, [])
        self.path_table.setRowCount(0)
        for i, path in enumerate(paths):
            self.path_table.insertRow(i)
            self.path_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.path_table.setItem(i, 1, QTableWidgetItem(path))
            
            # Action buttons layout
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(10)
            action_layout.setAlignment(Qt.AlignCenter) # Center the layout contents
            
            btn_reassign = QPushButton("重新指定")
            btn_reassign.setFlat(True)
            btn_reassign.setCursor(Qt.PointingHandCursor)
            btn_reassign.setStyleSheet("color: blue; text-decoration: underline; border: none; background: transparent; padding: 0;")
            btn_reassign.clicked.connect(lambda _, k=kw, p=path: self.reassign_target_path(k, p))
            
            btn_del = QPushButton("删除")
            btn_del.setFlat(True)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setStyleSheet("color: blue; text-decoration: underline; border: none; background: transparent; padding: 0;")
            btn_del.clicked.connect(lambda _, k=kw, p=path: self.remove_target_path(k, p))
            
            action_layout.addWidget(btn_reassign)
            action_layout.addWidget(btn_del)
            
            self.path_table.setCellWidget(i, 2, action_widget)

    def reassign_target_path(self, kw, old_path):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来重新指定目标路径，或切换到批量模式。")
            return

        new_path = QFileDialog.getExistingDirectory(self, "重新指定目标路径", old_path)
        if new_path and new_path != old_path:
            if kw in rules_dict and old_path in rules_dict[kw]: # Ensure kw and old_path exist before trying to modify
                idx = rules_dict[kw].index(old_path)
                rules_dict[kw][idx] = new_path
                self.refresh_path_table(kw, rules_dict) # Pass rules_dict to refresh_path_table
                if self.current_rule_mode == "batch": # Only save global config
                    self.save_config()

    def add_target_path(self):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来添加目标路径，或切换到批量模式。")
            return

        curr_item = self.kw_list.currentItem()
        if not curr_item:
            QMessageBox.warning(self, "提示", "请先选择一个关键字")
            return

        cb = self.kw_list.itemWidget(curr_item)
        if not cb:
            return
        kw = cb.text()

        path = QFileDialog.getExistingDirectory(self, "选择目标路径")
        if path:
            if kw in rules_dict and path not in rules_dict[kw]:
                rules_dict[kw].append(path)
                self.refresh_path_table(kw, rules_dict) # Pass rules_dict to refresh_path_table
                if self.current_rule_mode == "batch": # Only save global config
                    self.save_config()

    def remove_target_path(self, kw, path):
        rules_dict, selected_item_data = self._get_current_rules_and_item_data()
        if rules_dict is None:
            QMessageBox.warning(self, "提示", "请在独立模式下选择一个文件/文件夹来删除目标路径，或切换到批量模式。")
            return

        if kw in rules_dict and path in rules_dict[kw]:
            rules_dict[kw].remove(path)
            self.refresh_path_table(kw, rules_dict) # Pass rules_dict to refresh_path_table
            if self.current_rule_mode == "batch": # Only save global config
                self.save_config()

    def apply_independent_rules(self):
        if self.current_rule_mode != "independent":
            return
            
        checked_items_data = [item for item in self.file_folder_items if item.get("checked", False)]
        
        if not checked_items_data:
            QMessageBox.warning(self, "提示", "请先勾选要应用规则的文件/文件夹。")
            return

        if self.temp_independent_rules is None:
             QMessageBox.warning(self, "提示", "当前没有可应用的规则。")
             return

        # Apply the temporary rules to all checked items
        for item in checked_items_data:
            item["rules"] = copy.deepcopy(self.temp_independent_rules)
            
        # Save to persist the changes
        self.save_config()
        
        if len(checked_items_data) == 1:
            QMessageBox.information(self, "成功", f"规则已应用到 '{os.path.basename(checked_items_data[0]['path'])}'。")
        else:
            QMessageBox.information(self, "成功", f"规则已应用到 {len(checked_items_data)} 个勾选项。")
        
        # Refresh UI to clear the inconsistency warning if there was one
        self.refresh_rule_management_ui()




    def add_history_entry(self, action, source, target, status):
        row = self.history_table.rowCount()
        self.history_table.insertRow(row)
        
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.history_table.setItem(row, 0, QTableWidgetItem(time_str))
        self.history_table.setItem(row, 1, QTableWidgetItem(action))
        self.history_table.setItem(row, 2, QTableWidgetItem(source))
        self.history_table.setItem(row, 3, QTableWidgetItem(target))
        
        status_item = QTableWidgetItem(status)
        if "失败" in status:
            status_item.setForeground(Qt.red)
        else:
            status_item.setForeground(Qt.darkGreen)
        self.history_table.setItem(row, 4, status_item)
        
        # Auto scroll to bottom
        self.history_table.scrollToBottom()

    def clear_history(self):
        if QMessageBox.question(self, "确认", "确定清空所有历史记录吗？") == QMessageBox.Yes:
            self.history_table.setRowCount(0)

    # --- Core Logic ---
    def batch_add_prefix_to_items(self):
        selected_items = [item for item in self.file_folder_items if item["checked"]]
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要处理的文件/文件夹")
            return
        
        selected_kws = []
        for i in range(self.kw_list.count()):
            item = self.kw_list.item(i)
            cb = self.kw_list.itemWidget(item)
            if cb and cb.isChecked():
                selected_kws.append(cb.text())
        
        if not selected_kws:
            QMessageBox.warning(self, "提示", "请先在规则列表中勾选要添加的关键字")
            return
        
        prefix = "_".join(selected_kws) + "_"
        
        success_count = 0
        error_count = 0
        
        for item in selected_items:
            old_path = item["path"]
            dir_name = os.path.dirname(old_path)
            base_name = os.path.basename(old_path)
            new_name = prefix + base_name
            new_path = os.path.join(dir_name, new_name)
            
            try:
                os.rename(old_path, new_path)
                item["path"] = new_path
                success_count += 1
                item_type_str = "文件" if not item["is_dir"] else "文件夹"
                self.statusBar().showMessage(f"已重命名{item_type_str}: {base_name}")
                self.add_history_entry("添加前缀", base_name, new_name, "成功")
            except Exception as e:
                error_count += 1
                item_type_str = "文件" if not item["is_dir"] else "文件夹"
                self.statusBar().showMessage(f"重命名{item_type_str}失败: {base_name} - {e}")
                self.add_history_entry("添加前缀", base_name, new_name, f"失败: {str(e)}")
        
        QMessageBox.information(self, "完成", f"文件/文件夹前缀添加完成。成功: {success_count}, 失败: {error_count}")
        self.refresh_item_table()

    def start_processing(self):
        # 1. Gather source items (Snapshot)
        source_items = self.file_folder_items

        selected_sources = [item for item in source_items if item["checked"]]
        
        if not selected_sources:
            QMessageBox.warning(self, "提示", f"请先选择要处理的文件/文件夹")
            return
        
        active_rules = {} # Rules to be used for processing
        selected_kws_for_worker = [] # Keywords to be passed to worker (might be empty in independent mode)

        if self.current_rule_mode == "batch":
            # 2. Get active rules for batch mode
            selected_kws = []
            for i in range(self.kw_list.count()):
                item = self.kw_list.item(i)
                cb = self.kw_list.itemWidget(item)
                if cb and cb.isChecked():
                    selected_kws.append(cb.text())
            
            if not selected_kws:
                QMessageBox.warning(self, "提示", "请先在规则列表中勾选要执行的关键字规则")
                return

            active_rules = {kw: self.rules[kw] for kw in selected_kws if kw in self.rules and self.rules[kw]}
            selected_kws_for_worker = selected_kws # Pass checked KWs to worker
            if not active_rules:
                QMessageBox.warning(self, "提示", "勾选的规则没有设置目标路径")
                return
        
        elif self.current_rule_mode == "independent":
            # In independent mode, each item will carry its own rules
            # We don't need global active_rules here, but will check per-item rules
            # The worker thread will be responsible for checking item["rules"]
            # We'll pass an empty active_rules and selected_kws, and worker will look at item["rules"]
            pass # No global active_rules or selected_kws in this mode, worker handles per-item

        # 3. Build detailed item list (Snapshot)
        items_to_process = []
        for item in selected_sources:
            # In independent mode, also pass the item's rules
            item_data = {"path": item["path"], "is_dir": item["is_dir"], "source_item": item}
            if self.current_rule_mode == "independent" and "rules" in item and item["rules"]:
                item_data["rules"] = item["rules"]
            else:
                item_data["rules"] = {} # Ensure rules field exists, even if empty
            items_to_process.append(item_data)

        if not items_to_process:
            QMessageBox.warning(self, "提示", "没有找到要处理的文件或文件夹")
            return

        # 4. Determine processing mode (Move/Copy)
        is_move = (self.mode_group.checkedButton().text() == "转移")

        # 5. Start worker thread
        self.is_task_cancelled_by_user = False # Reset cancellation flag for new task
        self.progress_dialog = QProgressDialog("正在处理...", "取消", 0, len(items_to_process), self)
        self.progress_dialog.setWindowTitle("处理进度")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.canceled.connect(self.cancel_processing)

        self.worker = ProcessingWorker(items_to_process, active_rules, selected_kws_for_worker, is_move, self.get_unique_path)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.task_log.connect(self.add_history_entry)
        self.worker.finished_report.connect(self.processing_finished)
        self.worker.moved_items_report.connect(self.handle_moved_items)
        self.worker.start()
        self.progress_dialog.show()

    def update_progress(self, index, file_name, success_count):
        self.progress_dialog.setValue(index)
        total = self.progress_dialog.maximum()
        self.progress_dialog.setLabelText(
            f"正在扫描: {index + 1} / {total}\n"
            f"已发现匹配项目: {success_count}\n"
            f"当前: {file_name}"
        )

    def processing_finished(self, success_count, error_count, was_cancelled):
        # Disconnect the canceled signal before closing to prevent triggering cancel_processing
        try:
            self.progress_dialog.canceled.disconnect(self.cancel_processing)
        except Exception:
            pass # Ignore if not connected
            
        self.progress_dialog.close()
        self.refresh_item_table()
        
        if was_cancelled:
            QMessageBox.information(self, "取消", "任务已取消！")
        else:
            QMessageBox.information(self, "完成", f"任务处理结束！\n成功: {success_count} 个项目\n失败: {error_count} 个")
        
        # Reset the user cancellation flag after handling the message
        self.is_task_cancelled_by_user = False

    def cancel_processing(self):
        self.is_task_cancelled_by_user = True # Mark as cancelled by user
        if self.worker and self.worker.isRunning():
            self.worker.cancel() # Just set the flag, don't wait

    def get_unique_path(self, path):
        if not os.path.exists(path):
            return path
            
        dir_name, file_name = os.path.split(path)
        name, ext = os.path.splitext(file_name)
        
        # First conflict: append "_复件"
        new_name = f"{name}_复件{ext}"
        new_path = os.path.join(dir_name, new_name)
        
        if not os.path.exists(new_path):
            return new_path
            
        # Subsequent conflicts: append "(2)", "(3)", etc.
        counter = 2
        while True:
            new_name = f"{name}_复件({counter}){ext}"
            new_path = os.path.join(dir_name, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1
            # Safety break to avoid infinite loop
            if counter > 1000:
                return new_path

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5) # Reduce spacing between major sections
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        self.statusBar().showMessage("准备就绪")
        
        # Main Vertical Splitter: Top (Content) and Bottom (History)
        self.main_v_splitter = QSplitter(Qt.Vertical)
        self.main_v_splitter.setHandleWidth(2) # Thinner handle
        self.main_v_splitter.setAcceptDrops(True)

        # Top Horizontal Splitter: Left (Files) and Right (Rules)
        self.top_h_splitter = QSplitter(Qt.Horizontal)
        self.top_h_splitter.setAcceptDrops(True)

        # --- Left Side: Source Items (Tabs) ---
        left_widget = QWidget()
        left_widget.setAcceptDrops(True)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        
        self.source_tabs = QTabWidget()
        self.source_tabs.setAcceptDrops(True)
        
        # File/Folder Tab
        file_folder_tab_widget = QWidget()
        file_folder_tab_widget.setAcceptDrops(True)
        file_folder_tab_layout = QVBoxLayout(file_folder_tab_widget)
        
        file_folder_header_layout = QHBoxLayout()
        self.cb_select_all_items = QCheckBox("全选")
        self.lbl_item_count = QLabel("已选 0 个文件/文件夹")
        file_folder_header_layout.addWidget(self.cb_select_all_items)
        file_folder_header_layout.addStretch()
        file_folder_header_layout.addWidget(self.lbl_item_count)
        
        self.item_table = FileTable(0, 2)
        # Pass the handle_dropped_files method to the FileTable
        self.item_table.handle_dropped_files = self.handle_dropped_files
        self.item_table.setHorizontalHeaderLabels(["", "操作"])
        self.item_table.horizontalHeader().setVisible(False)
        self.item_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.item_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.item_table.setColumnWidth(1, 60)
        self.item_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.item_table.setShowGrid(False)
        self.item_table.setStyleSheet("QTableWidget { border: none; }")
        
        file_folder_tab_layout.addLayout(file_folder_header_layout)
        file_folder_tab_layout.addWidget(self.item_table)
        self.source_tabs.addTab(file_folder_tab_widget, "文件/文件夹")

        left_layout.addWidget(self.source_tabs)
        
        # Action Buttons for current tab
        btn_add_layout = QHBoxLayout()
        self.btn_clear_items = QPushButton("清空列表")
        self.btn_clear_items.setMinimumHeight(35) # Set same height
        self.btn_add_prefix_to_items = QPushButton("新增文件/文件夹前缀关键字")
        self.btn_add_prefix_to_items.setMinimumHeight(35)
        self.btn_add_prefix_to_items.setStyleSheet("background-color: #f0f0f0;")

        btn_add_layout.addWidget(self.btn_add_prefix_to_items) # Left button
        btn_add_layout.addStretch() # Space in between
        btn_add_layout.addWidget(self.btn_clear_items) # Right button
        
        left_layout.addLayout(btn_add_layout)
        
        # --- Right Side: Rule Management ---
        right_widget = QGroupBox("分X规则管理")
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(2)
        right_layout.setContentsMargins(10, 5, 10, 10)
        
        rule_desc = QLabel("所选文件或目录根据所选规则进行分X整理")
        rule_desc.setStyleSheet("color: orange; font-size: 11px; margin: 0; padding: 0;")
        rule_desc.setFixedHeight(15)
        
        rule_header_layout = QHBoxLayout()
        rule_header_layout.setContentsMargins(0, 0, 0, 0)
        self.cb_select_all_rules = QCheckBox("全选")
        self.btn_add_kw = QPushButton("新增关键字")
        self.btn_add_kw.setFlat(True)
        self.btn_add_kw.setStyleSheet("color: blue; text-decoration: underline; border: none;")
        self.btn_rename_kw = QPushButton("重命名关键字")
        self.btn_rename_kw.setFlat(True)
        self.btn_rename_kw.setStyleSheet("color: blue; text-decoration: underline; border: none;")
        self.btn_del_kw = QPushButton("删除关键字")
        self.btn_del_kw.setFlat(True)
        self.btn_del_kw.setStyleSheet("color: blue; text-decoration: underline; border: none;")
        
        rule_header_layout.addWidget(self.cb_select_all_rules)
        rule_header_layout.addStretch()
        rule_header_layout.addWidget(self.btn_add_kw)
        rule_header_layout.addWidget(self.btn_rename_kw)
        rule_header_layout.addWidget(self.btn_del_kw)
        
        # Rule Splitter: Keywords and Paths
        rule_content_splitter = QSplitter(Qt.Horizontal)
        
        # Keyword List
        self.kw_list = QListWidget()
        
        # Path area: Table + Button
        path_area_widget = QWidget()
        path_area_layout = QVBoxLayout(path_area_widget)
        path_area_layout.setContentsMargins(0, 0, 0, 0)
        path_area_layout.setSpacing(0)
        
        self.path_table = QTableWidget(0, 3)
        self.path_table.setHorizontalHeaderLabels(["序号", "目标路径", "操作"])
        self.path_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.path_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.path_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.path_table.setColumnWidth(2, 120)
        
        self.btn_add_target_path = QPushButton("新增目标路径")
        self.btn_add_target_path.setMinimumHeight(35)
        self.btn_add_target_path.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ddd; border-top: none;")
        
        path_area_layout.addWidget(self.path_table)
        path_area_layout.addWidget(self.btn_add_target_path)
        
        rule_content_splitter.addWidget(self.kw_list)
        rule_content_splitter.addWidget(path_area_widget)
        rule_content_splitter.setStretchFactor(0, 1)
        rule_content_splitter.setStretchFactor(1, 2)
        
        right_layout.addWidget(rule_desc)
        right_layout.addLayout(rule_header_layout)
        right_layout.addWidget(rule_content_splitter)

        self.btn_apply_rules = QPushButton("应用规则")
        self.btn_apply_rules.setMinimumHeight(35)
        self.btn_apply_rules.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_apply_rules.setVisible(False) # Initially hidden
        right_layout.addWidget(self.btn_apply_rules)
        
        self.top_h_splitter.addWidget(left_widget)
        self.top_h_splitter.addWidget(right_widget)
        self.top_h_splitter.setStretchFactor(0, 1)
        self.top_h_splitter.setStretchFactor(1, 1)
        
        # --- Bottom Area: History ---
        history_widget = QGroupBox()
        history_widget.setObjectName("history_panel")
        history_layout = QVBoxLayout(history_widget)
        history_layout.setContentsMargins(10, 5, 10, 10)
        history_layout.setSpacing(5)
        
        history_header = QHBoxLayout()
        history_header.setContentsMargins(0, 0, 0, 0)
        
        history_title = QLabel("操作记录")
        history_title.setStyleSheet("font-weight: bold; color: #303133;")
        history_header.addWidget(history_title)
        
        history_header.addStretch()
        self.btn_clear_history = QPushButton("清空记录")
        self.btn_clear_history.setFlat(True)
        self.btn_clear_history.setStyleSheet("color: blue; text-decoration: underline; border: none; padding: 0;")
        history_header.addWidget(self.btn_clear_history)
        
        self.history_table = QTableWidget(0, 5)
        self.history_table.setHorizontalHeaderLabels(["时间", "操作类型", "源文件/目录", "目标路径", "状态"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        history_layout.addLayout(history_header)
        history_layout.addWidget(self.history_table)
        
        # Combine in main vertical splitter
        self.main_v_splitter.addWidget(self.top_h_splitter)
        self.main_v_splitter.addWidget(history_widget)
        self.main_v_splitter.setStretchFactor(0, 2) # Give more space to history (ratio 2:1 instead of 3:1)
        self.main_v_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.main_v_splitter)
        
        # Bottom Layout (Start button and mode)
        bottom_layout = QHBoxLayout()
        
        # Rule Mode selection
        rule_mode_group_box = QGroupBox("规则模式")
        rule_mode_layout = QVBoxLayout(rule_mode_group_box)
        self.rule_mode_group = QButtonGroup(self)
        self.rb_independent_mode = QRadioButton("独立模式")
        self.rb_batch_mode = QRadioButton("批量模式")
        self.rb_batch_mode.setChecked(True) # Default to batch mode
        self.rule_mode_group.addButton(self.rb_independent_mode)
        self.rule_mode_group.addButton(self.rb_batch_mode)
        
        rule_mode_layout.addWidget(self.rb_independent_mode)
        self.independent_mode_tip = QLabel("独立模式下，请在左侧列表勾选文件/文件夹，以便在“分X规则管理”中进行操作。")
        self.independent_mode_tip.setStyleSheet("color: #FFA500; padding-left: 20px;")
        rule_mode_layout.addWidget(self.independent_mode_tip)
        rule_mode_layout.addWidget(self.rb_batch_mode)
        
        bottom_layout.addWidget(rule_mode_group_box)
        bottom_layout.addStretch() # Spacer
        
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(0)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        
        mode_radio_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.rb_move = QRadioButton("转移")
        self.rb_copy = QRadioButton("复制")
        self.rb_move.setChecked(True)
        self.mode_group.addButton(self.rb_move)
        self.mode_group.addButton(self.rb_copy)
        mode_radio_layout.addWidget(QLabel("分X模式："))
        mode_radio_layout.addWidget(self.rb_move)
        mode_radio_layout.addWidget(self.rb_copy)
        mode_radio_layout.addStretch()
        
        mode_tip = QLabel("温馨提示：转移模式下文件仅有一个归宿，匹配多条规则时以首项为准")
        mode_tip.setStyleSheet("color: orange; font-size: 11px; margin: 0; padding: 0;")
        mode_tip.setFixedHeight(15)
        
        mode_layout.addLayout(mode_radio_layout)
        mode_layout.addWidget(mode_tip)
        
        self.btn_start = QPushButton("开始分X")
        self.btn_start.setMinimumSize(150, 45)
        
        bottom_layout.addLayout(mode_layout)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_start)
        
        main_layout.addLayout(bottom_layout)

    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f8f9fa; }
            QWidget { font-family: "Microsoft YaHei", "Segoe UI", sans-serif; font-size: 12px; }
            
            /* 统一按钮样式 */
            QPushButton { 
                padding: 6px 15px; 
                border: 1px solid #dcdfe6; 
                border-radius: 4px; 
                background-color: #ffffff;
                color: #606266;
            }
            QPushButton:hover { 
                background-color: #f5f7fa; 
                color: #409eff;
                border-color: #c6e2ff;
            }
            QPushButton:pressed {
                background-color: #ecf5ff;
            }

            /* 主按钮样式 (开始分X) */
            QPushButton#btn_start { 
                background-color: #409eff; 
                color: white; 
                font-size: 14px; 
                font-weight: bold; 
                border: none;
            }
            QPushButton#btn_start:hover { background-color: #66b1ff; }
            QPushButton#btn_start:pressed { background-color: #3a8ee6; }

            /* 次要功能按钮 (灰底样式) */
            QPushButton.secondary-btn {
                background-color: #f4f4f5;
                border: 1px solid #e9e9eb;
            }
            QPushButton.secondary-btn:hover {
                background-color: #e9e9eb;
                border-color: #d3d4d6;
                color: #909399;
            }

            /* 表格和列表样式 */
            QTableWidget, QListWidget { 
                background-color: white; 
                border: 1px solid #dcdfe6; 
                border-radius: 4px; 
                gridline-color: #f2f6fc;
            }
            QHeaderView::section { 
                background-color: #f5f7fa; 
                padding: 4px; 
                border: 1px solid #ebeef5;
                font-weight: bold;
                color: #909399;
            }

            /* 修复 GroupBox 标题飞出问题 */
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #dcdfe6; 
                margin-top: 20px; 
                padding-top: 10px; 
                background-color: white;
                border-radius: 4px;
            }
            /* 历史记录专用的紧凑样式，覆盖全局 QGroupBox 边距 */
            #history_panel {
                margin-top: 0px;
                padding-top: 5px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; /* 强制标题在顶部左侧 */
                left: 10px; 
                padding: 0 5px; 
                color: #303133;
                background-color: transparent;
            }

            /* 选项卡样式 */
            QTabWidget::pane { border: 1px solid #dcdfe6; border-radius: 4px; top: -1px; }
            QTabBar::tab {
                background: #f5f7fa;
                border: 1px solid #dcdfe6;
                padding: 5px 20px;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                border-color: #dcdfe6;
                border-bottom: 2px solid white;
                font-weight: bold;
            }
        """)
        self.btn_start.setObjectName("btn_start")
        # 为功能按钮添加自定义类名以便统一控制
        self.btn_add_prefix_to_items.setProperty("class", "secondary-btn")
        self.btn_add_target_path.setProperty("class", "secondary-btn")


        self.btn_clear_items.setProperty("class", "secondary-btn")
        self.btn_clear_history.setProperty("class", "secondary-btn")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DistributeHelper()
    window.show()
    sys.exit(app.exec())
