def create_journal_tab(self):
    self.journal_frame = ttk.Frame(self.notebook)
    self.notebook.add(self.journal_frame, text="Журнал")

    # Левая панель - увеличена ширина с 300 до 450
    left_frame = ttk.Frame(self.journal_frame, width=450)
    left_frame.pack(side='left', fill='y', padx=5, pady=5)
    left_frame.pack_propagate(False)

    # Документы в начале месяца
    begin_frame = ttk.LabelFrame(left_frame, text="Документы в начале месяца", padding=5)
    begin_frame.pack(fill='both', expand=True, pady=5)

    # Создаём фрейм для списка и скролла
    begin_list_frame = ttk.Frame(begin_frame)
    begin_list_frame.pack(fill='both', expand=True, padx=2, pady=2)
    
    scrollbar_begin_h = ttk.Scrollbar(begin_list_frame, orient='horizontal')
    scrollbar_begin_v = ttk.Scrollbar(begin_list_frame, orient='vertical')
    self.begin_listbox = tk.Listbox(begin_list_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA',
                                    xscrollcommand=scrollbar_begin_h.set, yscrollcommand=scrollbar_begin_v.set)
    scrollbar_begin_h.config(command=self.begin_listbox.xview)
    scrollbar_begin_v.config(command=self.begin_listbox.yview)
    
    self.begin_listbox.pack(side='left', fill='both', expand=True)
    scrollbar_begin_v.pack(side='right', fill='y')
    scrollbar_begin_h.pack(side='bottom', fill='x')
    
    self.begin_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('begin'))
    
    btn_begin_add = ttk.Button(begin_frame, text="Добавить", command=lambda: self.add_client('begin'))
    btn_begin_add.pack(side='left', padx=5, pady=2)
    btn_begin_del = ttk.Button(begin_frame, text="Удалить", command=lambda: self.delete_client('begin'))
    btn_begin_del.pack(side='left', padx=5, pady=2)

    # Документы в конце месяца
    end_frame = ttk.LabelFrame(left_frame, text="Документы в конце месяца", padding=5)
    end_frame.pack(fill='both', expand=True, pady=5)
    
    end_list_frame = ttk.Frame(end_frame)
    end_list_frame.pack(fill='both', expand=True, padx=2, pady=2)
    
    scrollbar_end_h = ttk.Scrollbar(end_list_frame, orient='horizontal')
    scrollbar_end_v = ttk.Scrollbar(end_list_frame, orient='vertical')
    self.end_listbox = tk.Listbox(end_list_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA',
                                  xscrollcommand=scrollbar_end_h.set, yscrollcommand=scrollbar_end_v.set)
    scrollbar_end_h.config(command=self.end_listbox.xview)
    scrollbar_end_v.config(command=self.end_listbox.yview)
    
    self.end_listbox.pack(side='left', fill='both', expand=True)
    scrollbar_end_v.pack(side='right', fill='y')
    scrollbar_end_h.pack(side='bottom', fill='x')
    
    self.end_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('end'))
    
    btn_end_add = ttk.Button(end_frame, text="Добавить", command=lambda: self.add_client('end'))
    btn_end_add.pack(side='left', padx=5, pady=2)
    btn_end_del = ttk.Button(end_frame, text="Удалить", command=lambda: self.delete_client('end'))
    btn_end_del.pack(side='left', padx=5, pady=2)

    # Остальная часть (правая панель) без изменений...
    # ... (продолжение кода)