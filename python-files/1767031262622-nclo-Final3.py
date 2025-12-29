import mysql.connector as mysql
import tkinter as tk
from tkinter import ttk,messagebox


def initialize_database(passwd):
    try:
        # Step 1: Connect to MySQL server (no database)
        server_conn = mysql.connect(
            host="localhost",
            user="root",
            password=passwd
        )
        cursor = server_conn.cursor()

        # Step 2: Check if database exists
        cursor.execute("SHOW DATABASES")
        databases = [db[0].lower() for db in cursor.fetchall()]

        if "cs_project2" not in databases:
            cursor.execute("CREATE DATABASE cs_Project2")

        # Step 3: Connect to cs_Project database
        server_conn.close()
        db_conn = mysql.connect(
            host="localhost",
            user="root",
            password=passwd,
            database="cs_Project2"
        )
        cursor = db_conn.cursor()

        # Step 4: Check if table exists
        cursor.execute("SHOW TABLES")
        tables = [tbl[0].lower() for tbl in cursor.fetchall()]

        if "disease_database" not in tables:
            cursor.execute("""
                CREATE TABLE disease_database (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    disease_name VARCHAR(150),
                    short_description TEXT,
                    symptoms TEXT,
                    treatments TEXT
                )
            """)

        # Step 5: Check if table has data
        cursor.execute("SELECT COUNT(*) FROM disease_database")
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("ALTER TABLE disease_database AUTO_INCREMENT = 1")
            diseases = [
                ("Common Cold","A mild viral infection of the nose and throat.","Sneezing, cough, runny nose","Rest, fluids, cold meds"),
                ("Influenza","A contagious flu virus that affects breathing.","Fever, chills, muscle ache","Antivirals, rest, fluids"),
                ("Diabetes","A condition where blood sugar levels stay too high.","Thirst, tiredness, urination","Diet, insulin, exercise"),
                ("Hypertension","A long-term condition of high blood pressure.","Headache, dizzy, blurry vision","Meds, less salt, exercise"),
                ("Asthma","Chronic lung condition with inflamed airways.","Wheezing, breathlessness, chest tightness","Inhalers & steroids"),
                ("COVID-19","Contagious respiratory illness by SARS-CoV-2.","Fever, cough, breathing issues","Supportive care & antivirals"),
                ("Chronic Kidney Disease","Gradual loss of kidney function.","Fatigue, swelling, urine changes","Medications & dialysis if needed"),
                ("Obesity","Excess body fat raising health risks.","Fatigue, joint pain","Diet, exercise, sometimes surgery"),
                ("Osteoarthritis","Joint degeneration with pain & stiffness.","Pain, stiffness, reduced movement","Analgesics & therapy"),
                ("Lung Cancer","Malignant tumor in the lungs.","Chronic cough, chest pain","Surgery, chemo, radiation"),
                ("HIV/AIDS","Viral infection impairing immunity.","Frequent infections, weight loss, fatigue","Antiretroviral therapy"),
                ("Hepatitis C","Viral liver infection damaging the liver.","Fatigue, joint pain, jaundice","Direct antivirals"),
                ("Food Poisoning","Illness from contaminated food or water.","Nausea, vomiting, diarrhea","Hydration & antibiotics if needed"),
                ("Dengue Fever","Mosquito-borne virus with high fever.","High fever, headache, muscle pain","Supportive care & hydration"),
                ("Meningitis","Inflammation of brain and spinal membranes.","Headache, neck stiffness, fever","Antibiotics/antivirals"),
                ("Ulcerative Colitis","Chronic inflammation of the colon.","Diarrhea, abdominal pain, bleeding","Anti-inflammatories, surgery if needed"),
                ("Crohn's Disease","Chronic inflammation of the GI tract.","Abdominal pain, diarrhea, weight loss","Anti-inflammatory and immunosuppressants"),
                ("Epilepsy","Neurological disorder with recurrent seizures.","Seizures, confusion, loss of consciousness","Antiepileptic drugs"),
                ("Migraine","Recurrent severe headache disorder.","Pulsing head pain, nausea","Analgesics & migraine-specific meds"),
                ("Psoriasis","Chronic autoimmune skin disorder.","Red, scaly patches, itchiness","Topicals, phototherapy, systemic treatments"),
                ("Depression","Mood disorder with persistent sadness.","Low mood, fatigue, sleep changes","Psychotherapy & antidepressants"),
                ("Anxiety Disorder","Excessive and persistent worry.","Nervousness, rapid heartbeat","Therapy, medication, relaxation techniques"),
                ("Bipolar Disorder","Mood swings between depression and mania.","Depressive and manic episodes","Mood stabilizers & therapy"),
                ("Schizophrenia","Severe mental disorder with delusions.","Hallucinations, disorganized thoughts","Antipsychotics & support therapy"),
                ("Hyperlipidemia","High blood lipid levels.","Usually asymptomatic","Diet, exercise, lipid-lowering drugs"),
                ("Gout","Arthritis from uric acid crystals.","Sudden joint pain & swelling","Anti-inflammatories & uric acid reducers"),
                ("Kidney Stones","Mineral deposits in the kidneys.","Sharp flank pain, blood in urine","Hydration, analgesics, surgery"),
                ("GERD","Acid reflux disorder.","Heartburn, acid regurgitation","Lifestyle changes & antacids"),
                ("Urinary Tract Infection","Infection of the urinary system.","Painful, frequent urination","Antibiotics"),
                ("Appendicitis","Inflamed appendix needing surgery.","Severe abdominal pain, nausea","Surgery & antibiotics"),
                ("Inflammatory Bowel Disease","Chronic GI inflammation.","Abdominal pain, diarrhea, weight loss","Anti-inflammatories & immunosuppressants"),
                ("Multiple Sclerosis","Autoimmune disorder affecting CNS.","Muscle weakness, balance issues","Disease modifying drugs"),
                ("Parkinson's Disease","Neurodegenerative movement disorder.","Tremors, rigidity, slow movement","Dopaminergic meds & therapy"),
                ("Rheumatoid Arthritis","Chronic autoimmune joint inflammation.","Joint pain, stiffness, swelling","DMARDs & physical therapy")
            ]

            cursor.executemany(
                "INSERT INTO disease_database (disease_name, short_description, symptoms, treatments) VALUES (%s,%s,%s,%s)",
                diseases
            )
            db_conn.commit()

        return db_conn

    except Exception as e:
        print("Database Initialization Error:", e)
        return None


def extract_symptoms():
    mydb = initialize_database(password1)
    if mydb is None:
        print("Failed to connect to the database!!!")
        return []
    else:
        cursor = mydb.cursor()
        cursor.execute("select * from disease_database")
        data = cursor.fetchall()
        symptoms = []
        for row in data:
            if len(row) > 3 and isinstance(row[3], str):
                symptom_str = row[3].replace(".", "").lower()
                symptoms += [s.strip() for s in symptom_str.split(",")]
        symptoms = list(set(symptoms))
        symptoms.sort()
        return symptoms


def input_symptoms(symptoms):
    selected = []

    def on_submit():
        for i, var in enumerate(vars_):
            if var.get():
                selected.append(symptoms[i])
        root.destroy()

    root = tk.Tk()
    root.title("Symptom Selector")
    root.geometry("400x500")
    root.configure(bg="#2E2E2E")

    # --- Style Configuration ---
    style = ttk.Style()
    style.theme_use('clam')

    # General widget styles
    style.configure("TFrame", background="#2E2E2E")
    style.configure("TLabel", background="#2E2E2E", foreground="white", font=('Segoe UI', 14, 'bold'))
    style.configure("TScrollbar", background="#2E2E2E", troughcolor="#3C3C3C")

    # Checkbutton style
    style.configure("TCheckbutton",
                    background="#3C3C3C",
                    foreground="white",
                    font=('Segoe UI', 10),
                    indicatorrelief=tk.FLAT,
                    indicatormargin=5)
    style.map("TCheckbutton",
              background=[('active', '#4A4A4A')],
              indicatorcolor=[("selected", "#007ACC"), ("!selected", "white")],
              foreground=[('active', 'white')])

    # Button style
    style.configure("TButton",
                    background="#007ACC",
                    foreground="white",
                    font=('Segoe UI', 11, 'bold'),
                    borderwidth=0)
    style.map("TButton", background=[('active', '#005f9e')])


    # --- UI Layout ---
    title_label = ttk.Label(root, text="Select Your Symptoms")
    title_label.pack(pady=(15, 10))

    frame = ttk.Frame(root, padding="10")
    frame.pack(fill=tk.BOTH, expand=True)

    canvas = tk.Canvas(frame, bg="#3C3C3C", highlightthickness=0)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style="TFrame")
    scrollable_frame.configure(style="TFrame") # Apply style to inner frame

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    vars_ = []
    for symptom in symptoms:
        var = tk.BooleanVar()
        chk = ttk.Checkbutton(scrollable_frame, text=symptom, variable=var)
        chk.pack(anchor='w', padx=10, pady=5, fill='x')
        vars_.append(var)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    submit_btn = ttk.Button(root, text="Submit", command=on_submit, style="TButton")
    submit_btn.pack(pady=15, padx=20, ipadx=10, ipady=5)

    root.mainloop()
    return selected
def disease_prediction(selected_symptoms):
    mydb = initialize_database(password1)
    if mydb is None:
        print("Failed to connect to the database!!!")
        return []

    cursor = mydb.cursor()
    cursor.execute("select * from disease_database")
    data = cursor.fetchall()

    results = []
    full_matches = []

    for row in data:
        if len(row) > 3 and isinstance(row[3], str):
            disease_symptoms = [s.strip().lower() for s in row[3].replace(".", "").split(",")]
            matches = len(set(selected_symptoms).intersection(disease_symptoms))
            total = len(disease_symptoms)
            if matches > 0 and total > 0:
                percentage = round((matches / total) * 100, 2)
                tup = (row[1], percentage)
                results.append(tup)
                # Check if all selected symptoms are present in this disease
                all_present = True
                for sym in selected_symptoms:
                    if sym.lower() not in disease_symptoms:
                        all_present = False
                        break
                if all_present:
                    full_matches.append(tup)

    # Sort results by percentage descending (without lambda)
    def sort_by_percentage(data_list):
        for i in range(len(data_list)):
            for j in range(i + 1, len(data_list)):
                if data_list[j][1] > data_list[i][1]:
                    data_list[i], data_list[j] = data_list[j], data_list[i]
        return data_list

    if full_matches:
        return sort_by_percentage(full_matches)
    else:
        return sort_by_percentage(results)


def show_predictions(name, age, predictions, selected_symptoms):
    if not predictions:
        messagebox.showinfo("No Results", "No matching diseases found.")
        return

    # -------- FETCH EXTRA DETAILS FROM DATABASE --------
    mydb = initialize_database(password1)
    cursor = mydb.cursor()

    detailed_results = []

    for disease, percentage in predictions:
        cursor.execute(
            "SELECT short_description, symptoms, treatments FROM disease_database WHERE disease_name = %s",
            (disease,)
        )
        row = cursor.fetchone()
        if row:
            short_desc, symptoms, treatments = row
            detailed_results.append(
                (disease, percentage, short_desc, symptoms, treatments)
            )

    cursor.close()
    mydb.close()

    # -------- SAVE REPORT AS TEXT FILE --------
    report_name = f"{name.replace(' ', '_')}_medical_report.txt"

    with open(report_name, "w", encoding="utf-8") as file:
        file.write("===== DISEASE PREDICTION MEDICAL REPORT =====\n\n")
        file.write(f"Patient Name : {name}\n")
        file.write(f"Age          : {age}\n\n")

        file.write("Selected Symptoms:\n")
        for s in selected_symptoms:
            file.write(f"- {s}\n")

        file.write("\n--------------------------------------------\n\n")

        for disease, percentage, desc, symp, treat in detailed_results:
            file.write(f"Disease Name        : {disease}\n")
            file.write(f"Match Percentage    : {percentage}%\n")
            file.write(f"Short Description   : {desc}\n")
            file.write(f"Common Symptoms     : {symp}\n")
            file.write(f"Possible Treatment  : {treat}\n")
            file.write("\n--------------------------------------------\n\n")

        file.write("NOTE: This is an AI-generated report. Consult a doctor for confirmation.\n")

    # -------- SHOW GUI RESULT --------
    window = tk.Tk()
    window.title(f"Disease Predictions for {name} (Age: {age})")
    window.geometry("800x450")
    window.configure(bg="#e6f2ff")

    title = ttk.Label(
        window,
        text=f"Disease Predictions for {name} (Age: {age})",
        font=('Segoe UI', 14, 'bold'),
        background="#e6f2ff"
    )
    title.pack(pady=10)

    columns = ("Disease", "Match %", "Treatment")
    tree = ttk.Treeview(window, columns=columns, show="headings", height=12)

    tree.heading("Disease", text="Disease")
    tree.heading("Match %", text="Match %")
    tree.heading("Treatment", text="Possible Treatment")

    tree.column("Disease", width=200)
    tree.column("Match %", width=100, anchor="center")
    tree.column("Treatment", width=450)

    for disease, percentage, _, _, treatment in detailed_results:
        tree.insert("", tk.END, values=(disease, f"{percentage}%", treatment))

    tree.pack(padx=10, pady=10, fill="both", expand=True)

    messagebox.showinfo(
        "Report Generated",
        f"Medical report saved successfully as:\n{report_name}"
    )

    window.mainloop()



    
def add_new_disease():
    mydb = initialize_database(password1)
    if mydb is None:
        print("Failed to connect to the database!!!")
        return

    cursor = mydb.cursor()

    try:
        # Ask user for each column except id (auto-increment)
        disease_name = input("Enter disease name: ").strip()
        short_description = input("Enter short description: ").strip()
        symptoms = input("Enter symptoms (comma separated): ").strip()
        treatments = input("Enter treatments (comma separated or text): ").strip()

        sql = """
        INSERT INTO disease_database (disease_name, short_description, symptoms, treatments)
        VALUES (%s, %s, %s, %s)
        """
        values = (disease_name, short_description, symptoms, treatments)
        cursor.execute(sql, values)
        mydb.commit()
        print("Disease added successfully!")

    except Exception as e:
        print("Error while adding disease:", e)
    finally:
        cursor.close()
        mydb.close()




def show_database_table():
    mydb = initialize_database(password1)
    if mydb is None:
        messagebox.showerror("Database Error", "Failed to connect to the database!")
        return

    cursor = mydb.cursor()
    cursor.execute("SELECT id, disease_name, short_description, symptoms, treatments FROM disease_database")
    data = cursor.fetchall()
    columns = ["ID", "Disease Name", "Description", "Symptoms", "Treatments"]

    # Create main window
    root = tk.Tk()
    root.title("Disease Database Table")
    root.geometry("900x500")
    root.configure(bg="#e6f2ff")  # Light blue background

    # Simple color style for Treeview
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview", background="#f9fbfd", foreground="black", rowheight=25, fieldbackground="#f9fbfd")
    style.configure("Treeview.Heading", background="#3399ff", foreground="white", font=('Arial', 10, 'bold'))
    style.map('Treeview', background=[('selected', '#b3d1ff')])

    # Add striped row tags for grid effect
    tree = ttk.Treeview(root, columns=columns, show="headings", style="Treeview")
    tree.tag_configure('oddrow', background='#f9fbfd')
    tree.tag_configure('evenrow', background='#e0ecff')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)
    for idx, row in enumerate(data):
        tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
        tree.insert("", tk.END, values=row, tags=(tag,))

    # Add scrollbars
    vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    root.mainloop()

def delete_disease_by_name_and_id():
    mydb = initialize_database(password1)
    if mydb is None:
        print("Failed to connect to the database!")
        return

    cursor = mydb.cursor()
    try:
        disease_id = input("Enter the Disease ID to delete: ").strip()
        disease_name = input("Enter the Disease Name to delete: ").strip()

        # Check if the disease exists
        cursor.execute(
            "SELECT * FROM disease_database WHERE id = %s AND disease_name = %s",
            (disease_id, disease_name)
        )
        result = cursor.fetchone()
        if not result:
            print("No disease found with the given ID and Name.")
            return

        # Delete the disease
        cursor.execute(
            "DELETE FROM disease_database WHERE id = %s AND disease_name = %s",
            (disease_id, disease_name)
        )
        mydb.commit()
        print("Disease deleted successfully!")

    except Exception as e:
        print("Error while deleting disease:", e)
    finally:
        cursor.close()
        mydb.close()


print("Welcome to the Disease Prediction System ")
print("HELLO SIR , Please select any one option from below \n 1. Predict Disease \n 2. Add New Disease \n 3. Show Database Table \n 4. Delete Disease from Database")
Choice = input("Enter your choice (1-4): ")
password1 = input("Enter Admin Password to proceed: ")
if Choice == '1':
    paitent_name = input("Enter Patient Name: ")
    age = input("Enter Patient Age: ")
    try :
        symptoms = extract_symptoms()
        selected_symptoms = input_symptoms(symptoms)
        disease_predictions = disease_prediction(selected_symptoms)
        if disease_predictions:
            show_predictions(paitent_name, age, disease_predictions, selected_symptoms)

        else:
            messagebox.showinfo("No Match", "No matching diseases found.")
    except Exception as e:
        print("An error occurred during disease prediction:", e)
elif Choice == '2':
    add_new_disease()
elif Choice == '3':
    show_database_table()
elif Choice == '4':
    delete_disease_by_name_and_id()
else:
    print("Invalid choice! Please select a valid option (1-4).")
