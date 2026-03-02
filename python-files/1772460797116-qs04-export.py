import pyodbc
import pandas as pd
import csv
from datetime import datetime
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

class EstrazioneDatiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Estrazione Dati DIAMANTE - CSV Exporter")
        self.root.geometry("650x550")
        self.root.resizable(False, False)
        
        # Variabili
        self.server = tk.StringVar(value="localhost")
        self.database = tk.StringVar(value="DIAMANTE")
        self.auth_type = tk.StringVar(value="windows")
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.output_file = tk.StringVar(value="dati_diamante_completi.csv")
        self.status_text = tk.StringVar(value="Pronto")
        
        self.create_widgets()
        self.toggle_auth()
        
    def create_widgets(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Titolo
        title_label = ttk.Label(main_frame, text="Estrazione Completa Dati da Vista_Refertare_All", 
                                font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Server
        ttk.Label(main_frame, text="Server SQL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.server, width=40).grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        # Database
        ttk.Label(main_frame, text="Database:").grid(row=2, column=0, sticky=tk.W, pady=5)
        db_frame = ttk.Frame(main_frame)
        db_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Entry(db_frame, textvariable=self.database, width=30, state='readonly').pack(side=tk.LEFT)
        ttk.Label(db_frame, text="(fisso: DIAMANTE)", font=('Arial', 8)).pack(side=tk.LEFT, padx=5)
        
        # Tipo autenticazione
        ttk.Label(main_frame, text="Autenticazione:").grid(row=3, column=0, sticky=tk.W, pady=5)
        auth_frame = ttk.Frame(main_frame)
        auth_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(auth_frame, text="Windows", variable=self.auth_type, 
                       value="windows", command=self.toggle_auth).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(auth_frame, text="SQL Server", variable=self.auth_type, 
                       value="sql", command=self.toggle_auth).pack(side=tk.LEFT, padx=5)
        
        # Credenziali SQL
        self.sql_frame = ttk.Frame(main_frame)
        self.sql_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.sql_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.sql_frame, textvariable=self.username, width=30).grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(self.sql_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.sql_frame, textvariable=self.password, show="*", width=30).grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # File di output
        ttk.Label(main_frame, text="File CSV output:").grid(row=5, column=0, sticky=tk.W, pady=5)
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=5, column=1, columnspan=2, sticky=tk.W, pady=5)
        ttk.Entry(file_frame, textvariable=self.output_file, width=30).pack(side=tk.LEFT)
        ttk.Button(file_frame, text="Sfoglia...", command=self.browse_output).pack(side=tk.LEFT, padx=5)
        
        # Informazioni
        info_frame = ttk.LabelFrame(main_frame, text="Informazioni", padding="5")
        info_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text="• Estrazione di TUTTI i record senza limiti", 
                 foreground="blue").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="• I campi commentati nella query originale sono esclusi", 
                 foreground="green").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(info_frame, text="• Il file CSV sarà salvato con encoding UTF-8", 
                 foreground="green").grid(row=2, column=0, sticky=tk.W)
        
        # Barra di progresso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.grid(row=7, column=0, columnspan=3, pady=10)
        
        # Status
        ttk.Label(main_frame, textvariable=self.status_text).grid(row=8, column=0, columnspan=3, pady=5)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=3, pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Avvia Estrazione", 
                                       command=self.start_extraction, width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Esci", command=self.root.quit, width=10).pack(side=tk.LEFT, padx=5)
        
    def toggle_auth(self):
        if self.auth_type.get() == "windows":
            self.sql_frame.grid_remove()
        else:
            self.sql_frame.grid()
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="dati_diamante_completi.csv"
        )
        if filename:
            self.output_file.set(filename)
    
    def start_extraction(self):
        # Disabilita il pulsante durante l'estrazione
        self.start_button.config(state='disabled')
        self.progress.start()
        self.status_text.set("Estrazione in corso...")
        
        # Avvia l'estrazione in un thread separato
        thread = threading.Thread(target=self.extract_data)
        thread.daemon = True
        thread.start()
    
    def extract_data(self):
        try:
            # Costruzione stringa di connessione
            if self.auth_type.get() == "windows":
                connection_string = f'DRIVER={{SQL Server}};SERVER={self.server.get()};DATABASE={self.database.get()};Trusted_Connection=yes;'
            else:
                connection_string = f'DRIVER={{SQL Server}};SERVER={self.server.get()};DATABASE={self.database.get()};UID={self.username.get()};PWD={self.password.get()};'
            
            # Query SQL SENZA TOP - tutti i record
            query = """
            USE [DIAMANTE]
            
            SELECT 
                  [DATAACC]
                  ,[DATAPREL]
                  ,[Num_Acc]
                  ,[Cat_Valori_Normali]
                  ,[Diagnosi]
                  ,[DATARIT]
                  ,[COD_ES_CONT]
                  ,[ES_CONT_DESC]
                  ,[Aggiunta_Descrizione]
                  ,[SESA_CONT_ID]
                  ,[Ris_Numerico]
                  ,[Ris_Alfabetico]
                  ,[Risultato_Patologico]
                  ,[Ris_Note]
                  ,[Stringa_Referto]
                  ,[Val_Minimo]
                  ,[Val_Massimo]
                  ,[SESA_REF_DESC]
                  ,[Moltiplicatore]
                  ,[Unita]
                  ,[Sesso]
                  ,[Eta_Cliente]
                  ,[DATAMEST]
                  ,[DATAREF]
                  ,[ID]
                  ,[Commento_Referto]
                  ,[Info]
                  ,[Set_Gestazione]
                  ,[Descrizione]
                  ,[Modello]
                  ,[DATA_PREL]
                  ,[Progressivo]
                  ,[Letto]
                  ,[Cod_Mnemonico]
                  ,[Ref_Stampato]
                  ,[Codice_Mnemonico]
                  ,[METOD]
                  ,[Num_Frazionamento]
                  ,[Validato]
                  ,[Nota_Referto]
                  ,[Valore_Normale_Applicato]
                  ,[OraAcc]
                  ,[Eta]
                  ,[STRUM]
                  ,[Urgenza]
                  ,[Tipo_Risultato]
            FROM [dbo].[Vista_Refertare_All]
            """
            
            # Connessione al database
            self.root.after(0, lambda: self.status_text.set("Connessione al database..."))
            conn = pyodbc.connect(connection_string, timeout=30)
            
            # Esecuzione della query
            self.root.after(0, lambda: self.status_text.set("Esecuzione query in corso..."))
            
            # Legge i dati in chunks per gestire grandi volumi
            chunk_size = 10000
            first_chunk = True
            total_rows = 0
            
            for chunk in pd.read_sql(query, conn, chunksize=chunk_size):
                if first_chunk:
                    # Scrive header e primo chunk
                    chunk.to_csv(self.output_file.get(), 
                                index=False, 
                                encoding='utf-8-sig',
                                quoting=csv.QUOTE_NONNUMERIC,
                                sep=',',
                                mode='w')
                    first_chunk = False
                else:
                    # Appende i chunk successivi senza header
                    chunk.to_csv(self.output_file.get(), 
                                index=False, 
                                encoding='utf-8-sig',
                                quoting=csv.QUOTE_NONNUMERIC,
                                sep=',',
                                mode='a',
                                header=False)
                
                total_rows += len(chunk)
                self.root.after(0, lambda rows=total_rows: self.status_text.set(f"Estratti {rows} record..."))
            
            conn.close()
            
            # Completamento
            self.root.after(0, self.extraction_complete, total_rows)
            
        except pyodbc.Error as e:
            self.root.after(0, self.extraction_error, f"Errore database: {str(e)}")
        except Exception as e:
            self.root.after(0, self.extraction_error, f"Errore: {str(e)}")
    
    def extraction_complete(self, total_rows):
        self.progress.stop()
        self.start_button.config(state='normal')
        self.status_text.set(f"Completato! Estratti {total_rows} record")
        messagebox.showinfo("Successo", 
                           f"Estrazione completata con successo!\n\n"
                           f"Record estratti: {total_rows}\n"
                           f"File salvato in: {self.output_file.get()}")
    
    def extraction_error(self, error_message):
        self.progress.stop()
        self.start_button.config(state='normal')
        self.status_text.set("Errore durante l'estrazione")
        messagebox.showerror("Errore", error_message)

def main():
    root = tk.Tk()
    app = EstrazioneDatiApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()