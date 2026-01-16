"""
Приложение для управления продажами в магазинах с графическим интерфейсом
Требуемые библиотеки: pyodbc, pandas, tkinter, matplotlib
Установка: pip install pyodbc pandas matplotlib seaborn
"""

import pyodbc
import pandas as pd
from datetime import datetime, date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
import os
import sys
import threading

# Настройка стиля seaborn для графиков
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

class SalesManagementSystem:
    def get_employees_data(self):
        """Получение данных о сотрудниках с JOIN"""
        query = """
        SELECT 
            e.EmployeeID,
            s.ShopName,
            e.FirstName,
            e.LastName,
            e.Position,
            e.Phone,
            e.Email,
            e.HireDate,
            e.Salary,
            CASE WHEN e.IsActive = 1 THEN 'Да' ELSE 'Нет' END as IsActive
        FROM Employees e
        INNER JOIN Shops s ON e.ShopID = s.ShopID
        ORDER BY s.ShopName, e.LastName, e.FirstName
        """

        return self.execute_query(query)

    def add_employee(self, shop_id, first_name, last_name, position, phone, email, salary):
        """Добавление нового сотрудника"""
        try:
            query = """
            INSERT INTO Employees (ShopID, FirstName, LastName, Position, 
                   Phone, Email, Salary, HireDate, IsActive)
            VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE(), 1)
            """

            self.cursor.execute(query, (shop_id, first_name, last_name, position,
                                        phone, email, salary))
            self.connection.commit()
            return True, "Сотрудник успешно добавлен!"
        except Exception as e:
            return False, f"Ошибка при добавлении сотрудника: {e}"

    def update_employee(self, employee_id, shop_id, first_name, last_name,
                        position, phone, email, salary, is_active):
        """Обновление данных сотрудника"""
        try:
            query = """
            UPDATE Employees 
            SET ShopID = ?, FirstName = ?, LastName = ?, Position = ?, 
                Phone = ?, Email = ?, Salary = ?, IsActive = ?
            WHERE EmployeeID = ?
            """

            self.cursor.execute(query, (shop_id, first_name, last_name, position,
                                        phone, email, salary, is_active, employee_id))
            self.connection.commit()
            return True, "Данные сотрудника обновлены!"
        except Exception as e:
            return False, f"Ошибка при обновлении сотрудника: {e}"

    def delete_employee(self, employee_id):
        """Удаление сотрудника"""
        try:
            # Проверяем, есть ли у сотрудника продажи
            check_query = "SELECT COUNT(*) FROM Sales WHERE EmployeeID = ?"
            self.cursor.execute(check_query, (employee_id,))
            sales_count = self.cursor.fetchone()[0]

            if sales_count > 0:
                return False, "Нельзя удалить сотрудника, у которого есть продажи!"

            query = "DELETE FROM Employees WHERE EmployeeID = ?"
            self.cursor.execute(query, (employee_id,))
            self.connection.commit()

            if self.cursor.rowcount > 0:
                return True, "Сотрудник успешно удален!"
            else:
                return False, "Сотрудник не найден!"
        except Exception as e:
            return False, f"Ошибка при удалении сотрудника: {e}"
    def get_inventory_data(self):
        """Получение данных об инвентаре с JOIN"""
        query = """
        SELECT 
            i.InventoryID,
            s.ShopName,
            p.ProductName,
            pc.CategoryName,
            i.Quantity,
            i.MinStockLevel,
            i.LastRestockDate,
            CASE 
                WHEN i.Quantity <= i.MinStockLevel THEN 'Низкий запас'
                WHEN i.Quantity <= i.MinStockLevel * 1.5 THEN 'Заканчивается'
                ELSE 'В норме'
            END as StockStatus
        FROM Inventory i
        INNER JOIN Shops s ON i.ShopID = s.ShopID
        INNER JOIN Products p ON i.ProductID = p.ProductID
        LEFT JOIN ProductCategories pc ON p.CategoryID = pc.CategoryID
        ORDER BY s.ShopName, p.ProductName
        """

        return self.execute_query(query)

    def get_all_products(self):
        """Получение всех товаров"""
        query = """
        SELECT 
            p.ProductID,
            p.ProductName,
            pc.CategoryName,
            p.UnitPrice
        FROM Products p
        LEFT JOIN ProductCategories pc ON p.CategoryID = pc.CategoryID
        ORDER BY p.ProductName
        """

        return self.execute_query(query)

    def restock_product(self, inventory_id, quantity_to_add, restock_date=None):
        """Пополнение запасов товара"""
        if restock_date is None:
            restock_date = date.today()

        try:
            query = """
            UPDATE Inventory 
            SET Quantity = Quantity + ?, 
                LastRestockDate = ?
            WHERE InventoryID = ?
            """

            self.cursor.execute(query, (quantity_to_add, restock_date, inventory_id))
            self.connection.commit()
            return True, "Запасы успешно пополнены!"
        except Exception as e:
            return False, f"Ошибка при пополнении запасов: {e}"

    def restock_product_by_shop_product(self, shop_id, product_id, quantity_to_add, restock_date=None):
        """Пополнение запасов товара в конкретном магазине"""
        if restock_date is None:
            restock_date = date.today()

        try:
            # Проверяем, существует ли запись в Inventory
            check_query = """
            SELECT COUNT(*) FROM Inventory 
            WHERE ShopID = ? AND ProductID = ?
            """

            self.cursor.execute(check_query, (shop_id, product_id))
            exists = self.cursor.fetchone()[0]

            if exists == 0:
                # Если записи нет, создаем новую
                insert_query = """
                INSERT INTO Inventory (ShopID, ProductID, Quantity, MinStockLevel, LastRestockDate)
                VALUES (?, ?, ?, 10, ?)
                """
                self.cursor.execute(insert_query, (shop_id, product_id, quantity_to_add, restock_date))
            else:
                # Если запись есть, обновляем количество
                update_query = """
                UPDATE Inventory 
                SET Quantity = Quantity + ?, 
                    LastRestockDate = ?
                WHERE ShopID = ? AND ProductID = ?
                """
                self.cursor.execute(update_query, (quantity_to_add, restock_date, shop_id, product_id))

            self.connection.commit()
            return True, "Запасы успешно пополнены!"
        except Exception as e:
            return False, f"Ошибка при пополнении запасов: {e}"

    def update_min_stock_level(self, inventory_id, new_min_level):
        """Обновление минимального уровня запасов"""
        try:
            query = """
            UPDATE Inventory 
            SET MinStockLevel = ?
            WHERE InventoryID = ?
            """

            self.cursor.execute(query, (new_min_level, inventory_id))
            self.connection.commit()
            return True, "Минимальный уровень запасов обновлен!"
        except Exception as e:
            return False, f"Ошибка при обновлении минимального уровня: {e}"
    def check_product_stock(self, shop_id, product_id):
        """Проверка наличия товара на складе магазина"""
        query = "SELECT Quantity FROM Inventory WHERE ShopID = ? AND ProductID = ?"
        success, result, _ = self.execute_query(query, [shop_id, product_id])

        if success and result and result[0][0] is not None:
            return True, result[0][0]
        return False, 0
    def __init__(self, server='KRLAP', database='SalesManagement'):
        self.server = server
        self.database = database
        self.connection = None
        self.cursor = None

        self.connection_string = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={server};'
            f'DATABASE={database};'
            f'Trusted_Connection=yes;'
        )

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            self.cursor = self.connection.cursor()
            return True, "Успешное подключение к базе данных!"
        except pyodbc.Error as e:
            return False, f"Ошибка подключения: {e}"

    def create_database(self):
        try:
            master_conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={self.server};'
                f'Trusted_Connection=yes;'
            )
            master_cursor = master_conn.cursor()

            master_cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}')
                BEGIN
                    CREATE DATABASE [{self.database}];
                    PRINT 'База данных создана успешно.';
                END
            """)
            master_conn.commit()
            master_conn.close()

            return self.connect()
        except Exception as e:
            return False, f"Ошибка создания базы данных: {e}"

    def create_tables(self):
        tables = {
            'Shops': """
                CREATE TABLE Shops (
                    ShopID INT PRIMARY KEY IDENTITY(1,1),
                    ShopName NVARCHAR(100) NOT NULL,
                    Address NVARCHAR(200),
                    Phone NVARCHAR(20),
                    Email NVARCHAR(100),
                    OpeningDate DATE DEFAULT GETDATE(),
                    IsActive BIT DEFAULT 1
                );
            """,

            'Employees': """
                CREATE TABLE Employees (
                    EmployeeID INT PRIMARY KEY IDENTITY(1,1),
                    ShopID INT FOREIGN KEY REFERENCES Shops(ShopID),
                    FirstName NVARCHAR(50) NOT NULL,
                    LastName NVARCHAR(50) NOT NULL,
                    Position NVARCHAR(50),
                    Phone NVARCHAR(20),
                    Email NVARCHAR(100),
                    HireDate DATE DEFAULT GETDATE(),
                    Salary DECIMAL(10,2),
                    IsActive BIT DEFAULT 1
                );
            """,

            'ProductCategories': """
                CREATE TABLE ProductCategories (
                    CategoryID INT PRIMARY KEY IDENTITY(1,1),
                    CategoryName NVARCHAR(100) NOT NULL,
                    Description NVARCHAR(500)
                );
            """,

            'Suppliers': """
                CREATE TABLE Suppliers (
                    SupplierID INT PRIMARY KEY IDENTITY(1,1),
                    CompanyName NVARCHAR(100) NOT NULL,
                    ContactPerson NVARCHAR(100),
                    Phone NVARCHAR(20),
                    Email NVARCHAR(100),
                    Address NVARCHAR(200)
                );
            """,

            'Products': """
                CREATE TABLE Products (
                    ProductID INT PRIMARY KEY IDENTITY(1,1),
                    ProductName NVARCHAR(100) NOT NULL,
                    CategoryID INT FOREIGN KEY REFERENCES ProductCategories(CategoryID),
                    SupplierID INT FOREIGN KEY REFERENCES Suppliers(SupplierID),
                    UnitPrice DECIMAL(10,2) NOT NULL,
                    PurchasePrice DECIMAL(10,2),
                    Barcode NVARCHAR(50),
                    Description NVARCHAR(500),
                    CreatedDate DATETIME DEFAULT GETDATE()
                );
            """,

            'Inventory': """
                CREATE TABLE Inventory (
                    InventoryID INT PRIMARY KEY IDENTITY(1,1),
                    ShopID INT FOREIGN KEY REFERENCES Shops(ShopID),
                    ProductID INT FOREIGN KEY REFERENCES Products(ProductID),
                    Quantity INT NOT NULL DEFAULT 0,
                    MinStockLevel INT DEFAULT 10,
                    LastRestockDate DATE,
                    CONSTRAINT UC_ShopProduct UNIQUE (ShopID, ProductID)
                );
            """,

            'Customers': """
                CREATE TABLE Customers (
                    CustomerID INT PRIMARY KEY IDENTITY(1,1),
                    FirstName NVARCHAR(50) NOT NULL,
                    LastName NVARCHAR(50) NOT NULL,
                    Phone NVARCHAR(20),
                    Email NVARCHAR(100),
                    RegistrationDate DATE DEFAULT GETDATE(),
                    IsActive BIT DEFAULT 1
                );
            """,

            'Sales': """
                CREATE TABLE Sales (
                    SaleID INT PRIMARY KEY IDENTITY(1,1),
                    ShopID INT FOREIGN KEY REFERENCES Shops(ShopID),
                    EmployeeID INT FOREIGN KEY REFERENCES Employees(EmployeeID),
                    CustomerID INT NULL FOREIGN KEY REFERENCES Customers(CustomerID),
                    SaleDate DATETIME DEFAULT GETDATE(),
                    TotalAmount DECIMAL(10,2),
                    PaymentMethod NVARCHAR(50),
                    Discount DECIMAL(10,2) DEFAULT 0
                );
            """,

            'SaleDetails': """
                CREATE TABLE SaleDetails (
                    SaleDetailID INT PRIMARY KEY IDENTITY(1,1),
                    SaleID INT FOREIGN KEY REFERENCES Sales(SaleID),
                    ProductID INT FOREIGN KEY REFERENCES Products(ProductID),
                    Quantity INT NOT NULL,
                    UnitPrice DECIMAL(10,2) NOT NULL,
                    Subtotal AS (Quantity * UnitPrice)
                );
            """,

            'Purchases': """
                CREATE TABLE Purchases (
                    PurchaseID INT PRIMARY KEY IDENTITY(1,1),
                    SupplierID INT FOREIGN KEY REFERENCES Suppliers(SupplierID),
                    ProductID INT FOREIGN KEY REFERENCES Products(ProductID),
                    ShopID INT FOREIGN KEY REFERENCES Shops(ShopID),
                    Quantity INT NOT NULL,
                    UnitCost DECIMAL(10,2) NOT NULL,
                    TotalCost AS (Quantity * UnitCost),
                    PurchaseDate DATETIME DEFAULT GETDATE(),
                    DeliveryDate DATE
                );
            """
        }

        try:
            for table_name, table_sql in tables.items():
                self.cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
                    BEGIN
                        {table_sql}
                    END
                """)
            self.connection.commit()
            return True, "Все таблицы успешно созданы!"
        except Exception as e:
            return False, f"Ошибка создания таблиц: {e}"

    def execute_query(self, query, params=None, fetch=True):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            if fetch and self.cursor.description:
                columns = [column[0] for column in self.cursor.description]
                results = self.cursor.fetchall()
                return True, results, columns
            else:
                self.connection.commit()
                return True, self.cursor.rowcount, None
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False, f"Ошибка выполнения запроса: {e}", None

    def insert_sample_data(self):
        """Вставка тестовых данных во все таблицы"""
        try:
            # Очищаем таблицы в правильном порядке (из-за внешних ключей)
            tables_to_clear = ['SaleDetails', 'Sales', 'Purchases', 'Inventory',
                             'Products', 'Suppliers', 'ProductCategories',
                             'Customers', 'Employees', 'Shops']

            for table in tables_to_clear:
                try:
                    self.cursor.execute(f"DELETE FROM {table}")
                    self.cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
                except:
                    pass

            self.connection.commit()

            # 1. Магазины
            shops_data = [
                ('Магазин "Солнечный"', 'ул. Ленина, 10', '+79105551111', 'sun@example.com'),
                ('Супермаркет "Весна"', 'пр. Мира, 25', '+79105552222', 'vesna@example.com'),
                ('Мини-маркет "У дома"', 'ул. Садовая, 5', '+79105553333', 'dom@example.com')
            ]

            for shop in shops_data:
                self.cursor.execute("""
                    INSERT INTO Shops (ShopName, Address, Phone, Email) 
                    VALUES (?, ?, ?, ?)
                """, shop)

            # 2. Категории товаров
            categories_data = [
                ('Молочные продукты', 'Молоко, сыр, йогурты'),
                ('Хлебобулочные изделия', 'Хлеб, булочки, выпечка'),
                ('Напитки', 'Соки, вода, газировка'),
                ('Бакалея', 'Крупы, макароны, консервы'),
                ('Овощи и фрукты', 'Свежие овощи и фрукты')
            ]

            for category in categories_data:
                self.cursor.execute("""
                    INSERT INTO ProductCategories (CategoryName, Description) 
                    VALUES (?, ?)
                """, category)

            # 3. Поставщики
            suppliers_data = [
                ('ООО "МолПродукт"', 'Иванов Иван', '+79106661111', 'milk@example.com', 'ул. Промышленная, 1'),
                ('ИП "Хлебозавод №1"', 'Петров Петр', '+79106662222', 'hleb@example.com', 'ул. Хлебная, 15'),
                ('АО "НапиткиСибири"', 'Сидоров Сидор', '+79106663333', 'drinks@example.com', 'пр. Заводской, 30')
            ]

            for supplier in suppliers_data:
                self.cursor.execute("""
                    INSERT INTO Suppliers (CompanyName, ContactPerson, Phone, Email, Address) 
                    VALUES (?, ?, ?, ?, ?)
                """, supplier)

            # 4. Товары
            products_data = [
                ('Молоко 2,5% 1л', 1, 1, 85.50, 65.00, '4601234567890', 'Пастеризованное молоко'),
                ('Хлеб Бородинский', 2, 2, 45.00, 30.00, '4601234567891', 'Ржаной хлеб'),
                ('Сок апельсиновый 1л', 3, 3, 120.00, 90.00, '4601234567892', 'Сок прямого отжима'),
                ('Гречка 900г', 4, 1, 95.00, 70.00, '4601234567893', 'Гречневая крупа'),
                ('Яблоки Голден', 5, 3, 150.00, 120.00, '4601234567894', 'Свежие яблоки'),
                ('Сыр Российский', 1, 1, 450.00, 380.00, '4601234567895', 'Твердый сыр')
            ]

            for product in products_data:
                self.cursor.execute("""
                    INSERT INTO Products (ProductName, CategoryID, SupplierID, 
                           UnitPrice, PurchasePrice, Barcode, Description) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, product)

            # 5. Сотрудники
            employees_data = [
                (1, 'Анна', 'Иванова', 'Администратор', '+79107771111', 'anna@example.com', 35000),
                (1, 'Сергей', 'Петров', 'Кассир', '+79107772222', 'sergey@example.com', 28000),
                (2, 'Мария', 'Сидорова', 'Менеджер', '+79107773333', 'maria@example.com', 40000),
                (3, 'Дмитрий', 'Кузнецов', 'Продавец', '+79107774444', 'dmitry@example.com', 25000)
            ]

            for employee in employees_data:
                self.cursor.execute("""
                    INSERT INTO Employees (ShopID, FirstName, LastName, Position, 
                           Phone, Email, Salary) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, employee)

            # 6. Клиенты
            customers_data = [
                ('Ольга', 'Смирнова', '+79108881111', 'olga@example.com'),
                ('Игорь', 'Васильев', '+79108882222', 'igor@example.com'),
                ('Елена', 'Попова', '+79108883333', 'elena@example.com'),
                ('Алексей', 'Соколов', '+79108884444', 'alex@example.com')
            ]

            for customer in customers_data:
                self.cursor.execute("""
                    INSERT INTO Customers (FirstName, LastName, Phone, Email) 
                    VALUES (?, ?, ?, ?)
                """, customer)

            # 7. Склад
            inventory_data = [
                (1, 1, 50, 10, '2024-01-01'),
                (1, 2, 30, 5, '2024-01-02'),
                (2, 3, 40, 10, '2024-01-03'),
                (2, 4, 25, 8, '2024-01-04'),
                (3, 5, 60, 15, '2024-01-05'),
                (3, 6, 20, 5, '2024-01-06')
            ]

            for inventory in inventory_data:
                self.cursor.execute("""
                    INSERT INTO Inventory (ShopID, ProductID, Quantity, MinStockLevel, LastRestockDate) 
                    VALUES (?, ?, ?, ?, ?)
                """, inventory)

            # 8. Продажи
            sales_data = [
                (1, 1, 1, '2024-01-15 10:30:00', 175.50, 'Карта', 10.00),
                (2, 3, 2, '2024-01-15 11:45:00', 265.00, 'Наличные', 0),
                (1, 2, 3, '2024-01-16 09:15:00', 450.00, 'Карта', 25.00),
                (3, 4, 4, '2024-01-16 14:20:00', 150.00, 'Наличные', 0)
            ]

            for sale in sales_data:
                self.cursor.execute("""
                    INSERT INTO Sales (ShopID, EmployeeID, CustomerID, SaleDate, 
                           TotalAmount, PaymentMethod, Discount) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, sale)

            # 9. Детали продаж
            sale_details_data = [
                (1, 1, 2, 85.50),
                (1, 2, 1, 45.00),
                (2, 3, 2, 120.00),
                (2, 4, 1, 95.00),
                (3, 6, 1, 450.00),
                (4, 5, 1, 150.00)
            ]

            for detail in sale_details_data:
                self.cursor.execute("""
                    INSERT INTO SaleDetails (SaleID, ProductID, Quantity, UnitPrice) 
                    VALUES (?, ?, ?, ?)
                """, detail)

            # 10. Закупки
            purchases_data = [
                (1, 1, 1, 100, 65.00, '2024-01-01', '2024-01-02'),
                (2, 2, 1, 50, 30.00, '2024-01-02', '2024-01-03'),
                (3, 3, 2, 80, 90.00, '2024-01-03', '2024-01-04')
            ]

            for purchase in purchases_data:
                self.cursor.execute("""
                    INSERT INTO Purchases (SupplierID, ProductID, ShopID, Quantity, 
                           UnitCost, PurchaseDate, DeliveryDate) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, purchase)

            self.connection.commit()
            return True, "Тестовые данные успешно добавлены!"

        except Exception as e:
            self.connection.rollback()
            return False, f"Ошибка при добавлении тестовых данных: {e}"

    def get_table_data(self, table_name, limit=100):
        query = f"SELECT TOP {limit} * FROM {table_name}"
        return self.execute_query(query)

    def get_sales_data(self, start_date=None, end_date=None):
        """Получение данных о продажах с JOIN таблицами"""
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = date.today().strftime("%Y-%m-%d")

        query = """
        SELECT 
            s.SaleID,
            CONVERT(VARCHAR, s.SaleDate, 120) as SaleDate,
            sh.ShopName,
            e.FirstName + ' ' + e.LastName as Employee,
            ISNULL(c.FirstName + ' ' + c.LastName, 'Гость') as Customer,
            s.TotalAmount,
            s.PaymentMethod,
            s.Discount
        FROM Sales s
        LEFT JOIN Shops sh ON s.ShopID = sh.ShopID
        LEFT JOIN Employees e ON s.EmployeeID = e.EmployeeID
        LEFT JOIN Customers c ON s.CustomerID = c.CustomerID
        WHERE CAST(s.SaleDate as DATE) BETWEEN ? AND ?
        ORDER BY s.SaleDate DESC
        """

        return self.execute_query(query, [start_date, end_date])

    def get_top_products_data(self, limit=10):
        """Получение данных о топ товарах"""
        query = f"""
        SELECT TOP {limit}
            p.ProductName,
            ISNULL(pc.CategoryName, 'Без категории') as CategoryName,
            SUM(ISNULL(sd.Quantity, 0)) as TotalSold,
            SUM(ISNULL(sd.Quantity * sd.UnitPrice, 0)) as TotalRevenue
        FROM Products p
        LEFT JOIN ProductCategories pc ON p.CategoryID = pc.CategoryID
        LEFT JOIN SaleDetails sd ON p.ProductID = sd.ProductID
        GROUP BY p.ProductID, p.ProductName, pc.CategoryName
        ORDER BY TotalSold DESC, TotalRevenue DESC
        """

        return self.execute_query(query)

    def create_sale(self, shop_id, employee_id, customer_id, total_amount, payment_method, discount=0):
        """Создание новой продажи"""
        try:
            # Сначала создаем запись продажи
            query = """
            INSERT INTO Sales (ShopID, EmployeeID, CustomerID, TotalAmount, PaymentMethod, Discount)
            OUTPUT INSERTED.SaleID
            VALUES (?, ?, ?, ?, ?, ?)
            """

            self.cursor.execute(query, (shop_id, employee_id, customer_id, total_amount, payment_method, discount))
            sale_id = self.cursor.fetchone()[0]
            self.connection.commit()

            return True, sale_id, None
        except Exception as e:
            return False, f"Ошибка при создании продажи: {e}", None

    def add_sale_detail(self, sale_id, product_id, quantity, unit_price):
        """Добавление детали продажи"""
        try:
            query = """
            INSERT INTO SaleDetails (SaleID, ProductID, Quantity, UnitPrice)
            VALUES (?, ?, ?, ?)
            """

            self.cursor.execute(query, (sale_id, product_id, quantity, unit_price))
            self.connection.commit()
            return True, "Деталь продажи добавлена", None
        except Exception as e:
            return False, f"Ошибка при добавлении детали продажи: {e}", None

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

class SalesManagementApp:
    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Создание меню
        self.create_menu()

        # Создание панели вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Создание вкладок
        self.create_dashboard_tab()
        self.create_shops_tab()
        self.create_employees_tab()  # Новая вкладка для сотрудников
        self.create_products_tab()
        self.create_inventory_tab()
        self.create_sales_tab()
        self.create_customers_tab()
        self.create_reports_tab()
        self.create_statistics_tab()

        # Статус бар
        self.create_status_bar()

    def create_employees_tab(self):
        """Создание вкладки управления сотрудниками"""
        self.employees_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.employees_tab, text="👥 Сотрудники")

        # Панель управления
        control_frame = tk.Frame(self.employees_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(control_frame,
                  text="➕ Добавить сотрудника",
                  command=self.add_employee_dialog,
                  bg=self.colors['success'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="✏️ Изменить",
                  command=self.edit_employee,
                  bg=self.colors['warning'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🗑️ Удалить",
                  command=self.delete_employee,
                  bg=self.colors['danger'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🔄 Обновить",
                  command=self.load_employees,
                  bg=self.colors['secondary'],
                  fg='white').pack(side='left', padx=5)

        # Таблица сотрудников
        columns = ("ID", "Магазин", "Имя", "Фамилия", "Должность",
                   "Телефон", "Email", "Дата найма", "Зарплата", "Активен")

        tree_frame = tk.Frame(self.employees_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.employees_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        column_widths = [50, 120, 80, 80, 100, 100, 150, 100, 80, 60]
        for idx, col in enumerate(columns):
            self.employees_tree.heading(col, text=col)
            self.employees_tree.column(col, width=column_widths[idx])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.employees_tree.yview)
        self.employees_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.employees_tree.xview)
        self.employees_tree.configure(xscrollcommand=hsb.set)

        self.employees_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню для сотрудников
        self.employees_context_menu = tk.Menu(self.root, tearoff=0)
        self.employees_context_menu.add_command(label="Изменить", command=self.edit_employee)
        self.employees_context_menu.add_command(label="Удалить", command=self.delete_employee)
        self.employees_tree.bind("<Button-3>", self.show_employees_context_menu)

    def show_employees_context_menu(self, event):
        """Показ контекстного меню для сотрудников"""
        try:
            self.employees_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.employees_context_menu.grab_release()

    def load_employees(self):
        """Загрузка данных сотрудников"""
        if not self.system:
            return

        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)

        success, results, columns = self.system.get_employees_data()

        if success and results:
            for row in results:
                formatted_row = list(row)
                # Форматируем дату
                if formatted_row[7]:
                    formatted_row[7] = formatted_row[7].strftime("%Y-%m-%d")
                # Форматируем зарплату
                if formatted_row[8]:
                    formatted_row[8] = f"{float(formatted_row[8]):.2f}"
                self.employees_tree.insert('', 'end', values=formatted_row)

    def add_employee_dialog(self):
        """Диалог добавления сотрудника"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление сотрудника")
        dialog.geometry("400x450")

        tk.Label(dialog, text="Новый сотрудник", font=('Arial', 14, 'bold')).pack(pady=10)

        # Получаем список магазинов
        success, shops, _ = self.system.execute_query(
            "SELECT ShopID, ShopName FROM Shops WHERE IsActive = 1 ORDER BY ShopName"
        )

        shop_names = []
        shop_dict = {}
        if success and shops:
            shop_names = [s[1] for s in shops]
            shop_dict = {s[1]: s[0] for s in shops}

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        # Поля для ввода
        tk.Label(fields_frame, text="Магазин:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        self.employee_shop_var = tk.StringVar()
        shop_combo = ttk.Combobox(fields_frame, textvariable=self.employee_shop_var,
                                  values=shop_names, width=30, state='readonly')
        shop_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        if shop_names:
            shop_combo.current(0)

        tk.Label(fields_frame, text="Имя:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        self.employee_first_name_entry = tk.Entry(fields_frame, width=30)
        self.employee_first_name_entry.grid(row=1, column=1, pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Фамилия:", anchor='w').grid(row=2, column=0, sticky='w', pady=5)
        self.employee_last_name_entry = tk.Entry(fields_frame, width=30)
        self.employee_last_name_entry.grid(row=2, column=1, pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Должность:", anchor='w').grid(row=3, column=0, sticky='w', pady=5)
        self.employee_position_entry = tk.Entry(fields_frame, width=30)
        self.employee_position_entry.grid(row=3, column=1, pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Телефон:", anchor='w').grid(row=4, column=0, sticky='w', pady=5)
        self.employee_phone_entry = tk.Entry(fields_frame, width=30)
        self.employee_phone_entry.grid(row=4, column=1, pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Email:", anchor='w').grid(row=5, column=0, sticky='w', pady=5)
        self.employee_email_entry = tk.Entry(fields_frame, width=30)
        self.employee_email_entry.grid(row=5, column=1, pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Зарплата:", anchor='w').grid(row=6, column=0, sticky='w', pady=5)
        self.employee_salary_entry = tk.Entry(fields_frame, width=30)
        self.employee_salary_entry.grid(row=6, column=1, pady=5, padx=(10, 0))
        self.employee_salary_entry.insert(0, "30000")

        def save_employee():
            try:
                # Проверяем заполненность обязательных полей
                if not self.employee_shop_var.get():
                    messagebox.showwarning("Внимание", "Выберите магазин!")
                    return

                if not self.employee_first_name_entry.get().strip():
                    messagebox.showwarning("Внимание", "Введите имя сотрудника!")
                    return

                if not self.employee_last_name_entry.get().strip():
                    messagebox.showwarning("Внимание", "Введите фамилию сотрудника!")
                    return

                shop_id = shop_dict[self.employee_shop_var.get()]
                first_name = self.employee_first_name_entry.get()
                last_name = self.employee_last_name_entry.get()
                position = self.employee_position_entry.get()
                phone = self.employee_phone_entry.get()
                email = self.employee_email_entry.get()
                salary = float(self.employee_salary_entry.get() or 0)

                success, message = self.system.add_employee(
                    shop_id, first_name, last_name, position, phone, email, salary
                )

                if success:
                    messagebox.showinfo("Успех", message)
                    dialog.destroy()
                    self.load_employees()
                    self.update_dashboard_stats()
                else:
                    messagebox.showerror("Ошибка", message)

            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную зарплату!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении сотрудника: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="💾 Сохранить",
                  command=save_employee,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

    def edit_employee(self):
        """Редактирование сотрудника"""
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите сотрудника для редактирования!")
            return

        item = self.employees_tree.item(selection[0])
        employee_id = item['values'][0]

        # Получаем данные сотрудника
        query = """
        SELECT ShopID, FirstName, LastName, Position, Phone, Email, Salary, IsActive
        FROM Employees WHERE EmployeeID = ?
        """

        success, results, _ = self.system.execute_query(query, [employee_id])

        if not success or not results:
            messagebox.showerror("Ошибка", "Не удалось получить данные сотрудника!")
            return

        employee_data = results[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование сотрудника")
        dialog.geometry("400x500")

        tk.Label(dialog, text="Редактирование сотрудника", font=('Arial', 14, 'bold')).pack(pady=10)

        # Получаем список магазинов
        success, shops, _ = self.system.execute_query(
            "SELECT ShopID, ShopName FROM Shops ORDER BY ShopName"
        )

        shop_names = []
        shop_dict = {}
        shop_id_to_name = {}
        if success and shops:
            shop_names = [s[1] for s in shops]
            shop_dict = {s[1]: s[0] for s in shops}
            shop_id_to_name = {s[0]: s[1] for s in shops}

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        # Поля для ввода
        tk.Label(fields_frame, text="Магазин:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        self.edit_employee_shop_var = tk.StringVar()
        shop_combo = ttk.Combobox(fields_frame, textvariable=self.edit_employee_shop_var,
                                  values=shop_names, width=30, state='readonly')
        shop_combo.grid(row=0, column=1, pady=5, padx=(10, 0))

        # Устанавливаем текущий магазин
        current_shop_name = shop_id_to_name.get(employee_data[0], "")
        self.edit_employee_shop_var.set(current_shop_name)

        tk.Label(fields_frame, text="Имя:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        self.edit_employee_first_name_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_first_name_entry.grid(row=1, column=1, pady=5, padx=(10, 0))
        self.edit_employee_first_name_entry.insert(0, employee_data[1])

        tk.Label(fields_frame, text="Фамилия:", anchor='w').grid(row=2, column=0, sticky='w', pady=5)
        self.edit_employee_last_name_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_last_name_entry.grid(row=2, column=1, pady=5, padx=(10, 0))
        self.edit_employee_last_name_entry.insert(0, employee_data[2])

        tk.Label(fields_frame, text="Должность:", anchor='w').grid(row=3, column=0, sticky='w', pady=5)
        self.edit_employee_position_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_position_entry.grid(row=3, column=1, pady=5, padx=(10, 0))
        self.edit_employee_position_entry.insert(0, employee_data[3] or "")

        tk.Label(fields_frame, text="Телефон:", anchor='w').grid(row=4, column=0, sticky='w', pady=5)
        self.edit_employee_phone_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_phone_entry.grid(row=4, column=1, pady=5, padx=(10, 0))
        self.edit_employee_phone_entry.insert(0, employee_data[4] or "")

        tk.Label(fields_frame, text="Email:", anchor='w').grid(row=5, column=0, sticky='w', pady=5)
        self.edit_employee_email_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_email_entry.grid(row=5, column=1, pady=5, padx=(10, 0))
        self.edit_employee_email_entry.insert(0, employee_data[5] or "")

        tk.Label(fields_frame, text="Зарплата:", anchor='w').grid(row=6, column=0, sticky='w', pady=5)
        self.edit_employee_salary_entry = tk.Entry(fields_frame, width=30)
        self.edit_employee_salary_entry.grid(row=6, column=1, pady=5, padx=(10, 0))
        self.edit_employee_salary_entry.insert(0, str(employee_data[6] or "0"))

        tk.Label(fields_frame, text="Активен:", anchor='w').grid(row=7, column=0, sticky='w', pady=5)
        self.edit_employee_active_var = tk.BooleanVar(value=bool(employee_data[7]))
        active_checkbox = tk.Checkbutton(fields_frame, variable=self.edit_employee_active_var)
        active_checkbox.grid(row=7, column=1, sticky='w', pady=5, padx=(10, 0))

        def update_employee():
            try:
                if not self.edit_employee_shop_var.get():
                    messagebox.showwarning("Внимание", "Выберите магазин!")
                    return

                if not self.edit_employee_first_name_entry.get().strip():
                    messagebox.showwarning("Внимание", "Введите имя сотрудника!")
                    return

                if not self.edit_employee_last_name_entry.get().strip():
                    messagebox.showwarning("Внимание", "Введите фамилию сотрудника!")
                    return

                shop_id = shop_dict[self.edit_employee_shop_var.get()]
                first_name = self.edit_employee_first_name_entry.get()
                last_name = self.edit_employee_last_name_entry.get()
                position = self.edit_employee_position_entry.get()
                phone = self.edit_employee_phone_entry.get()
                email = self.edit_employee_email_entry.get()
                salary = float(self.edit_employee_salary_entry.get() or 0)
                is_active = 1 if self.edit_employee_active_var.get() else 0

                success, message = self.system.update_employee(
                    employee_id, shop_id, first_name, last_name, position,
                    phone, email, salary, is_active
                )

                if success:
                    messagebox.showinfo("Успех", message)
                    dialog.destroy()
                    self.load_employees()
                else:
                    messagebox.showerror("Ошибка", message)

            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную зарплату!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении сотрудника: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="💾 Сохранить",
                  command=update_employee,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

    def delete_employee(self):
        """Удаление сотрудника"""
        selection = self.employees_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите сотрудника для удаления!")
            return

        item = self.employees_tree.item(selection[0])
        employee_id = item['values'][0]
        employee_name = f"{item['values'][2]} {item['values'][3]}"

        if messagebox.askyesno("Подтверждение",
                               f"Удалить сотрудника {employee_name}?\n"
                               f"Это действие нельзя отменить!"):
            try:
                success, message = self.system.delete_employee(employee_id)

                if success:
                    messagebox.showinfo("Успех", message)
                    self.load_employees()
                    self.update_dashboard_stats()
                else:
                    messagebox.showerror("Ошибка", message)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении сотрудника: {str(e)}")
    def create_inventory_tab(self):
        """Создание вкладки управления запасами"""
        self.inventory_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.inventory_tab, text="📦 Склад")

        # Панель управления
        control_frame = tk.Frame(self.inventory_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(control_frame,
                  text="➕ Пополнить запасы",
                  command=self.restock_dialog,
                  bg=self.colors['success'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="⚙️ Изменить мин. запас",
                  command=self.update_min_stock_dialog,
                  bg=self.colors['warning'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🔄 Обновить",
                  command=self.load_inventory,
                  bg=self.colors['secondary'],
                  fg='white').pack(side='left', padx=5)

        # Фрейм с фильтрами
        filter_frame = tk.LabelFrame(self.inventory_tab, text="Фильтры", padx=10, pady=5)
        filter_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(filter_frame, text="Статус запасов:").pack(side='left', padx=5)
        self.stock_filter_var = tk.StringVar(value="Все")
        stock_filter_combo = ttk.Combobox(filter_frame, textvariable=self.stock_filter_var,
                                          values=["Все", "Низкий запас", "Заканчивается", "В норме"],
                                          width=15, state='readonly')
        stock_filter_combo.pack(side='left', padx=5)

        tk.Button(filter_frame,
                  text="🔍 Применить фильтр",
                  command=self.load_inventory,
                  bg=self.colors['secondary'],
                  fg='white').pack(side='left', padx=10)

        # Таблица запасов
        columns = ("ID", "Магазин", "Товар", "Категория", "Количество", "Мин. запас", "Дата пополнения", "Статус")

        tree_frame = tk.Frame(self.inventory_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.inventory_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        column_widths = [50, 120, 150, 100, 80, 80, 100, 100]
        for idx, col in enumerate(columns):
            self.inventory_tree.heading(col, text=col)
            self.inventory_tree.column(col, width=column_widths[idx])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.inventory_tree.xview)
        self.inventory_tree.configure(xscrollcommand=hsb.set)

        self.inventory_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню для запасов
        self.inventory_context_menu = tk.Menu(self.root, tearoff=0)
        self.inventory_context_menu.add_command(label="Пополнить запасы", command=self.restock_selected_dialog)
        self.inventory_context_menu.add_command(label="Изменить мин. запас", command=self.update_min_stock_dialog)
        self.inventory_tree.bind("<Button-3>", self.show_inventory_context_menu)

    def show_inventory_context_menu(self, event):
        """Показ контекстного меню для запасов"""
        try:
            self.inventory_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.inventory_context_menu.grab_release()

    def load_inventory(self):
        """Загрузка данных о запасах"""
        if not self.system:
            return

        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        success, results, columns = self.system.get_inventory_data()

        if success and results:
            for row in results:
                formatted_row = list(row)
                # Форматируем дату
                if formatted_row[6]:
                    formatted_row[6] = formatted_row[6].strftime("%Y-%m-%d")

                # Применяем фильтр по статусу
                status_filter = self.stock_filter_var.get()
                if status_filter != "Все" and formatted_row[7] != status_filter:
                    continue

                # Раскрашиваем строки по статусу
                self.inventory_tree.insert('', 'end', values=formatted_row)

                # Добавляем теги для раскраски
                status = formatted_row[7]
                item_id = self.inventory_tree.get_children()[-1]

                if status == 'Низкий запас':
                    self.inventory_tree.item(item_id, tags=('low_stock',))
                elif status == 'Заканчивается':
                    self.inventory_tree.item(item_id, tags=('warning_stock',))
                else:
                    self.inventory_tree.item(item_id, tags=('normal_stock',))

            # Настраиваем теги для цветов
            self.inventory_tree.tag_configure('low_stock', background='#ffcccc')
            self.inventory_tree.tag_configure('warning_stock', background='#fff3cd')
            self.inventory_tree.tag_configure('normal_stock', background='#d4edda')

    def restock_dialog(self, inventory_id=None):
        """Диалог пополнения запасов"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Пополнение запасов" if not inventory_id else "Пополнение выбранного товара")
        dialog.geometry("500x400")

        tk.Label(dialog, text="Пополнение запасов товара",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        # Если передан inventory_id, заполняем поля данными выбранного товара
        if inventory_id:
            # Получаем данные о выбранном товаре на складе
            query = """
            SELECT s.ShopName, p.ProductName, i.Quantity, i.MinStockLevel
            FROM Inventory i
            JOIN Shops s ON i.ShopID = s.ShopID
            JOIN Products p ON i.ProductID = p.ProductID
            WHERE i.InventoryID = ?
            """

            success, results, _ = self.system.execute_query(query, [inventory_id])

            if success and results:
                shop_name, product_name, current_qty, min_stock = results[0]

                tk.Label(fields_frame, text="Магазин:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
                tk.Label(fields_frame, text=shop_name, font=('Arial', 9, 'bold')).grid(row=0, column=1, sticky='w',
                                                                                       pady=5, padx=(10, 0))

                tk.Label(fields_frame, text="Товар:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
                tk.Label(fields_frame, text=product_name, font=('Arial', 9, 'bold')).grid(row=1, column=1, sticky='w',
                                                                                          pady=5, padx=(10, 0))

                tk.Label(fields_frame, text="Текущий запас:", anchor='w').grid(row=2, column=0, sticky='w', pady=5)
                tk.Label(fields_frame, text=f"{current_qty} шт.", font=('Arial', 9)).grid(row=2, column=1, sticky='w',
                                                                                          pady=5, padx=(10, 0))

                tk.Label(fields_frame, text="Минимальный запас:", anchor='w').grid(row=3, column=0, sticky='w', pady=5)
                tk.Label(fields_frame, text=f"{min_stock} шт.", font=('Arial', 9)).grid(row=3, column=1, sticky='w',
                                                                                        pady=5, padx=(10, 0))

                self.current_inventory_id = inventory_id
            else:
                messagebox.showerror("Ошибка", "Не удалось получить данные о товаре!")
                dialog.destroy()
                return
        else:
            # Выбор магазина
            success, shops, _ = self.system.execute_query(
                "SELECT ShopID, ShopName FROM Shops WHERE IsActive = 1 ORDER BY ShopName"
            )

            shop_names = []
            shop_dict = {}
            if success and shops:
                shop_names = [s[1] for s in shops]
                shop_dict = {s[1]: s[0] for s in shops}

            tk.Label(fields_frame, text="Магазин:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
            self.restock_shop_var = tk.StringVar()
            shop_combo = ttk.Combobox(fields_frame, textvariable=self.restock_shop_var,
                                      values=shop_names, width=30, state='readonly')
            shop_combo.grid(row=0, column=1, sticky='w', pady=5, padx=(10, 0))
            if shop_names:
                shop_combo.current(0)

            # Выбор товара
            tk.Label(fields_frame, text="Товар:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
            self.restock_product_var = tk.StringVar()
            product_combo = ttk.Combobox(fields_frame, textvariable=self.restock_product_var,
                                         values=[], width=30)
            product_combo.grid(row=1, column=1, sticky='w', pady=5, padx=(10, 0))

            # Функция для загрузки товаров
            def load_products(event=None):
                if self.restock_shop_var.get() and self.restock_shop_var.get() in shop_dict:
                    shop_id = shop_dict[self.restock_shop_var.get()]

                    # Получаем все товары
                    success, products, _ = self.system.get_all_products()

                    product_names = []
                    self.product_dict = {}

                    if success and products:
                        for p in products:
                            display_text = f"{p[1]} ({p[2]})"
                            product_names.append(display_text)
                            self.product_dict[display_text] = p[0]

                    product_combo['values'] = product_names
                    if product_names:
                        product_combo.current(0)

            shop_combo.bind('<<ComboboxSelected>>', load_products)

            # Вызов загрузки товаров при открытии
            dialog.after(100, load_products)

            self.current_inventory_id = None

        # Количество для пополнения
        tk.Label(fields_frame, text="Количество для пополнения:", anchor='w').grid(row=4, column=0, sticky='w', pady=10)
        self.restock_quantity_entry = tk.Entry(fields_frame, width=15)
        self.restock_quantity_entry.grid(row=4, column=1, sticky='w', pady=10, padx=(10, 0))
        self.restock_quantity_entry.insert(0, "10")

        # Дата пополнения
        tk.Label(fields_frame, text="Дата пополнения:", anchor='w').grid(row=5, column=0, sticky='w', pady=5)
        self.restock_date_entry = tk.Entry(fields_frame, width=15)
        self.restock_date_entry.grid(row=5, column=1, sticky='w', pady=5, padx=(10, 0))
        self.restock_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        # Поставщик (опционально)
        success, suppliers, _ = self.system.execute_query(
            "SELECT SupplierID, CompanyName FROM Suppliers ORDER BY CompanyName"
        )

        supplier_names = ["Не указан"]
        supplier_dict = {"Не указан": None}
        if success and suppliers:
            for s in suppliers:
                supplier_names.append(s[1])
                supplier_dict[s[1]] = s[0]

        tk.Label(fields_frame, text="Поставщик:", anchor='w').grid(row=6, column=0, sticky='w', pady=5)
        self.restock_supplier_var = tk.StringVar(value="Не указан")
        supplier_combo = ttk.Combobox(fields_frame, textvariable=self.restock_supplier_var,
                                      values=supplier_names, width=25, state='readonly')
        supplier_combo.grid(row=6, column=1, sticky='w', pady=5, padx=(10, 0))

        # Цена закупки (только если указан поставщик)
        tk.Label(fields_frame, text="Цена закупки:", anchor='w').grid(row=7, column=0, sticky='w', pady=5)
        self.restock_price_entry = tk.Entry(fields_frame, width=15)
        self.restock_price_entry.grid(row=7, column=1, sticky='w', pady=5, padx=(10, 0))
        self.restock_price_entry.insert(0, "0")

        def process_restock():
            try:
                # Проверяем заполненность полей
                if not self.restock_quantity_entry.get():
                    messagebox.showwarning("Внимание", "Введите количество для пополнения!")
                    return

                quantity = int(self.restock_quantity_entry.get())

                if quantity <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть больше 0!")
                    return

                restock_date = self.restock_date_entry.get()

                # Проверяем формат даты
                try:
                    datetime.strptime(restock_date, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Ошибка", "Неверный формат даты! Используйте ГГГГ-ММ-ДД")
                    return

                if self.current_inventory_id:
                    # Пополняем существующий товар
                    success, message = self.system.restock_product(
                        self.current_inventory_id, quantity, restock_date
                    )
                else:
                    # Получаем ID магазина и товара
                    if not self.restock_shop_var.get():
                        messagebox.showwarning("Внимание", "Выберите магазин!")
                        return

                    if not self.restock_product_var.get():
                        messagebox.showwarning("Внимание", "Выберите товар!")
                        return

                    shop_id = shop_dict[self.restock_shop_var.get()]
                    product_id = self.product_dict[self.restock_product_var.get()]

                    success, message = self.system.restock_product_by_shop_product(
                        shop_id, product_id, quantity, restock_date
                    )

                if success:
                    # Если указан поставщик и цена, создаем запись о закупке
                    supplier_name = self.restock_supplier_var.get()
                    if supplier_name != "Не указан":
                        supplier_id = supplier_dict[supplier_name]
                        purchase_price = float(self.restock_price_entry.get() or 0)

                        if purchase_price > 0:
                            # Получаем ShopID для закупки
                            if self.current_inventory_id:
                                # Получаем ShopID из Inventory
                                query = "SELECT ShopID FROM Inventory WHERE InventoryID = ?"
                                success_result, inv_result, _ = self.system.execute_query(query,
                                                                                          [self.current_inventory_id])
                                if success_result and inv_result:
                                    shop_id = inv_result[0][0]

                                    # Получаем ProductID из Inventory
                                    query = "SELECT ProductID FROM Inventory WHERE InventoryID = ?"
                                    success_result, inv_result, _ = self.system.execute_query(query,
                                                                                              [self.current_inventory_id])
                                    if success_result and inv_result:
                                        product_id = inv_result[0][0]

                                        # Создаем запись о закупке
                                        purchase_query = """
                                        INSERT INTO Purchases (SupplierID, ProductID, ShopID, Quantity, 
                                               UnitCost, PurchaseDate, DeliveryDate)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """
                                        self.system.execute_query(purchase_query,
                                                                  [supplier_id, product_id, shop_id, quantity,
                                                                   purchase_price, restock_date, restock_date],
                                                                  fetch=False)

                    messagebox.showinfo("Успех", message)
                    dialog.destroy()
                    self.load_inventory()
                else:
                    messagebox.showerror("Ошибка", message)

            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверный формат данных: {str(e)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при пополнении запасов: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="✅ Пополнить запасы",
                  command=process_restock,
                  bg=self.colors['success'],
                  fg='white',
                  width=20).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=20).pack(side='left', padx=5)

    def restock_selected_dialog(self):
        """Диалог пополнения для выбранного товара"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для пополнения запасов!")
            return

        item = self.inventory_tree.item(selection[0])
        inventory_id = item['values'][0]

        self.restock_dialog(inventory_id)

    def update_min_stock_dialog(self):
        """Диалог изменения минимального уровня запасов"""
        selection = self.inventory_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для изменения минимального уровня запасов!")
            return

        item = self.inventory_tree.item(selection[0])
        inventory_id = item['values'][0]
        current_min = item['values'][5]
        product_name = item['values'][2]
        shop_name = item['values'][1]

        dialog = tk.Toplevel(self.root)
        dialog.title("Изменение минимального уровня запасов")
        dialog.geometry("400x300")

        tk.Label(dialog, text="Изменение минимального уровня",
                 font=('Arial', 14, 'bold')).pack(pady=10)

        info_frame = tk.Frame(dialog)
        info_frame.pack(padx=20, pady=10)

        tk.Label(info_frame, text="Магазин:", font=('Arial', 10, 'bold')).pack(anchor='w')
        tk.Label(info_frame, text=shop_name, font=('Arial', 10)).pack(anchor='w', pady=(0, 10))

        tk.Label(info_frame, text="Товар:", font=('Arial', 10, 'bold')).pack(anchor='w')
        tk.Label(info_frame, text=product_name, font=('Arial', 10)).pack(anchor='w', pady=(0, 20))

        tk.Label(info_frame, text="Текущий минимальный уровень:", font=('Arial', 10)).pack(anchor='w')
        tk.Label(info_frame, text=f"{current_min} шт.", font=('Arial', 10, 'bold')).pack(anchor='w', pady=(0, 10))

        tk.Label(info_frame, text="Новый минимальный уровень:", font=('Arial', 10)).pack(anchor='w')
        self.new_min_stock_entry = tk.Entry(info_frame, width=10)
        self.new_min_stock_entry.pack(anchor='w', pady=(5, 0))
        self.new_min_stock_entry.insert(0, str(current_min))

        def update_min_stock():
            try:
                new_min = int(self.new_min_stock_entry.get())

                if new_min < 0:
                    messagebox.showerror("Ошибка", "Минимальный уровень не может быть отрицательным!")
                    return

                success, message = self.system.update_min_stock_level(inventory_id, new_min)

                if success:
                    messagebox.showinfo("Успех", message)
                    dialog.destroy()
                    self.load_inventory()
                else:
                    messagebox.showerror("Ошибка", message)

            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число!")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="💾 Сохранить",
                  command=update_min_stock,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)
    def __init__(self, root):
        self.root = root
        self.root.title("🏪 Реализация продаж в магазинах")
        self.root.geometry("1300x750")

        # Инициализация системы БД
        self.system = None

        # Создание стиля
        self.setup_styles()

        # Создание интерфейса
        self.create_widgets()

        # Попытка подключения к БД
        self.connect_to_database()

    def setup_styles(self):
        """Настройка стилей для виджетов"""
        style = ttk.Style()

        # Цветовая схема
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#34495e'
        }

        # Конфигурация стилей
        style.theme_use('clam')

    def create_widgets(self):
        """Создание всех виджетов интерфейса"""
        # Создание меню
        self.create_menu()

        # Создание панели вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # Создание вкладок
        self.create_dashboard_tab()
        self.create_shops_tab()
        self.create_employees_tab()
        self.create_products_tab()
        self.create_inventory_tab()  # Добавляем вкладку склада
        self.create_sales_tab()
        self.create_customers_tab()
        self.create_reports_tab()
        self.create_statistics_tab()

        # Статус бар
        self.create_status_bar()

    def create_menu(self):
        """Создание меню приложения"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Подключиться к БД", command=self.connect_dialog)
        file_menu.add_command(label="Создать базу данных", command=self.create_database)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт данных", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)

        # Меню "Данные"
        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Данные", menu=data_menu)
        data_menu.add_command(label="Добавить тестовые данные", command=self.add_test_data)
        data_menu.add_command(label="Очистить все данные", command=self.clear_all_data)

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_dashboard_tab(self):
        """Создание вкладки дашборда"""
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_tab, text="📊 Дашборд")

        # Заголовок
        title_label = tk.Label(self.dashboard_tab,
                               text="Панель управления продажами",
                               font=('Arial', 20, 'bold'),
                               fg=self.colors['primary'])
        title_label.pack(pady=20)

        # Фрейм для кнопок быстрого доступа (обновленный список с сотрудниками)
        quick_access_frame = tk.Frame(self.dashboard_tab)
        quick_access_frame.pack(fill='x', padx=20, pady=10)

        buttons = [
            ("🏪 Магазины", lambda: self.notebook.select(1)),
            ("👥 Сотрудники", lambda: self.notebook.select(2)),  # Новая кнопка
            ("📦 Товары", lambda: self.notebook.select(3)),
            ("📦 Склад", lambda: self.notebook.select(4)),
            ("💰 Продажи", lambda: self.notebook.select(5)),
            ("👥 Клиенты", lambda: self.notebook.select(6)),
            ("📈 Отчеты", lambda: self.notebook.select(7)),
            ("📊 Статистика", lambda: self.notebook.select(8))
        ]

        for i, (text, command) in enumerate(buttons):
            btn = tk.Button(quick_access_frame,
                            text=text,
                            command=command,
                            bg=self.colors['secondary'],
                            fg='white',
                            font=('Arial', 11),
                            padx=15,
                            pady=8,
                            relief='raised',
                            bd=2)
            btn.grid(row=i // 4, column=i % 4, padx=5, pady=5, sticky='nsew')
            quick_access_frame.grid_columnconfigure(i % 4, weight=1)

        # Остальной код метода остается без изменений...
        # Фрейм для статистики
        stats_frame = tk.LabelFrame(self.dashboard_tab,
                                    text="📈 Быстрая статистика",
                                    font=('Arial', 12, 'bold'),
                                    padx=15,
                                    pady=15)
        stats_frame.pack(fill='x', padx=20, pady=20)

        # Статистические показатели
        self.stats_labels = {}
        stats_items = [
            ("Всего магазинов:", "shops_count"),
            ("Всего сотрудников:", "employees_count"),
            ("Всего товаров:", "products_count"),
            ("Всего клиентов:", "customers_count"),
            ("Всего продаж:", "sales_count"),
            ("Общая выручка:", "total_revenue")
        ]

        for i, (text, key) in enumerate(stats_items):
            frame = tk.Frame(stats_frame)
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=8, sticky='w')

            tk.Label(frame, text=text, font=('Arial', 10)).pack(side='left')
            self.stats_labels[key] = tk.Label(frame, text="0", font=('Arial', 10, 'bold'),
                                              fg=self.colors['primary'])
            self.stats_labels[key].pack(side='left', padx=(5, 0))

        # Кнопка обновления
        tk.Button(self.dashboard_tab,
                  text="🔄 Обновить статистику",
                  command=self.update_dashboard_stats,
                  bg=self.colors['success'],
                  fg='white',
                  font=('Arial', 10),
                  padx=15,
                  pady=5).pack(pady=10)

    # Добавляем новый отчет по истории закупок:
    def show_purchases_report(self):
        """Отчет по закупкам"""
        if not self.system:
            return

        self.report_text.delete(1.0, tk.END)

        query = """
        SELECT 
            p.PurchaseID,
            s.CompanyName as Supplier,
            pr.ProductName,
            sh.ShopName,
            p.Quantity,
            p.UnitCost,
            p.TotalCost,
            p.PurchaseDate,
            p.DeliveryDate
        FROM Purchases p
        LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
        LEFT JOIN Products pr ON p.ProductID = pr.ProductID
        LEFT JOIN Shops sh ON p.ShopID = sh.ShopID
        ORDER BY p.PurchaseDate DESC
        """

        success, results, columns = self.system.execute_query(query)

        if success:
            self.report_text.insert(tk.END, "📦 ОТЧЕТ ПО ЗАКУПКАМ\n")
            self.report_text.insert(tk.END, "=" * 60 + "\n\n")

            if results:
                total_cost = 0
                total_quantity = 0

                for row in results:
                    self.report_text.insert(tk.END, f"Закупка #{row[0]}:\n")
                    self.report_text.insert(tk.END, f"  Поставщик: {row[1]}\n")
                    self.report_text.insert(tk.END, f"  Товар: {row[2]}\n")
                    self.report_text.insert(tk.END, f"  Магазин: {row[3]}\n")
                    self.report_text.insert(tk.END, f"  Количество: {row[4]} шт.\n")
                    self.report_text.insert(tk.END, f"  Цена закупки: {row[5]:.2f} руб.\n")
                    self.report_text.insert(tk.END, f"  Общая стоимость: {row[6]:.2f} руб.\n")
                    self.report_text.insert(tk.END,
                                            f"  Дата закупки: {row[7].strftime('%Y-%m-%d') if hasattr(row[7], 'strftime') else row[7]}\n")
                    if row[8]:
                        self.report_text.insert(tk.END,
                                                f"  Дата доставки: {row[8].strftime('%Y-%m-%d') if hasattr(row[8], 'strftime') else row[8]}\n")
                    self.report_text.insert(tk.END, "-" * 40 + "\n")

                    total_cost += float(row[6]) if row[6] else 0
                    total_quantity += int(row[4]) if row[4] else 0

                self.report_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                self.report_text.insert(tk.END, f"ИТОГО: {len(results)} закупок\n")
                self.report_text.insert(tk.END, f"Общее количество: {total_quantity} шт.\n")
                self.report_text.insert(tk.END, f"Общая стоимость: {total_cost:.2f} руб.\n")
            else:
                self.report_text.insert(tk.END, "Закупок нет.\n")
        else:
            self.report_text.insert(tk.END, f"Ошибка: {results}")

    def create_shops_tab(self):
        """Создание вкладки управления магазинами"""
        self.shops_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.shops_tab, text="🏪 Магазины")

        # Панель управления
        control_frame = tk.Frame(self.shops_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(control_frame,
                 text="➕ Добавить магазин",
                 command=self.add_shop_dialog,
                 bg=self.colors['success'],
                 fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                 text="🔄 Обновить",
                 command=self.load_shops,
                 bg=self.colors['secondary'],
                 fg='white').pack(side='left', padx=5)

        # Таблица магазинов
        columns = ("ID", "Название", "Адрес", "Телефон", "Email", "Дата открытия", "Активен")

        # Создаем фрейм для таблицы и скроллбаров
        tree_frame = tk.Frame(self.shops_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Создаем Treeview с полосой прокрутки
        self.shops_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        # Настраиваем ширину колонок
        column_widths = [50, 150, 200, 100, 150, 100, 80]
        for idx, col in enumerate(columns):
            self.shops_tree.heading(col, text=col)
            self.shops_tree.column(col, width=column_widths[idx], minwidth=50)

        # Вертикальная полоса прокрутки
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.shops_tree.yview)
        self.shops_tree.configure(yscrollcommand=vsb.set)

        # Горизонтальная полоса прокрутки
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.shops_tree.xview)
        self.shops_tree.configure(xscrollcommand=hsb.set)

        # Размещаем элементы
        self.shops_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню
        self.shops_context_menu = tk.Menu(self.root, tearoff=0)
        self.shops_context_menu.add_command(label="Изменить", command=self.edit_shop)
        self.shops_context_menu.add_command(label="Удалить", command=self.delete_shop)
        self.shops_tree.bind("<Button-3>", self.show_shops_context_menu)

    def create_products_tab(self):
        """Создание вкладки управления товарами"""
        self.products_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.products_tab, text="📦 Товары")

        # Панель управления
        control_frame = tk.Frame(self.products_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(control_frame,
                  text="➕ Добавить товар",
                  command=self.add_product_dialog,
                  bg=self.colors['success'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="✏️ Изменить",
                  command=self.edit_product,
                  bg=self.colors['warning'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🗑️ Удалить",
                  command=self.delete_product,
                  bg=self.colors['danger'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🔄 Обновить",
                  command=self.load_products,
                  bg=self.colors['secondary'],
                  fg='white').pack(side='left', padx=5)

        # Таблица товаров
        columns = ("ID", "Название", "Категория", "Цена", "Закупка", "Штрихкод")

        tree_frame = tk.Frame(self.products_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.products_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        column_widths = [50, 200, 150, 80, 80, 120]
        for idx, col in enumerate(columns):
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=column_widths[idx])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.products_tree.xview)
        self.products_tree.configure(xscrollcommand=hsb.set)

        self.products_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню для товаров
        self.products_context_menu = tk.Menu(self.root, tearoff=0)
        self.products_context_menu.add_command(label="Изменить", command=self.edit_product)
        self.products_context_menu.add_command(label="Удалить", command=self.delete_product)
        self.products_tree.bind("<Button-3>", self.show_products_context_menu)

    def show_products_context_menu(self, event):
        """Показ контекстного меню для товаров"""
        try:
            self.products_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.products_context_menu.grab_release()

    def create_sales_tab(self):
        """Создание вкладки управления продажами"""
        self.sales_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.sales_tab, text="💰 Продажи")

        # Верхняя панель
        top_frame = tk.Frame(self.sales_tab)
        top_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(top_frame,
                  text="➕ Новая продажа",
                  command=self.new_sale_dialog,
                  bg=self.colors['success'],
                  fg='white',
                  font=('Arial', 10, 'bold')).pack(side='left', padx=5)

        tk.Button(top_frame,
                  text="🗑️ Удалить продажу",
                  command=self.delete_sale,
                  bg=self.colors['danger'],
                  fg='white').pack(side='left', padx=5)

        # Фрейм с фильтрами
        filter_frame = tk.LabelFrame(self.sales_tab, text="Фильтры", padx=10, pady=5)
        filter_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(filter_frame, text="Дата от:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date_entry = tk.Entry(filter_frame, width=12)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)
        self.start_date_entry.insert(0, (date.today() - timedelta(days=30)).strftime("%Y-%m-%d"))

        tk.Label(filter_frame, text="Дата до:").grid(row=0, column=2, padx=5, pady=5)
        self.end_date_entry = tk.Entry(filter_frame, width=12)
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.end_date_entry.insert(0, date.today().strftime("%Y-%m-%d"))

        tk.Button(filter_frame,
                  text="🔍 Применить",
                  command=self.load_sales,
                  bg=self.colors['secondary'],
                  fg='white').grid(row=0, column=4, padx=10, pady=5)

        # Таблица продаж
        columns = ("ID", "Дата", "Магазин", "Сотрудник", "Клиент", "Сумма", "Оплата", "Скидка")

        tree_frame = tk.Frame(self.sales_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.sales_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)

        column_widths = [50, 120, 120, 120, 120, 80, 80, 80]
        for idx, col in enumerate(columns):
            self.sales_tree.heading(col, text=col)
            self.sales_tree.column(col, width=column_widths[idx])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.sales_tree.yview)
        self.sales_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.sales_tree.xview)
        self.sales_tree.configure(xscrollcommand=hsb.set)

        self.sales_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню для продаж
        self.sales_context_menu = tk.Menu(self.root, tearoff=0)
        self.sales_context_menu.add_command(label="Показать детали", command=self.show_sale_details)
        self.sales_context_menu.add_command(label="Удалить", command=self.delete_sale)
        self.sales_tree.bind("<Button-3>", self.show_sales_context_menu)

        # Кнопка просмотра деталей
        tk.Button(self.sales_tab,
                  text="📋 Показать детали продажи",
                  command=self.show_sale_details,
                  bg=self.colors['primary'],
                  fg='white').pack(pady=10)

    def show_sales_context_menu(self, event):
        """Показ контекстного меню для продаж"""
        try:
            self.sales_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.sales_context_menu.grab_release()

    def create_customers_tab(self):
        """Создание вкладки управления клиентами"""
        self.customers_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.customers_tab, text="👥 Клиенты")

        # Панель управления
        control_frame = tk.Frame(self.customers_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(control_frame,
                  text="➕ Добавить клиента",
                  command=self.add_customer_dialog,
                  bg=self.colors['success'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="✏️ Изменить",
                  command=self.edit_customer,
                  bg=self.colors['warning'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🗑️ Удалить",
                  command=self.delete_customer,
                  bg=self.colors['danger'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(control_frame,
                  text="🔄 Обновить",
                  command=self.load_customers,
                  bg=self.colors['secondary'],
                  fg='white').pack(side='left', padx=5)

        # Таблица клиентов
        columns = ("ID", "Имя", "Фамилия", "Телефон", "Email", "Дата регистрации", "Активен")

        tree_frame = tk.Frame(self.customers_tab)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.customers_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)

        column_widths = [50, 100, 100, 100, 150, 100, 80]
        for idx, col in enumerate(columns):
            self.customers_tree.heading(col, text=col)
            self.customers_tree.column(col, width=column_widths[idx])

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.customers_tree.yview)
        self.customers_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.customers_tree.xview)
        self.customers_tree.configure(xscrollcommand=hsb.set)

        self.customers_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Контекстное меню для клиентов
        self.customers_context_menu = tk.Menu(self.root, tearoff=0)
        self.customers_context_menu.add_command(label="Изменить", command=self.edit_customer)
        self.customers_context_menu.add_command(label="Удалить", command=self.delete_customer)
        self.customers_tree.bind("<Button-3>", self.show_customers_context_menu)

    def show_customers_context_menu(self, event):
        """Показ контекстного меню для клиентов"""
        try:
            self.customers_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.customers_context_menu.grab_release()

    def create_reports_tab(self):
        """Создание вкладки отчетов"""
        self.reports_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_tab, text="📈 Отчеты")

        # Панель выбора отчета
        report_frame = tk.LabelFrame(self.reports_tab, text="Выбор отчета", padx=10, pady=10)
        report_frame.pack(fill='x', padx=10, pady=5)

        reports = [
            ("📊 Продажи за сегодня", self.show_daily_sales_report),
            ("🏆 Топ товаров", self.show_top_products_report),
            ("📦 Низкие запасы", self.show_low_stock_report),
            ("💰 Финансовый отчет", self.show_financial_report),
            ("📦 История закупок", self.show_purchases_report)  # Добавляем новый отчет
        ]

        for text, command in reports:
            tk.Button(report_frame,
                      text=text,
                      command=command,
                      bg=self.colors['secondary'],
                      fg='white',
                      width=20).pack(side='left', padx=5, pady=5)

        # Область вывода отчета
        self.report_text = scrolledtext.ScrolledText(self.reports_tab, height=20, width=100)
        self.report_text.pack(fill='both', expand=True, padx=10, pady=10)

        # Кнопки управления отчетом
        button_frame = tk.Frame(self.reports_tab)
        button_frame.pack(fill='x', padx=10, pady=5)

        tk.Button(button_frame,
                  text="📄 Экспорт",
                  command=self.export_report_csv,
                  bg=self.colors['success'],
                  fg='white').pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="🖨️ Печать",
                  command=self.print_report,
                  bg=self.colors['primary'],
                  fg='white').pack(side='left', padx=5)

    def create_statistics_tab(self):
        """Создание вкладки статистики"""
        self.statistics_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.statistics_tab, text="📊 Статистика")

        # Панель управления
        control_frame = tk.Frame(self.statistics_tab)
        control_frame.pack(fill='x', padx=10, pady=5)

        tk.Label(control_frame, text="Период (дней):").pack(side='left', padx=5)
        self.period_entry = tk.Entry(control_frame, width=10)
        self.period_entry.pack(side='left', padx=5)
        self.period_entry.insert(0, "30")

        tk.Button(control_frame,
                 text="📈 Построить график",
                 command=self.plot_statistics,
                 bg=self.colors['secondary'],
                 fg='white').pack(side='left', padx=10)

        # Область для графиков
        self.figure_frame = tk.Frame(self.statistics_tab)
        self.figure_frame.pack(fill='both', expand=True, padx=10, pady=10)

    def create_status_bar(self):
        """Создание статус-бара"""
        self.status_bar = tk.Label(self.root, text="Готов к работе", bd=1, relief='sunken', anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

    def connect_to_database(self):
        """Подключение к базе данных"""
        try:
            self.system = SalesManagementSystem()
            success, message = self.system.connect()

            if success:
                self.update_status("✅ Подключено к базе данных")
                # Создаем таблицы, если их нет
                success, msg = self.system.create_tables()
                if not success and "уже существует" not in msg:
                    self.update_status(f"⚠ {msg}")
                self.update_dashboard_stats()
                self.load_shops()
                self.load_employees()  # Загружаем сотрудников
                self.load_products()
                self.load_inventory()
                self.load_sales()
                self.load_customers()
            else:
                self.update_status(f"❌ {message}")
        except Exception as e:
            self.update_status(f"❌ Ошибка: {str(e)}")

    def update_dashboard_stats(self):
        """Обновление статистики на дашборде"""
        if not self.system:
            return

        try:
            # Магазины
            success, result, _ = self.system.execute_query("SELECT COUNT(*) FROM Shops")
            if success and result:
                self.stats_labels['shops_count'].config(text=str(result[0][0] if result[0][0] else 0))

            # Сотрудники
            success, result, _ = self.system.execute_query("SELECT COUNT(*) FROM Employees")
            if success and result:
                self.stats_labels['employees_count'].config(text=str(result[0][0] if result[0][0] else 0))

            # Товары
            success, result, _ = self.system.execute_query("SELECT COUNT(*) FROM Products")
            if success and result:
                self.stats_labels['products_count'].config(text=str(result[0][0] if result[0][0] else 0))

            # Клиенты
            success, result, _ = self.system.execute_query("SELECT COUNT(*) FROM Customers")
            if success and result:
                self.stats_labels['customers_count'].config(text=str(result[0][0] if result[0][0] else 0))

            # Продажи
            success, result, _ = self.system.execute_query("SELECT COUNT(*) FROM Sales")
            if success and result:
                self.stats_labels['sales_count'].config(text=str(result[0][0] if result[0][0] else 0))

            # Общая выручка
            success, result, _ = self.system.execute_query("SELECT SUM(TotalAmount) FROM Sales")
            if success and result and result[0][0]:
                self.stats_labels['total_revenue'].config(text=f"{float(result[0][0]):.2f} руб.")
            else:
                self.stats_labels['total_revenue'].config(text="0.00 руб.")

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")

    def load_shops(self):
        """Загрузка данных магазинов"""
        if not self.system:
            return

        # Очистка таблицы
        for item in self.shops_tree.get_children():
            self.shops_tree.delete(item)

        success, results, columns = self.system.get_table_data("Shops")

        if success and results:
            for row in results:
                # Форматируем дату для отображения
                formatted_row = list(row)
                if formatted_row[5]:  # Дата открытия
                    formatted_row[5] = formatted_row[5].strftime("%Y-%m-%d")
                if formatted_row[6] is not None:  # Активен
                    formatted_row[6] = "Да" if formatted_row[6] else "Нет"
                self.shops_tree.insert('', 'end', values=formatted_row)
        else:
            if not success:
                print(f"Ошибка загрузки магазинов: {results}")

    def load_products(self):
        """Загрузка данных товаров"""
        if not self.system:
            return

        for item in self.products_tree.get_children():
            self.products_tree.delete(item)

        query = """
        SELECT p.ProductID, p.ProductName, pc.CategoryName, p.UnitPrice, 
               p.PurchasePrice, p.Barcode
        FROM Products p
        LEFT JOIN ProductCategories pc ON p.CategoryID = pc.CategoryID
        """

        success, results, columns = self.system.execute_query(query)

        if success and results:
            for row in results:
                formatted_row = list(row)
                if formatted_row[3]:  # Цена
                    formatted_row[3] = f"{float(formatted_row[3]):.2f}"
                if formatted_row[4]:  # Закупочная цена
                    formatted_row[4] = f"{float(formatted_row[4]):.2f}"
                self.products_tree.insert('', 'end', values=formatted_row)

    def load_sales(self):
        """Загрузка данных продаж"""
        if not self.system:
            return

        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        start_date = self.start_date_entry.get()
        end_date = self.end_date_entry.get()

        success, results, columns = self.system.get_sales_data(start_date, end_date)

        if success:
            if results:
                for row in results:
                    formatted_row = list(row)
                    # Форматируем сумму и скидку
                    if formatted_row[5]:  # Сумма
                        formatted_row[5] = f"{float(formatted_row[5]):.2f}"
                    if formatted_row[7]:  # Скидка
                        formatted_row[7] = f"{float(formatted_row[7]):.2f}"
                    self.sales_tree.insert('', 'end', values=formatted_row)
                self.update_status(f"✅ Загружено {len(results)} продаж")
            else:
                self.update_status("ℹ️ Нет данных о продажах за выбранный период")
        else:
            self.update_status(f"❌ Ошибка загрузки продаж: {results}")
            print(f"Ошибка загрузки продаж: {results}")

    def load_customers(self):
        """Загрузка данных клиентов"""
        if not self.system:
            return

        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)

        success, results, columns = self.system.get_table_data("Customers")

        if success and results:
            for row in results:
                formatted_row = list(row)
                if formatted_row[5]:  # Дата регистрации
                    formatted_row[5] = formatted_row[5].strftime("%Y-%m-%d")
                if formatted_row[6] is not None:  # Активен
                    formatted_row[6] = "Да" if formatted_row[6] else "Нет"
                self.customers_tree.insert('', 'end', values=formatted_row)

    def connect_dialog(self):
        """Диалог подключения к БД"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Подключение к базе данных")
        dialog.geometry("400x300")

        tk.Label(dialog, text="Настройки подключения", font=('Arial', 14, 'bold')).pack(pady=10)

        tk.Label(dialog, text="Сервер:").pack(pady=5)
        server_entry = tk.Entry(dialog, width=30)
        server_entry.pack(pady=5)
        server_entry.insert(0, "KRLAP")

        tk.Label(dialog, text="База данных:").pack(pady=5)
        db_entry = tk.Entry(dialog, width=30)
        db_entry.pack(pady=5)
        db_entry.insert(0, "SalesManagement")

        def connect():
            server = server_entry.get()
            database = db_entry.get()

            try:
                self.system = SalesManagementSystem(server, database)
                success, message = self.system.connect()

                if success:
                    messagebox.showinfo("Успех", "Подключение установлено!")
                    dialog.destroy()
                    self.update_status("✅ Подключено к базе данных")
                    self.update_dashboard_stats()
                else:
                    messagebox.showerror("Ошибка", message)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        tk.Button(dialog,
                 text="Подключиться",
                 command=connect,
                 bg=self.colors['success'],
                 fg='white',
                 width=20).pack(pady=20)

    def create_database(self):
        """Создание базы данных"""
        if not self.system:
            messagebox.showerror("Ошибка", "Сначала подключитесь к серверу!")
            return

        if messagebox.askyesno("Подтверждение", "Создать новую базу данных?\nВсе существующие данные будут удалены!"):
            success, message = self.system.create_database()

            if success:
                success, message = self.system.create_tables()
                if success:
                    messagebox.showinfo("Успех", "База данных и таблицы созданы успешно!")
                    self.update_status("✅ База данных создана")
                else:
                    messagebox.showerror("Ошибка", message)
            else:
                messagebox.showerror("Ошибка", message)

    def add_test_data(self):
        """Добавление тестовых данных"""
        if not self.system:
            messagebox.showerror("Ошибка", "Сначала подключитесь к базе данных!")
            return

        if messagebox.askyesno("Подтверждение", "Добавить тестовые данные?"):
            # Показываем индикатор прогресса
            progress_dialog = tk.Toplevel(self.root)
            progress_dialog.title("Добавление данных")
            progress_dialog.geometry("300x150")

            tk.Label(progress_dialog, text="Добавление тестовых данных...", font=('Arial', 12)).pack(pady=20)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_dialog, variable=progress_var, maximum=100)
            progress_bar.pack(pady=10, padx=20, fill='x')

            status_label = tk.Label(progress_dialog, text="Начинаем...")
            status_label.pack(pady=5)

            progress_dialog.update()

            def add_data_thread():
                try:
                    # Вставляем тестовые данные
                    success, message = self.system.insert_sample_data()

                    progress_dialog.destroy()

                    if success:
                        messagebox.showinfo("Успех", "Тестовые данные добавлены!")
                        self.update_dashboard_stats()
                        self.load_shops()
                        self.load_products()
                        self.load_sales()
                        self.load_customers()
                    else:
                        messagebox.showerror("Ошибка", message)

                except Exception as e:
                    progress_dialog.destroy()
                    messagebox.showerror("Ошибка", str(e))

            # Запускаем в отдельном потоке
            thread = threading.Thread(target=add_data_thread)
            thread.daemon = True
            thread.start()

    def clear_all_data(self):
        """Очистка всех данных"""
        if not self.system:
            return

        if messagebox.askyesno("Подтверждение",
                              "ВНИМАНИЕ! Все данные будут удалены без возможности восстановления!\n"
                              "Продолжить?"):
            try:
                # Удаляем данные в правильном порядке (из-за внешних ключей)
                tables = ['SaleDetails', 'Sales', 'Purchases', 'Inventory',
                         'Products', 'Suppliers', 'ProductCategories',
                         'Customers', 'Employees', 'Shops']

                for table in tables:
                    try:
                        self.system.execute_query(f"DELETE FROM {table}", fetch=False)
                    except:
                        pass

                # Сбрасываем identity
                for table in tables:
                    try:
                        self.system.execute_query(f"DBCC CHECKIDENT ('{table}', RESEED, 0)", fetch=False)
                    except:
                        pass

                messagebox.showinfo("Успех", "Все данные очищены!")
                self.update_dashboard_stats()
                self.load_shops()
                self.load_products()
                self.load_sales()
                self.load_customers()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def add_shop_dialog(self):
        """Диалог добавления магазина"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление магазина")
        dialog.geometry("400x350")

        tk.Label(dialog, text="Новый магазин", font=('Arial', 14, 'bold')).pack(pady=10)

        # Поля для ввода
        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        labels = ["Название магазина:", "Адрес:", "Телефон:", "Email:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            entry = tk.Entry(fields_frame, width=30)
            entry.grid(row=i, column=1, pady=5, padx=(10, 0))
            entries.append(entry)

        def save_shop():
            # Проверяем заполненность обязательных полей
            if not entries[0].get().strip():
                messagebox.showwarning("Внимание", "Введите название магазина!")
                return

            try:
                query = """
                INSERT INTO Shops (ShopName, Address, Phone, Email)
                VALUES (?, ?, ?, ?)
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    entries[1].get(),
                    entries[2].get(),
                    entries[3].get()
                ], fetch=False)

                messagebox.showinfo("Успех", "Магазин добавлен!")
                dialog.destroy()
                self.load_shops()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                 text="Сохранить",
                 command=save_shop,
                 bg=self.colors['success'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                 text="Отмена",
                 command=dialog.destroy,
                 bg=self.colors['danger'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

    def show_shops_context_menu(self, event):
        """Показ контекстного меню для магазинов"""
        try:
            self.shops_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.shops_context_menu.grab_release()

    def edit_shop(self):
        """Редактирование магазина"""
        selection = self.shops_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите магазин для редактирования!")
            return

        item = self.shops_tree.item(selection[0])
        shop_id = item['values'][0]

        # Получаем данные магазина
        success, results, _ = self.system.execute_query(
            "SELECT ShopName, Address, Phone, Email, OpeningDate, IsActive FROM Shops WHERE ShopID = ?",
            [shop_id]
        )

        if not success or not results:
            messagebox.showerror("Ошибка", "Не удалось получить данные магазина!")
            return

        shop_data = results[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование магазина")
        dialog.geometry("400x400")

        tk.Label(dialog, text="Редактирование магазина", font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        labels = ["Название магазина:", "Адрес:", "Телефон:", "Email:", "Активен:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            if i < 4:
                entry = tk.Entry(fields_frame, width=30)
                entry.insert(0, shop_data[i] if shop_data[i] else "")
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)
            else:
                var = tk.BooleanVar(value=bool(shop_data[5]))
                checkbox = tk.Checkbutton(fields_frame, variable=var)
                checkbox.grid(row=i, column=1, sticky='w', pady=5, padx=(10, 0))
                entries.append(var)

        def update_shop():
            try:
                query = """
                UPDATE Shops 
                SET ShopName = ?, Address = ?, Phone = ?, Email = ?, IsActive = ?
                WHERE ShopID = ?
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    entries[1].get(),
                    entries[2].get(),
                    entries[3].get(),
                    1 if entries[4].get() else 0,
                    shop_id
                ], fetch=False)

                messagebox.showinfo("Успех", "Данные магазина обновлены!")
                dialog.destroy()
                self.load_shops()

            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                 text="Обновить",
                 command=update_shop,
                 bg=self.colors['success'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                 text="Отмена",
                 command=dialog.destroy,
                 bg=self.colors['danger'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

    def delete_shop(self):
        """Удаление магазина"""
        selection = self.shops_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите магазин для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранный магазин?"):
            item = self.shops_tree.item(selection[0])
            shop_id = item['values'][0]

            try:
                # Проверяем, есть ли связанные записи
                success, result, _ = self.system.execute_query(
                    "SELECT COUNT(*) FROM Employees WHERE ShopID = ?", [shop_id]
                )

                if success and result[0][0] > 0:
                    if not messagebox.askyesno("Внимание",
                        "У этого магазина есть сотрудники. Удалить вместе с сотрудниками?"):
                        return

                self.system.execute_query("DELETE FROM Shops WHERE ShopID = ?", [shop_id], fetch=False)
                messagebox.showinfo("Успех", "Магазин удален!")
                self.load_shops()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить магазин: {str(e)}")

    def add_product_dialog(self):
        """Диалог добавления товара"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление товара")
        dialog.geometry("400x500")

        tk.Label(dialog, text="Новый товар", font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        # Получаем список категорий из базы данных
        success, categories, _ = self.system.execute_query(
            "SELECT CategoryID, CategoryName FROM ProductCategories ORDER BY CategoryName"
        )

        category_names = ["Без категории"]
        category_dict = {"Без категории": None}
        if success and categories:
            for cat in categories:
                category_names.append(cat[1])
                category_dict[cat[1]] = cat[0]

        labels = ["Название товара:", "Категория:", "Цена:", "Закупочная цена:", "Штрихкод:", "Описание:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            if i == 1:  # Категория - выпадающий список
                self.product_category_var = tk.StringVar(value="Без категории")
                category_combo = ttk.Combobox(fields_frame, textvariable=self.product_category_var,
                                              values=category_names, width=27, state='readonly')
                category_combo.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(self.product_category_var)
            elif i == 5:  # Описание - многострочное поле
                entry = tk.Text(fields_frame, width=30, height=4)
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)
            else:
                entry = tk.Entry(fields_frame, width=30)
                if i == 2 or i == 3:  # Цены
                    entry.insert(0, "0.00")
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)

        def save_product():
            try:
                # Проверяем обязательные поля
                if not entries[0].get().strip():
                    messagebox.showwarning("Внимание", "Введите название товара!")
                    return

                # Получаем ID категории
                category_name = entries[1].get()
                category_id = category_dict.get(category_name)

                # Получаем цену, проверяем корректность
                try:
                    price = float(entries[2].get() or 0)
                    if price < 0:
                        messagebox.showerror("Ошибка", "Цена не может быть отрицательной!")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите корректную цену!")
                    return

                # Получаем закупочную цену (опционально)
                purchase_price = None
                if entries[3].get().strip():
                    try:
                        purchase_price = float(entries[3].get())
                        if purchase_price < 0:
                            messagebox.showerror("Ошибка", "Закупочная цена не может быть отрицательной!")
                            return
                    except ValueError:
                        messagebox.showerror("Ошибка", "Введите корректную закупочную цену!")
                        return

                # Получаем описание
                description = entries[5].get("1.0", "end-1c").strip() if hasattr(entries[5], 'get') else entries[
                    5].get()

                query = """
                INSERT INTO Products (ProductName, CategoryID, UnitPrice, PurchasePrice, Barcode, Description)
                VALUES (?, ?, ?, ?, ?, ?)
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    category_id,
                    price,
                    purchase_price,
                    entries[4].get(),
                    description
                ], fetch=False)

                messagebox.showinfo("Успех", "Товар добавлен!")
                dialog.destroy()
                self.load_products()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="Сохранить",
                  command=save_product,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        # Добавляем кнопку для создания новой категории
        tk.Button(fields_frame,
                  text="➕ Новая категория",
                  command=lambda: self.add_category_dialog(dialog, category_combo, category_names, category_dict),
                  bg=self.colors['secondary'],
                  fg='white',
                  font=('Arial', 8)).grid(row=1, column=2, padx=5, pady=5)

    def add_category_dialog(self, parent_dialog=None, category_combo=None, category_names=None, category_dict=None):
        """Диалог добавления новой категории"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая категория")
        dialog.geometry("300x250")

        tk.Label(dialog, text="Новая категория товаров", font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        tk.Label(fields_frame, text="Название категории:", anchor='w').grid(row=0, column=0, sticky='w', pady=10)
        category_name_entry = tk.Entry(fields_frame, width=30)
        category_name_entry.grid(row=0, column=1, pady=10, padx=(10, 0))

        tk.Label(fields_frame, text="Описание:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        description_text = tk.Text(fields_frame, width=30, height=4)
        description_text.grid(row=1, column=1, pady=5, padx=(10, 0))

        def save_category():
            category_name = category_name_entry.get().strip()
            if not category_name:
                messagebox.showwarning("Внимание", "Введите название категории!")
                return

            try:
                query = """
                INSERT INTO ProductCategories (CategoryName, Description)
                VALUES (?, ?)
                """

                self.system.execute_query(query, [
                    category_name,
                    description_text.get("1.0", "end-1c")
                ], fetch=False)

                messagebox.showinfo("Успех", "Категория добавлена!")

                # Если переданы параметры для обновления родительского окна
                if parent_dialog and category_combo and category_names is not None:
                    # Обновляем список категорий
                    success, categories, _ = self.system.execute_query(
                        "SELECT CategoryID, CategoryName FROM ProductCategories ORDER BY CategoryName"
                    )
                    if success and categories:
                        new_category_names = ["Без категории"]
                        new_category_dict = {"Без категории": None}

                        for cat in categories:
                            new_category_names.append(cat[1])
                            new_category_dict[cat[1]] = cat[0]

                        # Обновляем выпадающий список
                        category_combo['values'] = new_category_names
                        category_combo.set(category_name)  # Устанавливаем новую категорию как выбранную

                        # Обновляем переданные словари
                        if category_dict is not None:
                            category_dict.update(new_category_dict)

                dialog.destroy()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при добавлении категории: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="💾 Сохранить",
                  command=save_category,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)
    def add_customer_dialog(self):
        """Диалог добавления клиента"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление клиента")
        dialog.geometry("400x300")

        tk.Label(dialog, text="Новый клиент", font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        labels = ["Имя:", "Фамилия:", "Телефон:", "Email:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            entry = tk.Entry(fields_frame, width=30)
            entry.grid(row=i, column=1, pady=5, padx=(10, 0))
            entries.append(entry)

        def save_customer():
            try:
                query = """
                INSERT INTO Customers (FirstName, LastName, Phone, Email)
                VALUES (?, ?, ?, ?)
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    entries[1].get(),
                    entries[2].get(),
                    entries[3].get()
                ], fetch=False)

                messagebox.showinfo("Успех", "Клиент добавлен!")
                dialog.destroy()
                self.load_customers()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                 text="Сохранить",
                 command=save_customer,
                 bg=self.colors['success'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                 text="Отмена",
                 command=dialog.destroy,
                 bg=self.colors['danger'],
                 fg='white',
                 width=15).pack(side='left', padx=5)

    def new_sale_dialog(self):
        """Диалог новой продажи"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая продажа")
        dialog.geometry("700x550")

        tk.Label(dialog, text="Новая продажа", font=('Arial', 14, 'bold')).pack(pady=10)

        # Переменные для хранения данных
        self.current_shop_id = None
        self.current_product_id = None
        self.product_stock = 0

        # Фрейм для полей ввода
        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        # Получаем список магазинов
        success, shops, _ = self.system.execute_query(
            "SELECT ShopID, ShopName FROM Shops WHERE IsActive = 1"
        )

        shop_names = []
        shop_dict = {}
        if success and shops:
            shop_names = [f"{s[1]}" for s in shops]
            shop_dict = {f"{s[1]}": s[0] for s in shops}

        tk.Label(fields_frame, text="Магазин:", anchor='w').grid(row=0, column=0, sticky='w', pady=5)
        self.shop_var = tk.StringVar()
        shop_combo = ttk.Combobox(fields_frame, textvariable=self.shop_var,
                                  values=shop_names, width=40, state='readonly')
        shop_combo.grid(row=0, column=1, pady=5, padx=(10, 0))
        if shop_names:
            shop_combo.current(0)

        # Функция для обновления сотрудников при выборе магазина
        def update_employees(event=None):
            if self.shop_var.get() and self.shop_var.get() in shop_dict:
                self.current_shop_id = shop_dict[self.shop_var.get()]

                # Получаем сотрудников выбранного магазина
                success, employees, _ = self.system.execute_query(
                    "SELECT EmployeeID, FirstName, LastName FROM Employees WHERE ShopID = ? AND IsActive = 1",
                    [self.current_shop_id]
                )

                employee_names = []
                if success and employees:
                    employee_names = [f"{e[1]} {e[2]}" for e in employees]

                self.employee_var.set('')
                employee_combo['values'] = employee_names
                if employee_names:
                    employee_combo.current(0)

                # Обновляем список товаров для этого магазина
                update_products()

        shop_combo.bind('<<ComboboxSelected>>', update_employees)

        tk.Label(fields_frame, text="Сотрудник:", anchor='w').grid(row=1, column=0, sticky='w', pady=5)
        self.employee_var = tk.StringVar()
        employee_combo = ttk.Combobox(fields_frame, textvariable=self.employee_var,
                                      values=[], width=40, state='readonly')
        employee_combo.grid(row=1, column=1, pady=5, padx=(10, 0))

        # Получаем список клиентов (необязательно)
        success, customers, _ = self.system.execute_query(
            "SELECT CustomerID, FirstName, LastName FROM Customers WHERE IsActive = 1"
        )

        customer_names = ["Гость"]
        customer_dict = {"Гость": 0}
        if success and customers:
            for c in customers:
                customer_names.append(f"{c[1]} {c[2]}")
                customer_dict[f"{c[1]} {c[2]}"] = c[0]

        tk.Label(fields_frame, text="Клиент:", anchor='w').grid(row=2, column=0, sticky='w', pady=5)
        self.customer_var = tk.StringVar(value="Гость")
        customer_combo = ttk.Combobox(fields_frame, textvariable=self.customer_var,
                                      values=customer_names, width=40, state='readonly')
        customer_combo.grid(row=2, column=1, pady=5, padx=(10, 0))

        # Функция для обновления товаров при выборе магазина
        def update_products():
            if not self.current_shop_id:
                return

            # Получаем товары, которые есть на складе выбранного магазина
            query = """
            SELECT p.ProductID, p.ProductName, p.UnitPrice, i.Quantity 
            FROM Products p
            INNER JOIN Inventory i ON p.ProductID = i.ProductID
            WHERE i.ShopID = ? AND i.Quantity > 0
            ORDER BY p.ProductName
            """

            success, products, _ = self.system.execute_query(query, [self.current_shop_id])

            product_names = []
            self.product_dict = {}
            self.product_prices = {}
            self.product_stocks = {}

            if success and products:
                for p in products:
                    display_text = f"{p[1]} ({p[2]} руб.) - остаток: {p[3]} шт."
                    product_names.append(display_text)
                    self.product_dict[display_text] = p[0]
                    self.product_prices[p[0]] = float(p[2])
                    self.product_stocks[p[0]] = int(p[3])

            self.product_var.set('')
            product_combo['values'] = product_names
            if product_names:
                product_combo.current(0)

        tk.Label(fields_frame, text="Товар:", anchor='w').grid(row=3, column=0, sticky='w', pady=5)
        self.product_var = tk.StringVar()
        product_combo = ttk.Combobox(fields_frame, textvariable=self.product_var,
                                     values=[], width=40, state='readonly')
        product_combo.grid(row=3, column=1, pady=5, padx=(10, 0))

        # Метка для отображения остатка товара
        self.stock_label = tk.Label(fields_frame, text="Остаток: -", fg=self.colors['dark'])
        self.stock_label.grid(row=4, column=1, sticky='w', pady=2, padx=(10, 0))

        # Функция для обновления информации о товаре
        def update_product_info(event=None):
            if self.product_var.get() and hasattr(self, 'product_dict'):
                if self.product_var.get() in self.product_dict:
                    product_id = self.product_dict[self.product_var.get()]
                    self.current_product_id = product_id

                    # Получаем остаток товара
                    if product_id in self.product_stocks:
                        stock = self.product_stocks[product_id]
                        self.product_stock = stock
                        self.stock_label.config(text=f"Остаток: {stock} шт.")

                        # Устанавливаем максимальное значение для количества
                        self.quantity_entry.delete(0, tk.END)
                        self.quantity_entry.insert(0, "1")

                        # Обновляем цену
                        if product_id in self.product_prices:
                            price = self.product_prices[product_id]
                            self.unit_price_label.config(text=f"Цена за единицу: {price:.2f} руб.")

        product_combo.bind('<<ComboboxSelected>>', update_product_info)

        tk.Label(fields_frame, text="Количество:", anchor='w').grid(row=5, column=0, sticky='w', pady=5)
        self.quantity_entry = tk.Entry(fields_frame, width=10)
        self.quantity_entry.insert(0, "1")
        self.quantity_entry.grid(row=5, column=1, sticky='w', pady=5, padx=(10, 0))

        # Метка для отображения цены за единицу
        self.unit_price_label = tk.Label(fields_frame, text="Цена за единицу: -")
        self.unit_price_label.grid(row=6, column=1, sticky='w', pady=2, padx=(10, 0))

        tk.Label(fields_frame, text="Способ оплаты:", anchor='w').grid(row=7, column=0, sticky='w', pady=5)
        self.payment_var = tk.StringVar(value="Наличные")
        payment_combo = ttk.Combobox(fields_frame, textvariable=self.payment_var,
                                     values=["Наличные", "Карта", "Онлайн"], width=20, state='readonly')
        payment_combo.grid(row=7, column=1, sticky='w', pady=5, padx=(10, 0))

        tk.Label(fields_frame, text="Скидка (руб.):", anchor='w').grid(row=8, column=0, sticky='w', pady=5)
        self.discount_entry = tk.Entry(fields_frame, width=10)
        self.discount_entry.insert(0, "0")
        self.discount_entry.grid(row=8, column=1, sticky='w', pady=5, padx=(10, 0))

        # Метка для отображения итоговой суммы
        self.total_label = tk.Label(fields_frame, text="Итого: -", font=('Arial', 10, 'bold'),
                                    fg=self.colors['success'])
        self.total_label.grid(row=9, column=1, sticky='w', pady=10, padx=(10, 0))

        # Функция для расчета итоговой суммы
        def calculate_total():
            try:
                quantity = int(self.quantity_entry.get() or 1)
                discount = float(self.discount_entry.get() or 0)

                if self.current_product_id and self.current_product_id in self.product_prices:
                    unit_price = self.product_prices[self.current_product_id]
                    total = (unit_price * quantity) - discount

                    if total < 0:
                        total = 0

                    self.total_label.config(text=f"Итого: {total:.2f} руб.")
            except:
                self.total_label.config(text="Итого: -")

        self.quantity_entry.bind('<KeyRelease>', lambda e: calculate_total())
        self.discount_entry.bind('<KeyRelease>', lambda e: calculate_total())

        def process_sale():
            try:
                # Проверяем заполненность полей
                if not self.shop_var.get():
                    messagebox.showwarning("Внимание", "Выберите магазин!")
                    return

                if not self.employee_var.get():
                    messagebox.showwarning("Внимание", "Выберите сотрудника!")
                    return

                if not self.product_var.get():
                    messagebox.showwarning("Внимание", "Выберите товар!")
                    return

                # Проверяем, выбран ли сотрудник из правильного магазина
                if not self.current_shop_id:
                    messagebox.showwarning("Внимание", "Магазин не выбран!")
                    return

                # Проверяем наличие товара на складе
                if not self.current_product_id:
                    messagebox.showwarning("Внимание", "Товар не выбран!")
                    return

                quantity = int(self.quantity_entry.get() or 1)

                # Проверяем, достаточно ли товара на складе
                if self.product_stock < quantity:
                    messagebox.showerror("Ошибка",
                                         f"Недостаточно товара на складе!\n"
                                         f"Доступно: {self.product_stock} шт.\n"
                                         f"Заказано: {quantity} шт.")
                    return

                if quantity <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть больше 0!")
                    return

                # Получаем ID сотрудника
                employee_name = self.employee_var.get()
                success, result, _ = self.system.execute_query(
                    "SELECT EmployeeID FROM Employees WHERE FirstName + ' ' + LastName = ? AND ShopID = ?",
                    [employee_name, self.current_shop_id]
                )

                if not success or not result:
                    messagebox.showerror("Ошибка", "Сотрудник не найден в выбранном магазине!")
                    return

                employee_id = result[0][0]

                # Получаем ID клиента
                customer_name = self.customer_var.get()
                customer_id = None
                if customer_name != "Гость":
                    customer_id = customer_dict[customer_name]

                discount = float(self.discount_entry.get() or 0)

                # Получаем цену товара
                unit_price = self.product_prices[self.current_product_id]
                total_amount = (unit_price * quantity) - discount

                if total_amount < 0:
                    messagebox.showerror("Ошибка", "Скидка не может превышать сумму заказа!")
                    return

                # Начинаем транзакцию
                self.system.cursor.execute("BEGIN TRANSACTION")

                try:
                    # Создаем продажу
                    success, sale_id, _ = self.system.create_sale(
                        self.current_shop_id, employee_id, customer_id, total_amount,
                        self.payment_var.get(), discount
                    )

                    if not success:
                        raise Exception(sale_id)  # В этом случае sale_id содержит сообщение об ошибке

                    # Добавляем деталь продажи
                    success, message, _ = self.system.add_sale_detail(
                        sale_id, self.current_product_id, quantity, unit_price
                    )

                    if not success:
                        raise Exception(message)

                    # Обновляем количество товара на складе
                    update_query = """
                    UPDATE Inventory 
                    SET Quantity = Quantity - ?
                    WHERE ShopID = ? AND ProductID = ?
                    """
                    self.system.execute_query(update_query,
                                              [quantity, self.current_shop_id, self.current_product_id], fetch=False)

                    # Коммитим транзакцию
                    self.system.connection.commit()

                    messagebox.showinfo("Успех",
                                        f"✅ Продажа #{sale_id} оформлена успешно!\n"
                                        f"Магазин: {self.shop_var.get()}\n"
                                        f"Сотрудник: {employee_name}\n"
                                        f"Товар: {self.product_var.get().split('(')[0].strip()}\n"
                                        f"Количество: {quantity} шт.\n"
                                        f"Сумма: {total_amount:.2f} руб.")

                    dialog.destroy()
                    self.load_sales()
                    self.update_dashboard_stats()

                except Exception as e:
                    # Откатываем транзакцию при ошибке
                    self.system.connection.rollback()
                    raise e

            except ValueError as e:
                messagebox.showerror("Ошибка", f"Неверный формат данных: {str(e)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при оформлении продажи: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="💳 Оформить продажу",
                  command=process_sale,
                  bg=self.colors['success'],
                  fg='white',
                  width=20).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="❌ Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=20).pack(side='left', padx=5)

        # Инициализируем данные при открытии диалога
        dialog.after(100, update_employees)

    def show_sale_details(self):
        """Показать детали выбранной продажи"""
        selection = self.sales_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите продажу для просмотра деталей!")
            return

        item = self.sales_tree.item(selection[0])
        sale_id = item['values'][0]

        dialog = tk.Toplevel(self.root)
        dialog.title(f"Детали продажи #{sale_id}")
        dialog.geometry("500x400")

        # Получаем детали продажи
        query = """
        SELECT p.ProductName, sd.Quantity, sd.UnitPrice, (sd.Quantity * sd.UnitPrice) as Subtotal
        FROM SaleDetails sd
        JOIN Products p ON sd.ProductID = p.ProductID
        WHERE sd.SaleID = ?
        """

        success, results, columns = self.system.execute_query(query, [sale_id])

        if success:
            tk.Label(dialog, text=f"Продажа #{sale_id}", font=('Arial', 14, 'bold')).pack(pady=10)

            # Таблица деталей
            tree_frame = tk.Frame(dialog)
            tree_frame.pack(fill='both', expand=True, padx=10, pady=10)

            tree = ttk.Treeview(tree_frame, columns=("Товар", "Количество", "Цена", "Сумма"),
                               show='headings', height=10)

            column_widths = [200, 80, 80, 100]
            for idx, col in enumerate(["Товар", "Количество", "Цена", "Сумма"]):
                tree.heading(col, text=col)
                tree.column(col, width=column_widths[idx])

            vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)

            tree.grid(row=0, column=0, sticky='nsew')
            vsb.grid(row=0, column=1, sticky='ns')

            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            total = 0
            if results:
                for row in results:
                    tree.insert('', 'end', values=row)
                    total += row[3]

            tk.Label(dialog, text=f"Общая сумма: {total:.2f} руб.",
                    font=('Arial', 12, 'bold')).pack(pady=10)

    def show_daily_sales_report(self):
        """Отчет по продажам за сегодня"""
        if not self.system:
            return

        self.report_text.delete(1.0, tk.END)

        today = date.today().strftime("%Y-%m-%d")

        query = """
        SELECT 
            s.SaleID,
            s.SaleDate,
            sh.ShopName,
            e.FirstName + ' ' + e.LastName as Employee,
            ISNULL(c.FirstName + ' ' + c.LastName, 'Гость') as Customer,
            s.TotalAmount,
            s.PaymentMethod,
            s.Discount,
            (SELECT COUNT(*) FROM SaleDetails sd WHERE sd.SaleID = s.SaleID) as ProductsCount
        FROM Sales s
        LEFT JOIN Shops sh ON s.ShopID = sh.ShopID
        LEFT JOIN Employees e ON s.EmployeeID = e.EmployeeID
        LEFT JOIN Customers c ON s.CustomerID = c.CustomerID
        WHERE CAST(s.SaleDate as DATE) = ?
        ORDER BY s.SaleDate DESC
        """

        success, results, columns = self.system.execute_query(query, [today])

        if success:
            self.report_text.insert(tk.END, f"📊 ОТЧЕТ ПО ПРОДАЖАМ ЗА {today}\n")
            self.report_text.insert(tk.END, "="*60 + "\n\n")

            if results:
                total_amount = 0
                total_sales = len(results)

                for row in results:
                    self.report_text.insert(tk.END, f"Продажа #{row[0]}:\n")
                    self.report_text.insert(tk.END, f"  Время: {row[1].strftime('%H:%M') if hasattr(row[1], 'strftime') else row[1]}\n")
                    self.report_text.insert(tk.END, f"  Магазин: {row[2]}\n")
                    self.report_text.insert(tk.END, f"  Сотрудник: {row[3]}\n")
                    self.report_text.insert(tk.END, f"  Клиент: {row[4]}\n")
                    self.report_text.insert(tk.END, f"  Сумма: {row[5]:.2f} руб.\n")
                    self.report_text.insert(tk.END, f"  Оплата: {row[6]}\n")
                    self.report_text.insert(tk.END, f"  Товаров: {row[8]}\n")
                    self.report_text.insert(tk.END, "-"*40 + "\n")
                    total_amount += row[5] if row[5] else 0

                self.report_text.insert(tk.END, "\n" + "="*60 + "\n")
                self.report_text.insert(tk.END, f"ИТОГО: {total_sales} продаж на сумму {total_amount:.2f} руб.\n")
            else:
                self.report_text.insert(tk.END, "За сегодня продаж нет.\n")
        else:
            self.report_text.insert(tk.END, f"Ошибка: {results}")

    def show_top_products_report(self):
        """Отчет по топ товарам - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        if not self.system:
            self.report_text.insert(tk.END, "Нет подключения к базе данных.\n")
            return

        self.report_text.delete(1.0, tk.END)

        success, results, columns = self.system.get_top_products_data(10)

        if success:
            self.report_text.insert(tk.END, "🏆 ТОП-10 ТОВАРОВ ПО ПРОДАЖАМ\n")
            self.report_text.insert(tk.END, "="*60 + "\n\n")

            if results and len(results) > 0:
                self.report_text.insert(tk.END, f"{'Товар':<30} {'Категория':<20} {'Продано':<10} {'Выручка':<15}\n")
                self.report_text.insert(tk.END, "-"*75 + "\n")

                total_revenue = 0
                for row in results:
                    if row and len(row) >= 4:
                        product_name = str(row[0]) if row[0] else "Без названия"
                        category_name = str(row[1]) if row[1] else "Без категории"
                        total_sold = int(row[2]) if row[2] else 0
                        revenue = float(row[3]) if row[3] else 0.0

                        self.report_text.insert(tk.END, f"{product_name[:30]:<30} {category_name[:20]:<20} {total_sold:<10} {revenue:<15.2f}\n")
                        total_revenue += revenue

                self.report_text.insert(tk.END, "\n" + "="*60 + "\n")
                self.report_text.insert(tk.END, f"Общая выручка: {total_revenue:.2f} руб.\n")
            else:
                self.report_text.insert(tk.END, "Нет данных о продажах.\n")
        else:
            self.report_text.insert(tk.END, f"Ошибка при выполнении запроса: {results}\n")

    def show_low_stock_report(self):
        """Отчет по низким запасам"""
        if not self.system:
            return

        self.report_text.delete(1.0, tk.END)

        query = """
        SELECT 
            s.ShopName,
            p.ProductName,
            i.Quantity,
            i.MinStockLevel,
            CASE 
                WHEN i.Quantity <= i.MinStockLevel THEN 'Низкий запас'
                WHEN i.Quantity <= i.MinStockLevel * 1.5 THEN 'Заканчивается'
                ELSE 'В норме'
            END as StockStatus
        FROM Inventory i
        JOIN Shops s ON i.ShopID = s.ShopID
        JOIN Products p ON i.ProductID = p.ProductID
        WHERE i.Quantity <= i.MinStockLevel * 2
        ORDER BY i.Quantity / i.MinStockLevel
        """

        success, results, columns = self.system.execute_query(query)

        if success:
            self.report_text.insert(tk.END, "📦 ТОВАРЫ С НИЗКИМ ЗАПАСОМ\n")
            self.report_text.insert(tk.END, "="*60 + "\n\n")

            if results:
                self.report_text.insert(tk.END, f"{'Магазин':<20} {'Товар':<30} {'Остаток':<10} {'Мин.запас':<10} {'Статус':<15}\n")
                self.report_text.insert(tk.END, "-"*85 + "\n")

                for row in results:
                    self.report_text.insert(tk.END, f"{str(row[0])[:20]:<20} {str(row[1])[:30]:<30} {row[2]:<10} {row[3]:<10} {str(row[4]):<15}\n")
            else:
                self.report_text.insert(tk.END, "Все товары в наличии!\n")
        else:
            self.report_text.insert(tk.END, f"Ошибка: {results}")

    def show_financial_report(self):
        """Финансовый отчет"""
        if not self.system:
            return

        self.report_text.delete(1.0, tk.END)

        today = date.today()

        query = """
        SELECT 
            COUNT(*) as SalesCount,
            SUM(TotalAmount) as TotalRevenue,
            AVG(TotalAmount) as AvgSale,
            MIN(TotalAmount) as MinSale,
            MAX(TotalAmount) as MaxSale
        FROM Sales
        WHERE MONTH(SaleDate) = MONTH(GETDATE()) 
          AND YEAR(SaleDate) = YEAR(GETDATE())
        """

        success, results, columns = self.system.execute_query(query)

        if success and results and results[0][0]:
            row = results[0]

            self.report_text.insert(tk.END, f"💰 ФИНАНСОВЫЙ ОТЧЕТ ЗА {today.strftime('%B %Y')}\n")
            self.report_text.insert(tk.END, "="*60 + "\n\n")

            self.report_text.insert(tk.END, f"Количество продаж: {row[0]}\n")
            self.report_text.insert(tk.END, f"Общая выручка: {row[1]:.2f} руб.\n")
            self.report_text.insert(tk.END, f"Средний чек: {row[2]:.2f} руб.\n")
            self.report_text.insert(tk.END, f"Минимальная продажа: {row[3]:.2f} руб.\n")
            self.report_text.insert(tk.END, f"Максимальная продажа: {row[4]:.2f} руб.\n")
        else:
            self.report_text.insert(tk.END, "Нет данных для отчета\n")

    def plot_statistics(self):
        """Построение графиков статистики"""
        if not self.system:
            return

        try:
            period = int(self.period_entry.get())
            end_date = date.today()
            start_date = end_date - timedelta(days=period)

            query = """
            SELECT 
                CAST(SaleDate as DATE) as SaleDate,
                COUNT(*) as SalesCount,
                SUM(TotalAmount) as TotalRevenue
            FROM Sales
            WHERE CAST(SaleDate as DATE) BETWEEN ? AND ?
            GROUP BY CAST(SaleDate as DATE)
            ORDER BY SaleDate
            """

            success, results, columns = self.system.execute_query(query, [start_date, end_date])

            if not success or not results:
                messagebox.showinfo("Информация", "Нет данных для построения графика")
                return

            # Очищаем предыдущий график
            for widget in self.figure_frame.winfo_children():
                widget.destroy()

            # Подготавливаем данные
            dates = [row[0].strftime("%d.%m") for row in results]
            revenues = [float(row[2]) if row[2] else 0 for row in results]
            counts = [int(row[1]) if row[1] else 0 for row in results]

            # Создаем фигуру с двумя субплогами
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

            # График выручки
            ax1.plot(dates, revenues, marker='o', color=self.colors['secondary'], linewidth=2)
            ax1.set_title('Выручка по дням', fontsize=14)
            ax1.set_ylabel('Выручка (руб.)', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)

            # График количества продаж
            ax2.bar(dates, counts, color=self.colors['success'], alpha=0.7)
            ax2.set_title('Количество продаж по дням', fontsize=14)
            ax2.set_ylabel('Количество продаж', fontsize=12)
            ax2.set_xlabel('Дата', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)

            plt.tight_layout()

            # Встраиваем график в Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.figure_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка построения графика: {str(e)}")

    def export_report_csv(self):
        """Экспорт отчета в CSV"""
        report_text = self.report_text.get(1.0, tk.END)
        if not report_text.strip():
            messagebox.showwarning("Внимание", "Нет данных для экспорта!")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                messagebox.showinfo("Успех", f"Отчет сохранен в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def print_report(self):
        """Печать отчета"""
        report_text = self.report_text.get(1.0, tk.END)
        if not report_text.strip():
            messagebox.showwarning("Внимание", "Нет данных для печати!")
            return

        # Простая эмуляция печати
        dialog = tk.Toplevel(self.root)
        dialog.title("Печать отчета")
        dialog.geometry("300x150")

        tk.Label(dialog, text="Отчет отправлен на печать", font=('Arial', 12)).pack(pady=30)
        tk.Label(dialog, text="(В реальном приложении здесь будет печать)").pack(pady=10)

        tk.Button(dialog,
                 text="OK",
                 command=dialog.destroy,
                 bg=self.colors['primary'],
                 fg='white',
                 width=10).pack(pady=10)

    def export_data(self):
        """Экспорт данных"""
        if not self.system:
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Экспорт основных таблиц
                tables = ['Shops', 'Products', 'Sales', 'Customers']
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for table in tables:
                        success, results, columns = self.system.get_table_data(table, 1000)
                        if success and results:
                            df = pd.DataFrame(results, columns=columns)
                            df.to_excel(writer, sheet_name=table, index=False)

                messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def show_about(self):
        """Окно 'О программе'"""
        about_text = """🏪 Реализация продаж в магазинах

Версия: 2.2
Разработчик: Корсуков Кирилл БИМ23-01

Функции:
• Управление магазинами и сотрудниками
• Учет товаров и запасов
• Оформление продаж и возвратов
• Управление клиентами
• Аналитика и отчетность
• Визуализация данных

"""

        dialog = tk.Toplevel(self.root)
        dialog.title("О программе")
        dialog.geometry("400x300")

        text_widget = scrolledtext.ScrolledText(dialog, width=50, height=15)
        text_widget.pack(padx=10, pady=10, fill='both', expand=True)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state='disabled')

        tk.Button(dialog,
                 text="Закрыть",
                 command=dialog.destroy,
                 bg=self.colors['primary'],
                 fg='white',
                 width=10).pack(pady=10)

    def update_status(self, message):
        """Обновление статус-бара"""
        self.status_bar.config(text=message)
        self.root.update()

    def delete_product(self):
        """Удаление товара"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранный товар?\nЭто может повлиять на историю продаж."):
            item = self.products_tree.item(selection[0])
            product_id = item['values'][0]

            try:
                # Проверяем, есть ли связанные записи
                success, result, _ = self.system.execute_query(
                    "SELECT COUNT(*) FROM SaleDetails WHERE ProductID = ?", [product_id]
                )

                if success and result[0][0] > 0:
                    if not messagebox.askyesno("Внимание",
                                               "Этот товар есть в продажах. Удалить вместе с историей?"):
                        return

                self.system.execute_query("DELETE FROM Products WHERE ProductID = ?", [product_id], fetch=False)
                messagebox.showinfo("Успех", "Товар удален!")
                self.load_products()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить товар: {str(e)}")

    def edit_product(self):
        """Редактирование товара"""
        selection = self.products_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите товар для редактирования!")
            return

        item = self.products_tree.item(selection[0])
        product_id = item['values'][0]

        # Получаем данные товара с категорией
        query = """
        SELECT p.ProductName, p.CategoryID, p.UnitPrice, 
               p.PurchasePrice, p.Barcode, p.Description 
        FROM Products p
        WHERE p.ProductID = ?
        """

        success, results, _ = self.system.execute_query(query, [product_id])

        if not success or not results:
            messagebox.showerror("Ошибка", "Не удалось получить данные товара!")
            return

        product_data = results[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование товара")
        dialog.geometry("400x500")

        tk.Label(dialog, text="Редактирование товара", font=('Arial', 14, 'bold')).pack(pady=10)

        # Получаем список категорий
        success, categories, _ = self.system.execute_query(
            "SELECT CategoryID, CategoryName FROM ProductCategories ORDER BY CategoryName"
        )

        category_names = ["Без категории"]
        category_dict = {"Без категории": None}

        if success and categories:
            for cat in categories:
                category_names.append(cat[1])
                category_dict[cat[1]] = cat[0]

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        labels = ["Название товара:", "Категория:", "Цена:", "Закупочная цена:", "Штрихкод:", "Описание:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            if i == 1:  # Категория - выпадающий список
                # Получаем название текущей категории
                current_category_id = product_data[1]
                current_category_name = "Без категории"

                if current_category_id:
                    # Ищем название категории по ID
                    for cat in categories:
                        if cat[0] == current_category_id:
                            current_category_name = cat[1]
                            break

                self.edit_product_category_var = tk.StringVar(value=current_category_name)
                category_combo = ttk.Combobox(fields_frame, textvariable=self.edit_product_category_var,
                                              values=category_names, width=27, state='readonly')
                category_combo.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(self.edit_product_category_var)

            elif i == 5:  # Описание - многострочное поле
                entry = tk.Text(fields_frame, width=30, height=4)
                entry.insert(1.0, product_data[5] if product_data[5] else "")
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)
            else:
                entry = tk.Entry(fields_frame, width=30)
                if i == 0:  # Название товара
                    entry.insert(0, product_data[0] if product_data[0] else "")
                elif i == 2:  # Цена
                    entry.insert(0, f"{float(product_data[2]):.2f}" if product_data[2] else "0.00")
                elif i == 3:  # Закупочная цена
                    entry.insert(0, f"{float(product_data[3]):.2f}" if product_data[3] else "0.00")
                elif i == 4:  # Штрихкод
                    entry.insert(0, product_data[4] if product_data[4] else "")
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)

        def update_product():
            try:
                if not entries[0].get().strip():
                    messagebox.showwarning("Внимание", "Введите название товара!")
                    return

                # Получаем ID категории
                category_name = entries[1].get()
                category_id = category_dict.get(category_name)

                # Проверяем цену
                try:
                    price = float(entries[2].get() or 0)
                    if price < 0:
                        messagebox.showerror("Ошибка", "Цена не может быть отрицательной!")
                        return
                except ValueError:
                    messagebox.showerror("Ошибка", "Введите корректную цену!")
                    return

                # Проверяем закупочную цену
                purchase_price = None
                if entries[3].get().strip():
                    try:
                        purchase_price = float(entries[3].get())
                        if purchase_price < 0:
                            messagebox.showerror("Ошибка", "Закупочная цена не может быть отрицательной!")
                            return
                    except ValueError:
                        messagebox.showerror("Ошибка", "Введите корректную закупочную цену!")
                        return

                # Получаем описание
                description = entries[5].get("1.0", "end-1c").strip() if hasattr(entries[5], 'get') else entries[
                    5].get()

                query = """
                UPDATE Products 
                SET ProductName = ?, CategoryID = ?, UnitPrice = ?, 
                    PurchasePrice = ?, Barcode = ?, Description = ?
                WHERE ProductID = ?
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    category_id,
                    price,
                    purchase_price,
                    entries[4].get(),
                    description,
                    product_id
                ], fetch=False)

                messagebox.showinfo("Успех", "Данные товара обновлены!")
                dialog.destroy()
                self.load_products()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при обновлении товара: {str(e)}")

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="Обновить",
                  command=update_product,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        # Добавляем кнопку для создания новой категории
        tk.Button(fields_frame,
                  text="➕ Новая категория",
                  command=lambda: self.add_category_dialog(dialog, category_combo, category_names, category_dict),
                  bg=self.colors['secondary'],
                  fg='white',
                  font=('Arial', 8)).grid(row=1, column=2, padx=5, pady=5)

    def delete_customer(self):
        """Удаление клиента"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранного клиента?"):
            item = self.customers_tree.item(selection[0])
            customer_id = item['values'][0]

            try:
                # Проверяем, есть ли связанные записи в продажах
                success, result, _ = self.system.execute_query(
                    "SELECT COUNT(*) FROM Sales WHERE CustomerID = ?", [customer_id]
                )

                if success and result[0][0] > 0:
                    if not messagebox.askyesno("Внимание",
                                               "У этого клиента есть история покупок. Удалить клиента и обнулить его в истории продаж?"):
                        return
                    # Обнуляем CustomerID в продажах
                    self.system.execute_query(
                        "UPDATE Sales SET CustomerID = NULL WHERE CustomerID = ?",
                        [customer_id], fetch=False
                    )

                self.system.execute_query("DELETE FROM Customers WHERE CustomerID = ?", [customer_id], fetch=False)
                messagebox.showinfo("Успех", "Клиент удален!")
                self.load_customers()
                self.update_dashboard_stats()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить клиента: {str(e)}")

    def edit_customer(self):
        """Редактирование клиента"""
        selection = self.customers_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите клиента для редактирования!")
            return

        item = self.customers_tree.item(selection[0])
        customer_id = item['values'][0]

        # Получаем данные клиента
        success, results, _ = self.system.execute_query(
            "SELECT FirstName, LastName, Phone, Email, IsActive FROM Customers WHERE CustomerID = ?",
            [customer_id]
        )

        if not success or not results:
            messagebox.showerror("Ошибка", "Не удалось получить данные клиента!")
            return

        customer_data = results[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("Редактирование клиента")
        dialog.geometry("400x350")

        tk.Label(dialog, text="Редактирование клиента", font=('Arial', 14, 'bold')).pack(pady=10)

        fields_frame = tk.Frame(dialog)
        fields_frame.pack(padx=20, pady=10)

        labels = ["Имя:", "Фамилия:", "Телефон:", "Email:", "Активен:"]
        entries = []

        for i, label in enumerate(labels):
            tk.Label(fields_frame, text=label, anchor='w').grid(row=i, column=0, sticky='w', pady=5)
            if i == 4:  # Активен - чекбокс
                var = tk.BooleanVar(value=bool(customer_data[4]))
                checkbox = tk.Checkbutton(fields_frame, variable=var)
                checkbox.grid(row=i, column=1, sticky='w', pady=5, padx=(10, 0))
                entries.append(var)
            else:
                entry = tk.Entry(fields_frame, width=30)
                value = customer_data[i] if i < len(customer_data) else ""
                entry.insert(0, str(value) if value else "")
                entry.grid(row=i, column=1, pady=5, padx=(10, 0))
                entries.append(entry)

        def update_customer():
            try:
                query = """
                UPDATE Customers 
                SET FirstName = ?, LastName = ?, Phone = ?, Email = ?, IsActive = ?
                WHERE CustomerID = ?
                """

                self.system.execute_query(query, [
                    entries[0].get(),
                    entries[1].get(),
                    entries[2].get(),
                    entries[3].get(),
                    1 if entries[5].get() else 0,
                    customer_id
                ], fetch=False)

                messagebox.showinfo("Успех", "Данные клиента обновлены!")
                dialog.destroy()
                self.load_customers()

            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=20)

        tk.Button(button_frame,
                  text="Обновить",
                  command=update_customer,
                  bg=self.colors['success'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

        tk.Button(button_frame,
                  text="Отмена",
                  command=dialog.destroy,
                  bg=self.colors['danger'],
                  fg='white',
                  width=15).pack(side='left', padx=5)

    def delete_sale(self):
        """Удаление продажи"""
        selection = self.sales_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите продажу для удаления!")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранную продажу?\nЭто действие нельзя отменить."):
            item = self.sales_tree.item(selection[0])
            sale_id = item['values'][0]

            try:
                # Начинаем транзакцию
                self.system.cursor.execute("BEGIN TRANSACTION")

                # Возвращаем товары на склад
                query_details = """
                SELECT sd.ProductID, sd.Quantity, s.ShopID 
                FROM SaleDetails sd
                JOIN Sales s ON sd.SaleID = s.SaleID
                WHERE sd.SaleID = ?
                """

                success, details, _ = self.system.execute_query(query_details, [sale_id])

                if success and details:
                    for detail in details:
                        product_id, quantity, shop_id = detail
                        # Возвращаем товар на склад
                        update_query = """
                        UPDATE Inventory 
                        SET Quantity = Quantity + ?
                        WHERE ShopID = ? AND ProductID = ?
                        """
                        self.system.execute_query(update_query, [quantity, shop_id, product_id], fetch=False)

                # Удаляем детали продажи
                self.system.execute_query("DELETE FROM SaleDetails WHERE SaleID = ?", [sale_id], fetch=False)

                # Удаляем продажу
                self.system.execute_query("DELETE FROM Sales WHERE SaleID = ?", [sale_id], fetch=False)

                # Коммитим транзакцию
                self.system.connection.commit()

                messagebox.showinfo("Успех", "Продажа удалена!\nТовары возвращены на склад.")
                self.load_sales()
                self.update_dashboard_stats()

            except Exception as e:
                # Откатываем транзакцию при ошибке
                self.system.connection.rollback()
                messagebox.showerror("Ошибка", f"Не удалось удалить продажу: {str(e)}")
def main():
    """Главная функция приложения"""
    root = tk.Tk()
    app = SalesManagementApp(root)

    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    # Обработка закрытия окна
    def on_closing():
        if app.system:
            app.system.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Запуск главного цикла
    root.mainloop()

if __name__ == "__main__":
    # Проверка наличия необходимых библиотек
    try:
        import pyodbc
        import pandas
        import matplotlib
    except ImportError as e:
        print(f"❌ Ошибка: Не установлена необходимая библиотека: {e}")
        print("Установите библиотеки командой: pip install pyodbc pandas matplotlib")
        sys.exit(1)

    main()