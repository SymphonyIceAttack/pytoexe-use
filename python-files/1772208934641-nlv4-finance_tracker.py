import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

class ExpenseTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("900x700")
        
        # Data storage
        self.data_file = Path.home() / "finance_tracker_data.json"
        self.load_data()
        
        # Common expense suggestions
        self.expense_suggestions = [
            "Groceries", "Restaurant", "Transportation", "Gas", 
            "Utilities", "Rent", "Entertainment", "Shopping",
            "Healthcare", "Education", "Insurance", "Coffee",
            "Phone Bill", "Internet", "Gym", "Subscriptions"
        ]
        
        # Income source suggestions
        self.income_suggestions = [
            "Salary", "Freelance", "Investment", "Bonus",
            "Gift", "Side Business", "Rental Income", "Dividends"
        ]
        
        self.setup_ui()
        self.update_display()
    
    def load_data(self):
        """Load data from JSON file"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = self.get_default_data()
        else:
            self.data = self.get_default_data()
    
    def get_default_data(self):
        """Return default data structure"""
        return {
            "expenses": [],
            "income": []
        }
    
    def save_data(self):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create tabs
        self.expense_frame = ttk.Frame(self.notebook)
        self.income_frame = ttk.Frame(self.notebook)
        self.summary_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.expense_frame, text="Daily Expenses")
        self.notebook.add(self.income_frame, text="Bi-Weekly Income")
        self.notebook.add(self.summary_frame, text="Monthly Summary")
        
        self.setup_expense_tab()
        self.setup_income_tab()
        self.setup_summary_tab()
    
    def setup_expense_tab(self):
        """Setup the daily expenses tab"""
        # Input frame
        input_frame = ttk.LabelFrame(self.expense_frame, text="Add New Expense", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # Amount
        ttk.Label(input_frame, text="Amount ($):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.expense_amount = ttk.Entry(input_frame, width=20)
        self.expense_amount.grid(row=0, column=1, padx=5, pady=5)
        
        # Expense name with suggestions
        ttk.Label(input_frame, text="Expense Name:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        name_frame = ttk.Frame(input_frame)
        name_frame.grid(row=1, column=1, padx=5, pady=5)
        
        self.expense_name = ttk.Combobox(name_frame, values=self.expense_suggestions, width=17)
        self.expense_name.pack(side='left')
        self.expense_name.bind('<KeyRelease>', self.update_expense_suggestions)
        
        # Date
        ttk.Label(input_frame, text="Date:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.expense_date = ttk.Entry(input_frame, width=20)
        self.expense_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.expense_date.grid(row=2, column=1, padx=5, pady=5)
        
        # Add button
        ttk.Button(input_frame, text="Add Expense", command=self.add_expense).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Today's expenses frame
        today_frame = ttk.LabelFrame(self.expense_frame, text="Today's Expenses", padding=10)
        today_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview for today's expenses
        columns = ('Time', 'Name', 'Amount')
        self.today_tree = ttk.Treeview(today_frame, columns=columns, show='headings', height=8)
        
        self.today_tree.heading('Time', text='Time')
        self.today_tree.heading('Name', text='Expense Name')
        self.today_tree.heading('Amount', text='Amount ($)')
        
        self.today_tree.column('Time', width=100)
        self.today_tree.column('Name', width=200)
        self.today_tree.column('Amount', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(today_frame, orient='vertical', command=self.today_tree.yview)
        self.today_tree.configure(yscrollcommand=scrollbar.set)
        
        self.today_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Daily total
        self.today_total_label = ttk.Label(today_frame, text="Today's Total: $0.00", font=('Arial', 12, 'bold'))
        self.today_total_label.pack(pady=10)
    
    def setup_income_tab(self):
        """Setup the bi-weekly income tab"""
        # Input frame
        input_frame = ttk.LabelFrame(self.income_frame, text="Add New Income", padding=10)
        input_frame.pack(fill='x', padx=10, pady=10)
        
        # Amount
        ttk.Label(input_frame, text="Amount ($):").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.income_amount = ttk.Entry(input_frame, width=20)
        self.income_amount.grid(row=0, column=1, padx=5, pady=5)
        
        # Income source with suggestions
        ttk.Label(input_frame, text="Source:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        
        source_frame = ttk.Frame(input_frame)
        source_frame.grid(row=1, column=1, padx=5, pady=5)
        
        self.income_source = ttk.Combobox(source_frame, values=self.income_suggestions, width=17)
        self.income_source.pack(side='left')
        self.income_source.bind('<KeyRelease>', self.update_income_suggestions)
        
        # Period selection
        ttk.Label(input_frame, text="Period:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        period_frame = ttk.Frame(input_frame)
        period_frame.grid(row=2, column=1, padx=5, pady=5)
        
        self.income_period = ttk.Combobox(period_frame, values=['First Half', 'Second Half'], width=17)
        self.income_period.set('First Half')
        self.income_period.pack(side='left')
        
        # Date
        ttk.Label(input_frame, text="Date:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.income_date = ttk.Entry(input_frame, width=20)
        self.income_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.income_date.grid(row=3, column=1, padx=5, pady=5)
        
        # Add button
        ttk.Button(input_frame, text="Add Income", command=self.add_income).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Recent income frame
        recent_frame = ttk.LabelFrame(self.income_frame, text="Recent Income Entries", padding=10)
        recent_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Treeview for recent income
        columns = ('Date', 'Period', 'Source', 'Amount')
        self.income_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        self.income_tree.heading('Date', text='Date')
        self.income_tree.heading('Period', text='Period')
        self.income_tree.heading('Source', text='Source')
        self.income_tree.heading('Amount', text='Amount ($)')
        
        self.income_tree.column('Date', width=100)
        self.income_tree.column('Period', width=100)
        self.income_tree.column('Source', width=200)
        self.income_tree.column('Amount', width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(recent_frame, orient='vertical', command=self.income_tree.yview)
        self.income_tree.configure(yscrollcommand=scrollbar.set)
        
        self.income_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def setup_summary_tab(self):
        """Setup the monthly summary tab"""
        # Controls frame
        controls_frame = ttk.Frame(self.summary_frame)
        controls_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(controls_frame, text="Select Month:").pack(side='left', padx=5)
        
        # Month selection
        current_date = datetime.now()
        months = []
        for i in range(12):
            date = current_date - timedelta(days=30*i)
            months.append(date.strftime("%Y-%m"))
        
        self.month_var = tk.StringVar(value=current_date.strftime("%Y-%m"))
        month_menu = ttk.Combobox(controls_frame, textvariable=self.month_var, values=months, width=10)
        month_menu.pack(side='left', padx=5)
        month_menu.bind('<<ComboboxSelected>>', lambda e: self.update_summary())
        
        ttk.Button(controls_frame, text="Refresh", command=self.update_summary).pack(side='left', padx=5)
        
        # Summary frame
        summary_display = ttk.LabelFrame(self.summary_frame, text="Monthly Summary", padding=10)
        summary_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Summary text
        self.summary_text = tk.Text(summary_display, height=20, width=60, font=('Courier', 10))
        self.summary_text.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(summary_display, orient='vertical', command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
    
    def update_expense_suggestions(self, event):
        """Update expense suggestions based on user input"""
        typed = self.expense_name.get().lower()
        if typed:
            matches = [s for s in self.expense_suggestions if typed in s.lower()]
            self.expense_name['values'] = matches if matches else self.expense_suggestions
    
    def update_income_suggestions(self, event):
        """Update income suggestions based on user input"""
        typed = self.income_source.get().lower()
        if typed:
            matches = [s for s in self.income_suggestions if typed in s.lower()]
            self.income_source['values'] = matches if matches else self.income_suggestions
    
    def add_expense(self):
        """Add a new expense"""
        try:
            amount = float(self.expense_amount.get())
            name = self.expense_name.get().strip()
            date_str = self.expense_date.get().strip()
            
            if not name:
                messagebox.showerror("Error", "Please enter an expense name")
                return
            
            # Validate date
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
            
            expense = {
                "amount": amount,
                "name": name,
                "date": date_str,
                "timestamp": datetime.now().isoformat()
            }
            
            self.data["expenses"].append(expense)
            self.save_data()
            
            # Clear inputs
            self.expense_amount.delete(0, tk.END)
            self.expense_name.delete(0, tk.END)
            
            self.update_display()
            messagebox.showinfo("Success", "Expense added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def add_income(self):
        """Add a new income entry"""
        try:
            amount = float(self.income_amount.get())
            source = self.income_source.get().strip()
            period = self.income_period.get()
            date_str = self.income_date.get().strip()
            
            if not source:
                messagebox.showerror("Error", "Please enter an income source")
                return
            
            # Validate date
            try:
                income_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD")
                return
            
            income = {
                "amount": amount,
                "source": source,
                "period": period,
                "date": date_str,
                "timestamp": datetime.now().isoformat()
            }
            
            self.data["income"].append(income)
            self.save_data()
            
            # Clear inputs
            self.income_amount.delete(0, tk.END)
            self.income_source.delete(0, tk.END)
            
            self.update_display()
            messagebox.showinfo("Success", "Income added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
    
    def update_display(self):
        """Update all displays"""
        self.update_today_expenses()
        self.update_income_display()
        self.update_summary()
    
    def update_today_expenses(self):
        """Update today's expenses display"""
        # Clear current items
        for item in self.today_tree.get_children():
            self.today_tree.delete(item)
        
        today = datetime.now().strftime("%Y-%m-%d")
        total = 0
        
        # Add today's expenses
        for expense in self.data["expenses"]:
            if expense["date"] == today:
                time_str = datetime.fromisoformat(expense["timestamp"]).strftime("%H:%M")
                self.today_tree.insert('', 'end', values=(
                    time_str,
                    expense["name"],
                    f"${expense['amount']:.2f}"
                ))
                total += expense["amount"]
        
        self.today_total_label.config(text=f"Today's Total: ${total:.2f}")
    
    def update_income_display(self):
        """Update income display"""
        # Clear current items
        for item in self.income_tree.get_children():
            self.income_tree.delete(item)
        
        # Show last 20 income entries
        for income in sorted(self.data["income"], key=lambda x: x["date"], reverse=True)[:20]:
            self.income_tree.insert('', 0, values=(
                income["date"],
                income["period"],
                income["source"],
                f"${income['amount']:.2f}"
            ))
    
    def update_summary(self):
        """Update monthly summary"""
        selected_month = self.month_var.get()
        
        # Clear summary text
        self.summary_text.delete(1.0, tk.END)
        
        # Filter expenses and income for selected month
        monthly_expenses = []
        monthly_income = []
        
        for expense in self.data["expenses"]:
            if expense["date"][:7] == selected_month:
                monthly_expenses.append(expense)
        
        for income in self.data["income"]:
            if income["date"][:7] == selected_month:
                monthly_income.append(income)
        
        # Calculate totals
        total_expenses = sum(e["amount"] for e in monthly_expenses)
        total_income = sum(i["amount"] for i in monthly_income)
        net_savings = total_income - total_expenses
        
        # Display summary
        summary = f"Monthly Summary for {selected_month}\n"
        summary += "="*50 + "\n\n"
        
        summary += "INCOME:\n"
        summary += "-"*30 + "\n"
        if monthly_income:
            for income in monthly_income:
                summary += f"{income['date']} - {income['source']} ({income['period']}): ${income['amount']:.2f}\n"
        else:
            summary += "No income recorded for this month\n"
        summary += f"\nTotal Income: ${total_income:.2f}\n\n"
        
        summary += "EXPENSES:\n"
        summary += "-"*30 + "\n"
        if monthly_expenses:
            # Group expenses by category
            expenses_by_category = {}
            for expense in monthly_expenses:
                if expense["name"] not in expenses_by_category:
                    expenses_by_category[expense["name"]] = 0
                expenses_by_category[expense["name"]] += expense["amount"]
            
            for category, amount in sorted(expenses_by_category.items(), key=lambda x: x[1], reverse=True):
                summary += f"{category}: ${amount:.2f}\n"
            
            summary += "\nDaily Breakdown:\n"
            for expense in sorted(monthly_expenses, key=lambda x: x["date"]):
                summary += f"{expense['date']} - {expense['name']}: ${expense['amount']:.2f}\n"
        else:
            summary += "No expenses recorded for this month\n"
        summary += f"\nTotal Expenses: ${total_expenses:.2f}\n\n"
        
        summary += "="*50 + "\n"
        summary += f"NET SAVINGS: ${net_savings:.2f}\n"
        if net_savings > 0:
            summary += f"Savings Rate: {(net_savings/total_income*100):.1f}%\n"
        
        self.summary_text.insert(1.0, summary)

def main():
    root = tk.Tk()
    app = ExpenseTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()