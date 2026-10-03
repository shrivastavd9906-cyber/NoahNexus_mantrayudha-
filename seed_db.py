"""
Seed script for NovaMart SQLite database (novamart.db).
Populates tables with realistic e-commerce data covering all test cases,
edge cases, and quick-test presets.
"""
import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = "novamart.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing tables to refresh cleanly
    tables = ["conversations", "escalations", "support_tickets", "refunds", "returns", "orders", "products", "customers", "policies"]
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t};")

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        loyalty_tier TEXT DEFAULT 'Silver',
        created_at TEXT
    );
    """)

    # 2. Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        sku TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        specs TEXT,
        return_window_days INTEGER NOT NULL DEFAULT 7,
        restocking_fee_percent REAL NOT NULL DEFAULT 0.0,
        warranty_months INTEGER DEFAULT 12
    );
    """)

    # 3. Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        total_amount REAL NOT NULL,
        order_date TEXT NOT NULL,
        status TEXT NOT NULL,
        delivery_date TEXT,
        delivery_eta TEXT,
        tracking_number TEXT,
        otp_verified INTEGER DEFAULT 0,
        delivery_notes TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        FOREIGN KEY (sku) REFERENCES products(sku)
    );
    """)

    # 4. Returns Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS returns (
        return_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        sku TEXT NOT NULL,
        reason TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    """)

    # 5. Refunds Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS refunds (
        refund_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        amount REAL NOT NULL,
        reason TEXT,
        status TEXT NOT NULL,
        processed_at TEXT NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );
    """)

    # 6. Support Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_tickets (
        ticket_id TEXT PRIMARY KEY,
        customer_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        details TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # 7. Escalations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        escalation_id TEXT PRIMARY KEY,
        reference_id TEXT NOT NULL,
        escalation_reason TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    # 8. Conversations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        role TEXT NOT NULL,
        message TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    );
    """)

    # 9. Policies Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        policy_id TEXT PRIMARY KEY,
        version TEXT NOT NULL,
        category TEXT NOT NULL,
        return_window_days INTEGER NOT NULL,
        restocking_fee_percent REAL NOT NULL,
        max_autonomous_refund REAL NOT NULL DEFAULT 50000.0,
        rules_text TEXT,
        is_active INTEGER DEFAULT 1
    );
    """)

    # Seed Customers
    customers = [
        ("CUST-101", "Priya Patel", "priya.patel@example.invalid", "0000000000", "Gold", "2025-01-15 10:30:00"),
        ("CUST-102", "Rahul Sharma", "rahul.sharma@example.invalid", "0000000000", "Platinum", "2024-11-20 14:15:00"),
        ("CUST-103", "Sneha Rao", "sneha.rao@example.invalid", "0000000000", "Silver", "2025-06-01 09:00:00"),
        ("CUST-104", "Vikram Singh", "vikram.singh@example.invalid", "0000000000", "Bronze", "2025-08-10 16:45:00"),
        ("CUST-105", "Arjun Mehta", "arjun.m@example.invalid", "0000000000", "Silver", "2025-05-12 11:20:00"),
        ("CUST-106", "Ravi Kumar", "ravi.k@example.invalid", "0000000000", "Gold", "2024-10-05 13:10:00"),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers)

    # Seed Products
    products = [
        ("SKU-SNY-100", "Sony WH-1000XM5 Noise-Cancelling Headphones", "Electronics", 14990.0, 
         json.dumps({"color": "Black", "battery_life": "30h", "connectivity": "Bluetooth 5.2", "noise_cancelling": "Active"}), 
         7, 5.0, 12),
        ("SKU-BOT-550", "boAt Rockerz 550 Over-Ear Wireless Headphones", "Electronics", 1999.0, 
         json.dumps({"color": "Army Green", "battery_life": "20h", "connectivity": "Bluetooth 5.0"}), 
         7, 5.0, 12),
        ("SKU-HP-PRO", "Headphones Pro Wireless ANC", "Electronics", 2499.0,
         json.dumps({"color": "Matte Black", "drivers": "40mm", "microphone": "Dual ENC"}),
         5, 0.0, 12),
        ("SKU-APL-IP15", "Apple iPhone 15 128GB Black", "Electronics", 74900.0, 
         json.dumps({"display": "6.1 Super Retina XDR", "storage": "128GB", "chip": "A16 Bionic"}), 
         7, 10.0, 12),
        ("SKU-SAM-TV55", "Samsung 55-inch 4K UHD Smart TV", "Electronics", 48990.0, 
         json.dumps({"resolution": "4K Ultra HD", "refresh_rate": "60Hz", "os": "Tizen"}), 
         10, 15.0, 24),
        ("SKU-NIK-AIR", "Nike Air Max 270 Running Shoes", "Footwear", 8495.0, 
         json.dumps({"size": "UK 9", "color": "Triple Black", "type": "Running/Lifestyle"}), 
         14, 0.0, 6),
        ("SKU-MUG-CER", "NovaMart Classic Ceramic Coffee Mug", "Home & Kitchen", 499.0, 
         json.dumps({"capacity": "350ml", "material": "Ceramic", "microwave_safe": True}), 
         30, 0.0, 0),
        ("SKU-LAP-XPS", "Dell XPS 15 InfinityEdge Laptop", "Computers", 124999.0,
         json.dumps({"processor": "Intel i7 13th Gen", "ram": "16GB", "storage": "1TB SSD"}),
         7, 10.0, 24),
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?)", products)

    # Seed Orders
    # Reference date context: Oct 03, 2026
    orders = [
        # Preset 1: NM1042 - out for delivery today
        ("NM1042", "CUST-101", "SKU-APL-IP15", "Apple iPhone 15 128GB Black", 1, 74900.0,
         "2026-10-01 11:20:00", "out_for_delivery", None, "Oct 03, 6 PM", "TRK-IND-90210", 0, 
         "Package dispatched from regional sorting facility at 08:30 AM. Delivery partner: BlueDart."),
        ("NM-1042", "CUST-101", "SKU-APL-IP15", "Apple iPhone 15 128GB Black", 1, 74900.0,
         "2026-10-01 11:20:00", "out_for_delivery", None, "Oct 03, 6 PM", "TRK-IND-90210", 0, 
         "Package dispatched from regional sorting facility at 08:30 AM. Delivery partner: BlueDart."),

        # Preset 2: NM4421 - Delivered via OTP on Sep 28 (Delivery Contradiction case)
        ("NM4421", "CUST-101", "SKU-SNY-100", "Sony WH-1000XM5 Noise-Cancelling Headphones", 1, 14990.0,
         "2026-09-25 15:45:00", "delivered", "2026-09-28 14:10:00", "Sep 28, 2 PM", "TRK-IND-44210", 1,
         "Delivered to recipient; OTP verification recorded."),
        ("NM-4421", "CUST-101", "SKU-SNY-100", "Sony WH-1000XM5 Noise-Cancelling Headphones", 1, 14990.0,
         "2026-09-25 15:45:00", "delivered", "2026-09-28 14:10:00", "Sep 28, 2 PM", "TRK-IND-44210", 1,
         "Delivered to recipient; OTP verification recorded."),

        # Preset 3 / Ambiguity case: Ravi Kumar (CUST-106) & Sneha Rao (CUST-103) both have two headphone orders
        ("NM-1101", "CUST-106", "SKU-SNY-100", "Sony WH-1000XM5 Noise-Cancelling Headphones", 1, 14990.0,
         "2026-09-22 10:00:00", "delivered", "2026-09-24 12:00:00", "Sep 24, 12 PM", "TRK-IND-11010", 1,
         "Delivered to resident at Bangalore."),
        ("NM1101", "CUST-106", "SKU-SNY-100", "Sony WH-1000XM5 Noise-Cancelling Headphones", 1, 14990.0,
         "2026-09-22 10:00:00", "delivered", "2026-09-24 12:00:00", "Sep 24, 12 PM", "TRK-IND-11010", 1,
         "Delivered to resident at Bangalore."),

        ("NM-2230", "CUST-106", "SKU-BOT-550", "boAt Rockerz 550 Over-Ear Wireless Headphones", 1, 1999.0,
         "2026-09-25 18:30:00", "delivered", "2026-09-27 16:20:00", "Sep 27, 4 PM", "TRK-IND-22300", 1,
         "Delivered to resident."),
        ("NM2230", "CUST-106", "SKU-BOT-550", "boAt Rockerz 550 Over-Ear Wireless Headphones", 1, 1999.0,
         "2026-09-25 18:30:00", "delivered", "2026-09-27 16:20:00", "Sep 27, 4 PM", "TRK-IND-22300", 1,
         "Delivered to resident."),

        # Page 11 Case: Arjun Mehta (CUST-105) order NM-7741 (Headphones Pro ₹2,499, delivered Oct 01)
        ("NM-7741", "CUST-105", "SKU-HP-PRO", "Headphones Pro Wireless ANC", 1, 2499.0,
         "2026-09-28 09:12:00", "delivered", "2026-10-01 11:00:00", "Oct 01, 11 AM", "TRK-IND-77410", 1,
         "Delivered to doorstep."),
        ("NM7741", "CUST-105", "SKU-HP-PRO", "Headphones Pro Wireless ANC", 1, 2499.0,
         "2026-09-28 09:12:00", "delivered", "2026-10-01 11:00:00", "Oct 01, 11 AM", "TRK-IND-77410", 1,
         "Delivered to doorstep."),

        # Footwear Return Window case: NM-3310 (Nike Air Max, 14-day window, delivered Oct 01)
        ("NM-3310", "CUST-101", "SKU-NIK-AIR", "Nike Air Max 270 Running Shoes", 1, 8495.0,
         "2026-09-29 13:00:00", "delivered", "2026-10-01 15:30:00", "Oct 01, 3 PM", "TRK-IND-33100", 1,
         "Delivered successfully."),
        ("NM3310", "CUST-101", "SKU-NIK-AIR", "Nike Air Max 270 Running Shoes", 1, 8495.0,
         "2026-09-29 13:00:00", "delivered", "2026-10-01 15:30:00", "Oct 01, 3 PM", "TRK-IND-33100", 1,
         "Delivered successfully."),

        # Return Window Expired: NM-5500 (Samsung TV delivered 45 days ago, return window is 10 days)
        ("NM-5500", "CUST-102", "SKU-SAM-TV55", "Samsung 55-inch 4K UHD Smart TV", 1, 48990.0,
         "2026-08-10 10:00:00", "delivered", "2026-08-14 17:00:00", "Aug 14, 5 PM", "TRK-IND-55000", 1,
         "Delivered and installed."),
        ("NM5500", "CUST-102", "SKU-SAM-TV55", "Samsung 55-inch 4K UHD Smart TV", 1, 48990.0,
         "2026-08-10 10:00:00", "delivered", "2026-08-14 17:00:00", "Aug 14, 5 PM", "TRK-IND-55000", 1,
         "Delivered and installed."),

        # Laptop Order for Context Continuity: NM-8820 (Dell XPS 15)
        ("NM-8820", "CUST-101", "SKU-LAP-XPS", "Dell XPS 15 InfinityEdge Laptop", 1, 124999.0,
         "2026-09-10 11:00:00", "delivered", "2026-09-15 14:00:00", "Sep 15, 2 PM", "TRK-IND-88200", 1,
         "Delivered to Priya Patel."),
        ("NM8820", "CUST-101", "SKU-LAP-XPS", "Dell XPS 15 InfinityEdge Laptop", 1, 124999.0,
         "2026-09-10 11:00:00", "delivered", "2026-09-15 14:00:00", "Sep 15, 2 PM", "TRK-IND-88200", 1,
         "Delivered to Priya Patel."),
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)

    # Seed Versioned Policies
    policies = [
        ("POL-V1-ELEC", "v1.0", "Electronics", 7, 5.0, 50000.0, "Standard return window 7 days from delivery. 5% restocking fee for opened audio/wearables. Max autonomous refund ₹50,000.", 1),
        ("POL-V1-FOOT", "v1.0", "Footwear", 14, 0.0, 50000.0, "14-day return window. No restocking fee if unworn with original box tags.", 1),
        ("POL-V1-HOME", "v1.0", "Home & Kitchen", 30, 0.0, 50000.0, "30-day return window. Items must be undamaged in original packaging.", 1),
        ("POL-V1-COMP", "v1.0", "Computers", 7, 10.0, 50000.0, "7-day return window. Physical screen damage not covered under manufacturer warranty.", 1),
    ]
    cursor.executemany("INSERT INTO policies VALUES (?, ?, ?, ?, ?, ?, ?, ?)", policies)

    # Seed Conversations (Context continuity from Page 14)
    conversations = [
        ("CUST-101", "user", "My laptop screen is broken.", "2026-10-02 14:20:00"),
        ("CUST-101", "assistant", "I'm sorry to hear that. Could you share a photo so I can verify the damage type?", "2026-10-02 14:21:00"),
        ("CUST-101", "user", "*(image sent)* photo_screen_crack_dell_xps.jpg", "2026-10-02 14:22:00"),
        ("CUST-101", "assistant", "Thank you. We have logged the photo of the screen damage in our records.", "2026-10-02 14:22:30"),
        ("CUST-106", "user", "When will my order NM-1101 arrive?", "2026-09-23 10:00:00"),
        ("CUST-106", "assistant", "Order NM-1101 is scheduled for delivery on Sep 24.", "2026-09-23 10:00:20"),
    ]
    cursor.executemany("INSERT INTO conversations (customer_id, role, message, timestamp) VALUES (?, ?, ?, ?)", conversations)

    conn.commit()
    conn.close()
    print("Database novamart.db initialized and seeded successfully.")

if __name__ == "__main__":
    init_db()
