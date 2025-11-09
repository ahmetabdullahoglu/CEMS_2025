-- seed_vault_data.sql
-- Seed Data for Vault Management System
-- Creates initial vault setup for testing

-- ==================== NOTES ====================
-- Run this AFTER:
-- 1. Currency seed data
-- 2. Branch seed data
-- 3. User seed data

-- ==================== CREATE MAIN VAULT ====================

-- Main Central Vault
INSERT INTO vaults (
    id,
    vault_code,
    name,
    vault_type,
    branch_id,
    is_active,
    description,
    location,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'VLT-MAIN',
    'Main Central Vault',
    'main',
    NULL,  -- No branch for main vault
    TRUE,
    'Central vault for all currency reserves',
    'Main Office - Level B2 - Security Room 1',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- ==================== CREATE BRANCH VAULTS ====================

-- Branch 001 Vault (Istanbul European)
INSERT INTO vaults (
    id,
    vault_code,
    name,
    vault_type,
    branch_id,
    is_active,
    description,
    location,
    created_at,
    updated_at
) 
SELECT 
    gen_random_uuid(),
    'VLT-BR001',
    'Branch 001 Vault',
    'branch',
    b.id,
    TRUE,
    'Vault for Istanbul European branch',
    'Branch 001 - Back Office',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM branches b
WHERE b.code = 'BR001'
LIMIT 1;

-- Branch 002 Vault (Istanbul Asian)
INSERT INTO vaults (
    id,
    vault_code,
    name,
    vault_type,
    branch_id,
    is_active,
    description,
    location,
    created_at,
    updated_at
) 
SELECT 
    gen_random_uuid(),
    'VLT-BR002',
    'Branch 002 Vault',
    'branch',
    b.id,
    TRUE,
    'Vault for Istanbul Asian branch',
    'Branch 002 - Back Office',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM branches b
WHERE b.code = 'BR002'
LIMIT 1;

-- Branch 003 Vault (Ankara)
INSERT INTO vaults (
    id,
    vault_code,
    name,
    vault_type,
    branch_id,
    is_active,
    description,
    location,
    created_at,
    updated_at
) 
SELECT 
    gen_random_uuid(),
    'VLT-BR003',
    'Branch 003 Vault',
    'branch',
    b.id,
    TRUE,
    'Vault for Ankara branch',
    'Branch 003 - Back Office',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM branches b
WHERE b.code = 'BR003'
LIMIT 1;

-- ==================== CREATE VAULT BALANCES ====================

-- Main Vault Balances (Initial Reserves)
-- USD Balance
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    500000.00,  -- $500,000
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-MAIN'
  AND c.code = 'USD'
LIMIT 1;

-- EUR Balance
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    400000.00,  -- €400,000
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-MAIN'
  AND c.code = 'EUR'
LIMIT 1;

-- TRY Balance
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    10000000.00,  -- ₺10,000,000
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-MAIN'
  AND c.code = 'TRY'
LIMIT 1;

-- GBP Balance
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    300000.00,  -- £300,000
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-MAIN'
  AND c.code = 'GBP'
LIMIT 1;

-- ==================== BRANCH VAULT BALANCES ====================

-- Branch 001 - Initial balances (small amounts for daily operations)
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    5000.00,  -- $5,000 per currency
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-BR001'
  AND c.code IN ('USD', 'EUR', 'TRY', 'GBP')
  AND c.is_active = TRUE;

-- Branch 002 - Initial balances
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    5000.00,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-BR002'
  AND c.code IN ('USD', 'EUR', 'TRY', 'GBP')
  AND c.is_active = TRUE;

-- Branch 003 - Initial balances
INSERT INTO vault_balances (
    id,
    vault_id,
    currency_id,
    balance,
    last_updated,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    v.id,
    c.id,
    5000.00,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM vaults v
CROSS JOIN currencies c
WHERE v.vault_code = 'VLT-BR003'
  AND c.code IN ('USD', 'EUR', 'TRY', 'GBP')
  AND c.is_active = TRUE;

-- ==================== SAMPLE VAULT TRANSFERS ====================

-- Example transfer: Main vault to Branch 001
INSERT INTO vault_transfers (
    id,
    transfer_number,
    from_vault_id,
    to_vault_id,
    to_branch_id,
    currency_id,
    amount,
    transfer_type,
    status,
    initiated_by,
    approved_by,
    received_by,
    initiated_at,
    approved_at,
    completed_at,
    notes,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    'VTR-20250109-00001',
    v_main.id,
    NULL,  -- Not vault-to-vault
    b.id,  -- To branch
    c.id,
    50000.00,  -- $50,000
    'vault_to_branch',
    'completed',  -- Already completed for seed data
    u.id,  -- Admin user
    u.id,  -- Admin approved
    u.id,  -- Admin received
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    'Initial branch funding - January 2025',
    CURRENT_TIMESTAMP - INTERVAL '2 days',
    CURRENT_TIMESTAMP - INTERVAL '2 days'
FROM vaults v_main
CROSS JOIN branches b
CROSS JOIN currencies c
CROSS JOIN users u
WHERE v_main.vault_code = 'VLT-MAIN'
  AND b.code = 'BR001'
  AND c.code = 'USD'
  AND u.username = 'admin'
LIMIT 1;

-- Example pending transfer: Main vault to Branch 002
INSERT INTO vault_transfers (
    id,
    transfer_number,
    from_vault_id,
    to_vault_id,
    to_branch_id,
    currency_id,
    amount,
    transfer_type,
    status,
    initiated_by,
    initiated_at,
    notes,
    created_at,
    updated_at
)
SELECT 
    gen_random_uuid(),
    'VTR-20250109-00002',
    v_main.id,
    NULL,
    b.id,
    c.id,
    30000.00,  -- €30,000
    'vault_to_branch',
    'pending',  -- Awaiting approval
    u.id,
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    'Branch replenishment request',
    CURRENT_TIMESTAMP - INTERVAL '1 hour',
    CURRENT_TIMESTAMP - INTERVAL '1 hour'
FROM vaults v_main
CROSS JOIN branches b
CROSS JOIN currencies c
CROSS JOIN users u
WHERE v_main.vault_code = 'VLT-MAIN'
  AND b.code = 'BR002'
  AND c.code = 'EUR'
  AND u.username = 'manager_br002'
LIMIT 1;

-- ==================== VERIFICATION QUERIES ====================

-- Verify vaults created
SELECT 
    vault_code,
    name,
    vault_type,
    is_active,
    location
FROM vaults
ORDER BY vault_code;

-- Verify vault balances
SELECT 
    v.vault_code,
    v.name,
    c.code AS currency,
    vb.balance,
    vb.last_updated
FROM vault_balances vb
JOIN vaults v ON vb.vault_id = v.id
JOIN currencies c ON vb.currency_id = c.id
ORDER BY v.vault_code, c.code;

-- Verify vault transfers
SELECT 
    transfer_number,
    v.vault_code AS from_vault,
    b.code AS to_branch,
    c.code AS currency,
    amount,
    status,
    initiated_at
FROM vault_transfers vt
JOIN vaults v ON vt.from_vault_id = v.id
LEFT JOIN branches b ON vt.to_branch_id = b.id
JOIN currencies c ON vt.currency_id = c.id
ORDER BY transfer_number;

-- ==================== SUMMARY ====================

-- Total vault balances summary
SELECT 
    c.code AS currency,
    c.symbol,
    SUM(vb.balance) AS total_balance
FROM vault_balances vb
JOIN currencies c ON vb.currency_id = c.id
GROUP BY c.code, c.symbol
ORDER BY c.code;

-- Vault balances by vault
SELECT 
    v.vault_code,
    v.vault_type,
    COUNT(vb.id) AS currency_count,
    SUM(vb.balance) AS total_balance
FROM vaults v
LEFT JOIN vault_balances vb ON v.id = vb.vault_id
GROUP BY v.vault_code, v.vault_type
ORDER BY v.vault_code;
