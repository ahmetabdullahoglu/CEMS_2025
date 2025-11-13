-- Update Role Permissions SQL Script
-- Run this to update existing roles with the latest permissions

-- Update Admin Role Permissions
UPDATE roles
SET permissions = ARRAY[
    -- User Management
    'users:create', 'users:read', 'users:update', 'users:delete',
    'users:assign_roles', 'users:manage_permissions',

    -- Branch Management
    'branches:create', 'branches:read', 'branches:update', 'branches:delete',
    'branches:assign_users', 'branches:view_all', 'branches:manage_balances',

    -- Currency Management
    'currencies:create', 'currencies:read', 'currencies:update', 'currencies:delete',
    'currencies:set_rates', 'currencies:view_rates', 'currencies:manage_rates',

    -- Transaction Management
    'transactions:create', 'transactions:read', 'transactions:update',
    'transactions:delete', 'transactions:approve', 'transactions:cancel',
    'transactions:view_all',

    -- Vault Management (UPDATED!)
    'vault:create', 'vault:read', 'vault:update', 'vault:transfer',
    'vault:approve', 'vault:receive', 'vault:cancel',
    'vault:view_balances', 'vault:adjust_balance', 'vault:reconcile',

    -- Reports
    'reports:view_branch', 'reports:view_all', 'reports:export',
    'reports:generate', 'reports:schedule',

    -- Customer Management
    'customers:create', 'customers:read', 'customers:update', 'customers:delete',
    'customers:verify', 'customers:view_all',

    -- Document Management
    'documents:upload', 'documents:read', 'documents:update', 'documents:delete',
    'documents:verify', 'documents:download',

    -- System Management
    'system:view_logs', 'system:manage_settings', 'system:backup',
    'system:restore', 'system:maintenance'
],
description = 'Full system access with all permissions'
WHERE name = 'admin';

-- Update Manager Role Permissions
UPDATE roles
SET permissions = ARRAY[
    -- User Management (limited)
    'users:read',

    -- Branch Management
    'branches:read', 'branches:update', 'branches:assign_users',
    'branches:view_own', 'branches:manage_balances',

    -- Currency Management
    'currencies:read', 'currencies:set_rates', 'currencies:view_rates',

    -- Transaction Management
    'transactions:create', 'transactions:read', 'transactions:update',
    'transactions:approve', 'transactions:cancel', 'transactions:view_branch',

    -- Vault Management (UPDATED!)
    'vault:read', 'vault:transfer', 'vault:approve', 'vault:receive',
    'vault:cancel', 'vault:view_balances', 'vault:adjust_balance', 'vault:reconcile',

    -- Reports
    'reports:view_branch', 'reports:export', 'reports:generate',

    -- Customer Management
    'customers:create', 'customers:read', 'customers:update',
    'customers:verify', 'customers:view_branch',

    -- Document Management
    'documents:upload', 'documents:read', 'documents:update',
    'documents:verify', 'documents:download'
],
description = 'Branch-level management with approval capabilities'
WHERE name = 'manager';

-- Update Teller Role Permissions
UPDATE roles
SET permissions = ARRAY[
    -- Currency Management (read only)
    'currencies:read', 'currencies:view_rates',

    -- Transaction Management
    'transactions:create', 'transactions:read', 'transactions:view_own',

    -- Reports
    'reports:view_branch',

    -- Customer Management
    'customers:create', 'customers:read', 'customers:view_branch',

    -- Document Management
    'documents:upload', 'documents:read'
],
description = 'Front-desk operations with limited permissions'
WHERE name = 'teller';

-- Verify the updates
SELECT
    name,
    display_name_ar,
    array_length(permissions, 1) as permission_count,
    CASE
        WHEN 'vault:approve' = ANY(permissions) THEN 'YES'
        ELSE 'NO'
    END as has_vault_approve
FROM roles
ORDER BY name;
