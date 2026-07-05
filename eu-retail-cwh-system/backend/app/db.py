import sqlite3
from datetime import datetime
from pathlib import Path
from flask import g, current_app


def get_db():
    """物流看板数据库 (shipments)"""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db


def get_wms_db():
    """WMS 库存数据库"""
    if 'wms_db' not in g:
        g.wms_db = sqlite3.connect(current_app.config['WMS_DATABASE'])
        g.wms_db.row_factory = sqlite3.Row
        g.wms_db.execute("PRAGMA journal_mode=WAL")
        g.wms_db.execute("PRAGMA foreign_keys=ON")
    return g.wms_db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
    wms_db = g.pop('wms_db', None)
    if wms_db is not None:
        wms_db.close()


def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def backup_sqlite_db(db_path, label):
    """Create a point-in-time SQLite backup before a data-changing operation."""
    source_path = Path(db_path)
    if not source_path.exists():
        return None

    backup_dir = source_path.parent / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)

    safe_label = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in label)[:40]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = backup_dir / f"{source_path.stem}_{safe_label}_{timestamp}.db"

    src = sqlite3.connect(str(source_path))
    try:
        dst = sqlite3.connect(str(backup_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()

    return str(backup_path)


# ========== Shipments Schema ==========
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS shipments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT NOT NULL,
    stt_number TEXT,
    waybill_no TEXT,
    shipment_status TEXT,
    transport_mode TEXT,
    shipment_type TEXT,
    warehouse TEXT,
    shipper_name TEXT,
    consignee_name TEXT,
    consignee_name2 TEXT,
    consignee_street TEXT,
    consignee_street2 TEXT,
    consignee_address TEXT,
    consignee_city TEXT,
    consignee_country_code TEXT,
    demand_country TEXT,
    demand_country_source TEXT DEFAULT 'default',
    pickup_city TEXT,
    pickup_country_code TEXT,
    delivery_city TEXT,
    delivery_country_code TEXT,
    creation_date TEXT,
    pickup_date TEXT,
    delivery_date TEXT,
    actual_delivery_date TEXT,
    delivery_locked INTEGER DEFAULT 0,
    manual_status TEXT DEFAULT NULL,
    last_checked TEXT,
    total_pieces REAL,
    total_weight REAL,
    total_volume REAL,
    price_without_vat REAL,
    incoterm TEXT,
    service_type TEXT,
    product TEXT,
    cargo_description TEXT,
    references_text TEXT,
    source_file TEXT,
    recycled_at TEXT,
    recycle_reason TEXT,
    recycle_operator TEXT,
    import_time TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(booking_id)
);

CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(shipment_status);
CREATE INDEX IF NOT EXISTS idx_shipments_type ON shipments(shipment_type);
CREATE INDEX IF NOT EXISTS idx_shipments_country ON shipments(consignee_country_code);
CREATE INDEX IF NOT EXISTS idx_shipments_creation ON shipments(creation_date);
CREATE INDEX IF NOT EXISTS idx_shipments_warehouse ON shipments(warehouse);

-- ========== Invoice Schema ==========
CREATE TABLE IF NOT EXISTS invoice_headers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number TEXT NOT NULL UNIQUE,
    invoice_date TEXT,
    invoice_type TEXT DEFAULT 'logistics',
    currency TEXT DEFAULT 'PLN',
    total_net REAL DEFAULT 0,
    total_vat REAL DEFAULT 0,
    total_gross REAL DEFAULT 0,
    status TEXT DEFAULT 'pending',
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id INTEGER NOT NULL,
    stt_number TEXT NOT NULL,
    net_amount REAL DEFAULT 0,
    ref_date TEXT,
    matched_booking_id TEXT,
    accepted_amount REAL,
    acceptance_status TEXT,
    exception_reason TEXT,
    acceptance_remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (invoice_id) REFERENCES invoice_headers(id)
);

CREATE INDEX IF NOT EXISTS idx_invoice_items_stt ON invoice_items(stt_number);
CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);
"""


def init_db(app):
    db_path = app.config['DATABASE']
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_SQL)
    # 增量迁移：添加新字段（不影响已有数据）
    new_cols = ['consignee_name2 TEXT', 'consignee_street TEXT', 'consignee_street2 TEXT',
                'last_checked TEXT', 'manual_status TEXT DEFAULT NULL',
                'recycled_at TEXT', 'recycle_reason TEXT', 'recycle_operator TEXT',
                'demand_country TEXT', "demand_country_source TEXT DEFAULT 'default'"]
    cur = conn.cursor()
    existing = [r[1] for r in cur.execute("PRAGMA table_info(shipments)").fetchall()]
    for col_def in new_cols:
        col_name = col_def.split()[0]
        if col_name not in existing:
            cur.execute(f"ALTER TABLE shipments ADD COLUMN {col_def}")
    invoice_item_cols = [r[1] for r in cur.execute("PRAGMA table_info(invoice_items)").fetchall()]
    for col_def in [
        "accepted_amount REAL",
        "acceptance_status TEXT",
        "exception_reason TEXT",
        "acceptance_remark TEXT",
    ]:
        col_name = col_def.split()[0]
        if col_name not in invoice_item_cols:
            cur.execute(f"ALTER TABLE invoice_items ADD COLUMN {col_def}")
    cur.execute("""
        UPDATE shipments
        SET demand_country = UPPER(TRIM(consignee_country_code)),
            demand_country_source = COALESCE(NULLIF(demand_country_source, ''), 'default')
        WHERE (demand_country IS NULL OR TRIM(demand_country) = '')
          AND consignee_country_code IS NOT NULL
          AND TRIM(consignee_country_code) != ''
    """)
    cur.execute("""
        UPDATE shipments
        SET shipment_status = 'Active'
        WHERE shipment_status IS NULL OR TRIM(shipment_status) = ''
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_shipments_demand_country ON shipments(demand_country)")
    conn.commit()
    conn.close()


# ========== WMS Schema ==========
WMS_SCHEMA = """
CREATE TABLE IF NOT EXISTS sku_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bom_code TEXT UNIQUE NOT NULL,
    product_number TEXT,
    product_description TEXT,
    category TEXT,
    category_2 TEXT,
    unit_price REAL DEFAULT 0,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_number TEXT UNIQUE NOT NULL,
    bom_code TEXT NOT NULL,
    product_description TEXT,
    category TEXT,
    category_2 TEXT,
    unit_price REAL DEFAULT 0,
    last_inbound_date DATE,
    last_outbound_date DATE,
    remark TEXT,
    dos_threshold INTEGER DEFAULT 180,
    idle_threshold INTEGER DEFAULT 180,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS warehouse_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse TEXT NOT NULL,
    bom_code TEXT NOT NULL,
    product_number TEXT,
    instruction TEXT,
    inventory INTEGER DEFAULT 0,
    last_inbound_date DATE,
    last_outbound_date DATE,
    comment TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(warehouse, product_number)
);

CREATE TABLE IF NOT EXISTS delivery_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    warehouse TEXT NOT NULL,
    destination_country TEXT,
    status TEXT DEFAULT 'pending',
    stt_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    shipped_at TIMESTAMP,
    delivered_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS delivery_order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    bom_code TEXT NOT NULL,
    product_number TEXT,
    requested_qty INTEGER DEFAULT 0,
    actual_qty INTEGER,
    FOREIGN KEY (order_id) REFERENCES delivery_orders(id)
);

CREATE TABLE IF NOT EXISTS inventory_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    warehouse TEXT NOT NULL,
    bom_code TEXT NOT NULL,
    product_number TEXT,
    change_type TEXT NOT NULL,
    quantity_change INTEGER NOT NULL,
    order_id INTEGER,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    movement_type TEXT NOT NULL,
    sheet_name TEXT,
    product_number TEXT NOT NULL,
    movement_date DATE,
    operation_id TEXT,
    operation_prefix TEXT,
    operation_target TEXT,
    order_date DATE,
    quantity REAL DEFAULT 0,
    uom TEXT,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sku_category ON sku_master(category);
CREATE INDEX IF NOT EXISTS idx_sku_category2 ON sku_master(category_2);
CREATE INDEX IF NOT EXISTS idx_product_bom ON product_master(bom_code);
CREATE INDEX IF NOT EXISTS idx_product_category ON product_master(category);
CREATE INDEX IF NOT EXISTS idx_product_category2 ON product_master(category_2);
CREATE INDEX IF NOT EXISTS idx_inv_warehouse ON warehouse_inventory(warehouse);
CREATE INDEX IF NOT EXISTS idx_inv_bom ON warehouse_inventory(bom_code);
CREATE INDEX IF NOT EXISTS idx_orders_status ON delivery_orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_stt ON delivery_orders(stt_number);
CREATE INDEX IF NOT EXISTS idx_items_order ON delivery_order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_txn_warehouse ON inventory_transactions(warehouse);
CREATE INDEX IF NOT EXISTS idx_txn_bom ON inventory_transactions(bom_code);
CREATE INDEX IF NOT EXISTS idx_movements_product ON inventory_movements(product_number);
CREATE INDEX IF NOT EXISTS idx_movements_date ON inventory_movements(movement_date);
"""


def init_wms_db(app):
    conn = sqlite3.connect(app.config['WMS_DATABASE'])
    pre_cur = conn.cursor()

    def pre_table_exists(table):
        return pre_cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

    def pre_table_cols(table):
        if not pre_table_exists(table):
            return []
        return [r[1] for r in pre_cur.execute(f"PRAGMA table_info({table})").fetchall()]

    def pre_ensure_columns(table, columns):
        if not pre_table_exists(table):
            return
        existing_cols = pre_table_cols(table)
        for col_name, col_type in columns:
            if col_name not in existing_cols:
                pre_cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                existing_cols.append(col_name)

    # Old PC databases may have early VN tables without these columns. Add them
    # before running WMS_SCHEMA, because CREATE INDEX statements reference them.
    pre_ensure_columns("sku_master", (
        ("product_number", "TEXT"),
        ("product_description", "TEXT"),
        ("category", "TEXT"),
        ("category_2", "TEXT"),
        ("unit_price", "REAL DEFAULT 0"),
        ("image_path", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    pre_ensure_columns("product_master", (
        ("bom_code", "TEXT"),
        ("product_description", "TEXT"),
        ("category", "TEXT"),
        ("category_2", "TEXT"),
        ("unit_price", "REAL DEFAULT 0"),
        ("last_inbound_date", "DATE"),
        ("last_outbound_date", "DATE"),
        ("remark", "TEXT"),
        ("dos_threshold", "INTEGER DEFAULT 180"),
        ("idle_threshold", "INTEGER DEFAULT 180"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    pre_ensure_columns("warehouse_inventory", (
        ("bom_code", "TEXT"),
        ("product_number", "TEXT"),
        ("instruction", "TEXT"),
        ("inventory", "INTEGER DEFAULT 0"),
        ("last_inbound_date", "DATE"),
        ("last_outbound_date", "DATE"),
        ("comment", "TEXT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    pre_ensure_columns("delivery_orders", (
        ("destination_country", "TEXT"),
        ("status", "TEXT DEFAULT 'pending'"),
        ("stt_number", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("confirmed_at", "TIMESTAMP"),
        ("shipped_at", "TIMESTAMP"),
        ("delivered_at", "TIMESTAMP"),
    ))
    pre_ensure_columns("delivery_order_items", (("product_number", "TEXT"),))
    pre_ensure_columns("inventory_transactions", (("product_number", "TEXT"),))
    pre_ensure_columns("inventory_movements", (
        ("movement_type", "TEXT"),
        ("sheet_name", "TEXT"),
        ("product_number", "TEXT"),
        ("movement_date", "DATE"),
        ("operation_id", "TEXT"),
        ("operation_prefix", "TEXT"),
        ("operation_target", "TEXT"),
        ("order_date", "DATE"),
        ("quantity", "REAL DEFAULT 0"),
        ("uom", "TEXT"),
        ("source_file", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    conn.commit()
    conn.executescript(WMS_SCHEMA)
    cur = conn.cursor()

    def table_cols(table):
        return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]

    def ensure_columns(table, columns):
        existing_cols = table_cols(table)
        for col_name, col_type in columns:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                existing_cols.append(col_name)

    ensure_columns("sku_master", (
        ("product_number", "TEXT"),
        ("product_description", "TEXT"),
        ("category", "TEXT"),
        ("category_2", "TEXT"),
        ("unit_price", "REAL DEFAULT 0"),
        ("image_path", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    ensure_columns("product_master", (
        ("bom_code", "TEXT"),
        ("product_description", "TEXT"),
        ("category", "TEXT"),
        ("category_2", "TEXT"),
        ("unit_price", "REAL DEFAULT 0"),
        ("last_inbound_date", "DATE"),
        ("last_outbound_date", "DATE"),
        ("remark", "TEXT"),
        ("dos_threshold", "INTEGER DEFAULT 180"),
        ("idle_threshold", "INTEGER DEFAULT 180"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))
    ensure_columns("warehouse_inventory", (
        ("bom_code", "TEXT"),
        ("product_number", "TEXT"),
        ("instruction", "TEXT"),
        ("inventory", "INTEGER DEFAULT 0"),
        ("last_inbound_date", "DATE"),
        ("last_outbound_date", "DATE"),
        ("comment", "TEXT"),
        ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ))

    for table in ("warehouse_inventory", "delivery_order_items", "inventory_transactions"):
        if "product_number" not in table_cols(table):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN product_number TEXT")

    product_cols = table_cols("product_master")
    for col_name, col_type in (
        ("last_inbound_date", "DATE"),
        ("last_outbound_date", "DATE"),
        ("remark", "TEXT"),
    ):
        if col_name not in product_cols:
            cur.execute(f"ALTER TABLE product_master ADD COLUMN {col_name} {col_type}")

    cur.execute("""
        UPDATE warehouse_inventory
        SET product_number = COALESCE(NULLIF(product_number, ''), (
            SELECT product_number FROM sku_master sm
            WHERE sm.bom_code = warehouse_inventory.bom_code
              AND NOT (
                REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(warehouse_inventory.bom_code, ''))), ' ', ''), '_', ''), '-', '') IN ('本地', 'LOCAL', 'LOCALSKU', 'LOCALITEM', '/', 'NOBOM', 'NOBOMCODE')
                OR COALESCE(NULLIF(warehouse_inventory.bom_code, ''), '') = ''
              )
        ), bom_code)
        WHERE product_number IS NULL OR product_number = ''
    """)
    cur.execute("""
        UPDATE delivery_order_items
        SET product_number = COALESCE(NULLIF(product_number, ''), (
            SELECT product_number FROM sku_master sm
            WHERE sm.bom_code = delivery_order_items.bom_code
              AND NOT (
                REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(delivery_order_items.bom_code, ''))), ' ', ''), '_', ''), '-', '') IN ('本地', 'LOCAL', 'LOCALSKU', 'LOCALITEM', '/', 'NOBOM', 'NOBOMCODE')
                OR COALESCE(NULLIF(delivery_order_items.bom_code, ''), '') = ''
              )
        ), bom_code)
        WHERE product_number IS NULL OR product_number = ''
    """)
    cur.execute("""
        UPDATE inventory_transactions
        SET product_number = COALESCE(NULLIF(product_number, ''), (
            SELECT product_number FROM sku_master sm
            WHERE sm.bom_code = inventory_transactions.bom_code
              AND NOT (
                REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(inventory_transactions.bom_code, ''))), ' ', ''), '_', ''), '-', '') IN ('本地', 'LOCAL', 'LOCALSKU', 'LOCALITEM', '/', 'NOBOM', 'NOBOMCODE')
                OR COALESCE(NULLIF(inventory_transactions.bom_code, ''), '') = ''
              )
        ), bom_code)
        WHERE product_number IS NULL OR product_number = ''
    """)

    cur.execute("""
        INSERT INTO product_master (product_number, bom_code, product_description, category, category_2, unit_price, updated_at)
        SELECT DISTINCT
               COALESCE(NULLIF(wi.product_number, ''), NULLIF(sm.product_number, ''), wi.bom_code) AS product_number,
               wi.bom_code,
               sm.product_description,
               UPPER(TRIM(COALESCE(sm.category, ''))) AS category,
               UPPER(TRIM(COALESCE(sm.category_2, ''))) AS category_2,
               COALESCE(sm.unit_price, 0),
               CURRENT_TIMESTAMP
        FROM warehouse_inventory wi
        LEFT JOIN sku_master sm ON wi.bom_code = sm.bom_code
            AND NOT (
                REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(wi.bom_code, ''))), ' ', ''), '_', ''), '-', '') IN ('本地', 'LOCAL', 'LOCALSKU', 'LOCALITEM', '/', 'NOBOM', 'NOBOMCODE')
                OR COALESCE(NULLIF(wi.bom_code, ''), '') = ''
            )
        WHERE COALESCE(NULLIF(wi.product_number, ''), NULLIF(sm.product_number, ''), wi.bom_code) IS NOT NULL
        ON CONFLICT(product_number) DO UPDATE SET
            bom_code=excluded.bom_code,
            product_description=COALESCE(excluded.product_description, product_description),
            category=COALESCE(NULLIF(excluded.category, ''), category),
            category_2=COALESCE(NULLIF(excluded.category_2, ''), category_2),
            unit_price=CASE
                WHEN COALESCE(excluded.unit_price, 0) > 0 THEN excluded.unit_price
                ELSE unit_price
            END,
            updated_at=CURRENT_TIMESTAMP
    """)
    category_compact = "REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(category, ''))), ' ', ''), '_', ''), '-', '')"
    category2_compact = "REPLACE(REPLACE(REPLACE(UPPER(TRIM(COALESCE(category_2, ''))), ' ', ''), '_', ''), '-', '')"
    for table in ("product_master", "sku_master"):
        cur.execute(f"""
            UPDATE {table}
            SET category_2 = CASE
                WHEN {category2_compact} IN ('ADUIO', 'AUDIO') THEN 'AUDIO'
                WHEN {category2_compact} = 'IOT' THEN 'IOT'
                WHEN {category2_compact} = 'OTHER' THEN 'OTHER'
                WHEN {category2_compact} = 'PHONE' THEN 'PHONE'
                WHEN {category2_compact} = 'TABLET' THEN 'TABLET'
                WHEN {category2_compact} = 'WEARABLE' THEN 'WEARABLE'
                ELSE UPPER(TRIM(COALESCE(category_2, '')))
            END,
            category = CASE
                WHEN {category_compact} = 'ACRYLICPROP' THEN 'ACRYLIC PROP'
                WHEN {category_compact} = 'DUMMY' THEN 'DUMMY'
                WHEN {category_compact} = 'FURNITURE' THEN 'FURNITURE'
                WHEN {category_compact} = 'GIFT' THEN 'GIFT'
                WHEN {category_compact} = 'PROP' THEN 'PROP'
                WHEN {category_compact} = 'SECURITYSYSTEM' THEN 'SECURITY SYSTEM'
                WHEN {category_compact} IN ('TOOLS/ACCESSORIES', 'TOOLSACCESSORIES', 'TOOLACCESSORIES') THEN 'TOOLS/ACCESSORIES'
                WHEN {category_compact} = 'TRAININGMATERIALS' THEN 'TRAINING MATERIALS'
                WHEN {category_compact} = 'UNIFORM' THEN 'UNIFORM'
                WHEN {category_compact} = 'WOODENOVERLAY' THEN 'WOODEN OVERLAY'
                ELSE UPPER(TRIM(COALESCE(category, '')))
            END
        """)
    cur.execute("UPDATE warehouse_inventory SET instruction = UPPER(TRIM(COALESCE(instruction, '')))")
    cur.execute("""
        UPDATE product_master
        SET last_outbound_date = last_inbound_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE (last_outbound_date IS NULL OR TRIM(last_outbound_date) = '')
          AND last_inbound_date IS NOT NULL
          AND TRIM(last_inbound_date) != ''
    """)
    cur.execute("""
        UPDATE warehouse_inventory
        SET last_outbound_date = last_inbound_date,
            updated_at = CURRENT_TIMESTAMP
        WHERE (last_outbound_date IS NULL OR TRIM(last_outbound_date) = '')
          AND last_inbound_date IS NOT NULL
          AND TRIM(last_inbound_date) != ''
    """)
    cur.execute("""
        UPDATE product_master
        SET unit_price = (
            SELECT sm.unit_price
            FROM sku_master sm
            WHERE sm.product_number = product_master.product_number
              AND COALESCE(sm.unit_price, 0) > 0
            ORDER BY sm.updated_at DESC
            LIMIT 1
        ),
            updated_at = CURRENT_TIMESTAMP
        WHERE COALESCE(product_master.unit_price, 0) <= 0
          AND EXISTS (
            SELECT 1
            FROM sku_master sm
            WHERE sm.product_number = product_master.product_number
              AND COALESCE(sm.unit_price, 0) > 0
          )
    """)
    cur.execute("""
        UPDATE sku_master
        SET unit_price = (
            SELECT pm.unit_price
            FROM product_master pm
            WHERE pm.product_number = sku_master.product_number
              AND COALESCE(pm.unit_price, 0) > 0
            ORDER BY pm.updated_at DESC
            LIMIT 1
        ),
            updated_at = CURRENT_TIMESTAMP
        WHERE COALESCE(sku_master.unit_price, 0) <= 0
          AND EXISTS (
            SELECT 1
            FROM product_master pm
            WHERE pm.product_number = sku_master.product_number
              AND COALESCE(pm.unit_price, 0) > 0
          )
    """)

    table_sql = cur.execute("""
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = 'warehouse_inventory'
    """).fetchone()
    if table_sql and "UNIQUE(warehouse, bom_code)" in (table_sql[0] or ""):
        cur.execute("""
            CREATE TABLE IF NOT EXISTS warehouse_inventory_vn11 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse TEXT NOT NULL,
                bom_code TEXT NOT NULL,
                product_number TEXT NOT NULL,
                instruction TEXT,
                inventory INTEGER DEFAULT 0,
                last_inbound_date DATE,
                last_outbound_date DATE,
                comment TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(warehouse, product_number)
            )
        """)
        rows = cur.execute("""
            SELECT wi.id, wi.warehouse, wi.bom_code,
                   COALESCE(NULLIF(wi.product_number, ''), NULLIF(sm.product_number, ''), wi.bom_code) AS product_number,
                   wi.instruction, wi.inventory, wi.last_inbound_date, wi.last_outbound_date, wi.comment, wi.updated_at
            FROM warehouse_inventory wi
            LEFT JOIN sku_master sm ON wi.bom_code = sm.bom_code
            ORDER BY COALESCE(wi.updated_at, ''), wi.id
        """).fetchall()
        for row in rows:
            cur.execute("""
                INSERT INTO warehouse_inventory_vn11
                    (warehouse, bom_code, product_number, instruction, inventory, last_inbound_date, last_outbound_date, comment, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(warehouse, product_number) DO UPDATE SET
                    bom_code=excluded.bom_code,
                    instruction=excluded.instruction,
                    inventory=excluded.inventory,
                    last_inbound_date=excluded.last_inbound_date,
                    last_outbound_date=excluded.last_outbound_date,
                    comment=excluded.comment,
                    updated_at=excluded.updated_at
            """, row[1:])
        cur.execute("DROP TABLE warehouse_inventory")
        cur.execute("ALTER TABLE warehouse_inventory_vn11 RENAME TO warehouse_inventory")

    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_inv_warehouse ON warehouse_inventory(warehouse);
        CREATE INDEX IF NOT EXISTS idx_inv_bom ON warehouse_inventory(bom_code);
        CREATE INDEX IF NOT EXISTS idx_inv_product_number ON warehouse_inventory(product_number);
        CREATE INDEX IF NOT EXISTS idx_txn_product_number ON inventory_transactions(product_number);
        CREATE INDEX IF NOT EXISTS idx_product_bom ON product_master(bom_code);
        CREATE INDEX IF NOT EXISTS idx_product_category ON product_master(category);
        CREATE INDEX IF NOT EXISTS idx_product_category2 ON product_master(category_2);
    """)
    conn.commit()
    conn.close()
