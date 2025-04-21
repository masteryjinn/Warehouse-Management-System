CREATE database WarehouseDB2;
USE WarehouseDB2;

-- Категорії товарів
CREATE TABLE ProductCategories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

-- Постачальники
CREATE TABLE Suppliers (
    supplier_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) CHECK (type IN ('manufacturer', 'distributor', 'wholesaler')) NOT NULL
);

-- Клієнти
CREATE TABLE Customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) CHECK (type IN ('individual', 'business')) NOT NULL
);

-- Працівники
CREATE TABLE Employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    position VARCHAR(255)
);

-- Секції складу
CREATE TABLE WarehouseSections (
    section_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    location TEXT,
    employee_id INT,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE SET NULL
);

-- Товари
CREATE TABLE Products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    unit VARCHAR(25) NOT NULL,
    expiration_date DATE,
    category_id INT,
    supplier_id INT,
    section_id INT,
    FOREIGN KEY (category_id) REFERENCES ProductCategories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id) ON DELETE SET NULL,
    FOREIGN KEY (section_id) REFERENCES WarehouseSections(section_id) ON DELETE SET NULL
);

-- Замовлення
CREATE TABLE Orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) CHECK (status IN ('new', 'processing', 'shipped')) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE
);

-- Історія статусів замовлень
CREATE TABLE OrderStatusHistory (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    status VARCHAR(50) CHECK (status IN ('new', 'processing', 'shipped')) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE
);

-- Деталі замовлення
CREATE TABLE OrderDetails (
    order_detail_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2) NOT NULL,
    section_id INT,
    FOREIGN KEY (order_id) REFERENCES Orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES WarehouseSections(section_id) ON DELETE SET NULL
);

-- Рух товарів
CREATE TABLE StockMovements (
    movement_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    movement_type VARCHAR(10) CHECK (movement_type IN ('in', 'out')) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    movement_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    section_id INT,
    FOREIGN KEY (product_id) REFERENCES Products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (section_id) REFERENCES WarehouseSections(section_id) ON DELETE SET NULL
);

-- Звіти
CREATE TABLE Reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_type VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Контакти постачальників
CREATE TABLE Contacts_suppliers (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    supplier_id INT NOT NULL,
    contact_type VARCHAR(50) CHECK (contact_type IN ('address', 'phone', 'email')) NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    CONSTRAINT fk_supplier_contact FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id) ON DELETE CASCADE,
    CONSTRAINT unique_supplier_contact UNIQUE (supplier_id, contact_type, contact_value)
);

-- Контакти клієнтів
CREATE TABLE Contacts_customers (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    contact_type VARCHAR(50) CHECK (contact_type IN ('address', 'phone', 'email')) NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    CONSTRAINT fk_customer_contact FOREIGN KEY (customer_id) REFERENCES Customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT unique_customer_contact UNIQUE (customer_id, contact_type, contact_value)
);

-- Контакти працівників
CREATE TABLE Contacts_employees (
    contact_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    contact_type VARCHAR(50) CHECK (contact_type IN ('address', 'phone', 'email')) NOT NULL,
    contact_value VARCHAR(255) NOT NULL,
    CONSTRAINT fk_employee_contact FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE,
    CONSTRAINT unique_employee_contact UNIQUE (employee_id, contact_type, contact_value)
);

-- Користувачі системи
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'employee') NOT NULL,
    is_temp_password BOOLEAN DEFAULT FALSE,
    employee_id INT UNIQUE NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE
);

