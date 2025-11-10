# CEMS Frontend Development Roadmap
## خارطة طريق تطوير واجهة المستخدم لنظام CEMS

**Version:** 1.0
**Last Updated:** 2025-11-10
**Backend API:** http://localhost:8000/api/v1
**API Documentation:** http://localhost:8000/docs

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Technology Stack Recommendations](#technology-stack)
3. [Project Structure](#project-structure)
4. [Phase-by-Phase Implementation](#phases)
5. [API Integration Guide](#api-integration)
6. [Authentication Flow](#authentication)
7. [Key Features by Module](#features)
8. [Component Library](#components)
9. [State Management](#state-management)
10. [Deployment Strategy](#deployment)

---

## 1. Project Overview

### نظرة عامة على المشروع

CEMS (Currency Exchange Management System) هو نظام شامل لإدارة الصرافة مع الميزات التالية:

**Core Modules (8 Modules):**
1. ✅ **Authentication & Authorization** - المصادقة والصلاحيات
2. ✅ **User Management** - إدارة المستخدمين
3. ✅ **Branch Management** - إدارة الفروع
4. ✅ **Currency Management** - إدارة العملات وأسعار الصرف
5. ✅ **Customer Management** - إدارة العملاء والوثائق
6. ✅ **Transaction Management** - إدارة المعاملات (4 أنواع)
7. ✅ **Vault Management** - إدارة الخزائن والتحويلات
8. ✅ **Reports & Dashboard** - التقارير والإحصائيات

**API Status:** 98% Production Ready
**CRUD Coverage:** 97%
**Documentation Quality:** 92%

---

## 2. Technology Stack Recommendations

### Recommended Stack (Modern & Scalable):

#### Option A: React + TypeScript (Recommended)
```json
{
  "framework": "React 18+",
  "language": "TypeScript",
  "routing": "React Router v6",
  "state": "TanStack Query (React Query) + Zustand",
  "ui": "Material-UI (MUI) or Ant Design",
  "forms": "React Hook Form + Zod",
  "api": "Axios + OpenAPI TypeScript Generator",
  "charts": "Recharts or ApexCharts",
  "tables": "TanStack Table",
  "date": "date-fns",
  "i18n": "react-i18next (Arabic + English)"
}
```

#### Option B: Vue 3 + TypeScript
```json
{
  "framework": "Vue 3 (Composition API)",
  "language": "TypeScript",
  "routing": "Vue Router 4",
  "state": "Pinia + TanStack Query Vue",
  "ui": "Vuetify or Element Plus",
  "forms": "VeeValidate + Yup",
  "api": "Axios",
  "charts": "Vue-ChartJS",
  "i18n": "vue-i18n"
}
```

#### Option C: Next.js (Full-Stack)
```json
{
  "framework": "Next.js 14+ (App Router)",
  "language": "TypeScript",
  "state": "TanStack Query + Zustand",
  "ui": "shadcn/ui + Tailwind CSS",
  "forms": "React Hook Form + Zod",
  "auth": "NextAuth.js",
  "api": "Server Actions + Axios"
}
```

### Our Recommendation: **React + TypeScript + MUI**

**Why?**
- ✅ Best ecosystem for enterprise applications
- ✅ Excellent TypeScript support
- ✅ MUI provides RTL support (Arabic)
- ✅ Large community and resources
- ✅ Easy to generate TypeScript types from OpenAPI

---

## 3. Project Structure

### Recommended Folder Structure:

```
cems-frontend/
├── public/
│   ├── locales/           # i18n translations
│   │   ├── ar.json
│   │   └── en.json
│   └── assets/
├── src/
│   ├── api/               # API client & generated types
│   │   ├── client.ts      # Axios instance
│   │   ├── generated/     # OpenAPI generated types
│   │   └── endpoints/     # API endpoint functions
│   │       ├── auth.ts
│   │       ├── users.ts
│   │       ├── branches.ts
│   │       ├── currencies.ts
│   │       ├── customers.ts
│   │       ├── transactions.ts
│   │       ├── vault.ts
│   │       └── reports.ts
│   ├── components/        # Reusable components
│   │   ├── common/        # Generic components
│   │   │   ├── DataTable/
│   │   │   ├── FormField/
│   │   │   ├── StatusBadge/
│   │   │   └── SearchBar/
│   │   ├── layout/
│   │   │   ├── AppBar/
│   │   │   ├── Sidebar/
│   │   │   └── Footer/
│   │   └── modules/       # Module-specific components
│   │       ├── auth/
│   │       ├── users/
│   │       ├── branches/
│   │       ├── currencies/
│   │       ├── customers/
│   │       ├── transactions/
│   │       ├── vault/
│   │       └── reports/
│   ├── pages/             # Page components
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Users/
│   │   ├── Branches/
│   │   ├── Currencies/
│   │   ├── Customers/
│   │   ├── Transactions/
│   │   ├── Vault/
│   │   └── Reports/
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── usePermissions.ts
│   │   ├── useUsers.ts
│   │   ├── useBranches.ts
│   │   └── ...
│   ├── store/             # Global state (Zustand)
│   │   ├── authStore.ts
│   │   ├── uiStore.ts
│   │   └── settingsStore.ts
│   ├── utils/             # Utility functions
│   │   ├── formatters.ts  # Date, number, currency formatting
│   │   ├── validators.ts  # Form validators
│   │   └── permissions.ts # Permission checks
│   ├── types/             # TypeScript types
│   │   └── index.ts
│   ├── config/            # App configuration
│   │   └── constants.ts
│   ├── i18n/              # i18n configuration
│   │   └── config.ts
│   ├── App.tsx
│   └── main.tsx
├── tests/
├── .env.example
├── package.json
├── tsconfig.json
└── vite.config.ts
```

---

## 4. Phase-by-Phase Implementation

### Phase 1: Project Setup & Authentication (Week 1)

#### Tasks:
1. **Setup Project**
   ```bash
   npm create vite@latest cems-frontend -- --template react-ts
   cd cems-frontend
   npm install
   ```

2. **Install Core Dependencies**
   ```bash
   npm install @mui/material @emotion/react @emotion/styled
   npm install react-router-dom
   npm install @tanstack/react-query
   npm install zustand
   npm install axios
   npm install react-hook-form zod @hookform/resolvers
   npm install react-i18next i18next
   npm install date-fns
   ```

3. **Generate API Types**
   ```bash
   npm install -D openapi-typescript-codegen
   npx openapi-typescript-codegen --input http://localhost:8000/openapi.json --output ./src/api/generated
   ```

4. **Setup API Client** (`src/api/client.ts`)
   ```typescript
   import axios from 'axios';

   const apiClient = axios.create({
     baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
     timeout: 30000,
   });

   // Request interceptor (add auth token)
   apiClient.interceptors.request.use((config) => {
     const token = localStorage.getItem('access_token');
     if (token) {
       config.headers.Authorization = `Bearer ${token}`;
     }
     return config;
   });

   // Response interceptor (handle errors)
   apiClient.interceptors.response.use(
     (response) => response,
     async (error) => {
       if (error.response?.status === 401) {
         // Handle token refresh
       }
       return Promise.reject(error);
     }
   );

   export default apiClient;
   ```

5. **Implement Authentication**
   - Login page
   - Token management
   - Protected routes
   - Auto token refresh

#### Deliverables:
- ✅ Project setup complete
- ✅ API client configured
- ✅ Login/Logout working
- ✅ Protected routes

---

### Phase 2: Core Layout & Navigation (Week 1-2)

#### Tasks:
1. **App Layout**
   - Top AppBar (user menu, language switcher)
   - Sidebar (navigation menu)
   - Main content area
   - Breadcrumbs

2. **Navigation Menu Structure**
   ```typescript
   {
     dashboard: { icon: DashboardIcon, path: '/dashboard' },
     users: { icon: PeopleIcon, path: '/users', permission: 'user:read' },
     branches: { icon: BusinessIcon, path: '/branches' },
     currencies: { icon: AttachMoneyIcon, path: '/currencies' },
     customers: { icon: PersonIcon, path: '/customers' },
     transactions: { icon: ReceiptIcon, path: '/transactions' },
     vault: { icon: AccountBalanceIcon, path: '/vault' },
     reports: { icon: BarChartIcon, path: '/reports' },
   }
   ```

3. **i18n Setup** (Arabic + English)

#### Deliverables:
- ✅ Responsive layout
- ✅ Navigation working
- ✅ Language switching
- ✅ Permission-based menu

---

### Phase 3: User Management Module (Week 2)

#### Features:
1. **Users List Page**
   - Data table with pagination
   - Search (name, email, username)
   - Filters (active status, branch)
   - Actions (edit, view, deactivate)

2. **Create User Form**
   - Form validation (React Hook Form + Zod)
   - Role selection
   - Branch assignment
   - Password strength indicator

3. **User Details Page**
   - View user info
   - Edit user
   - Change password
   - Activity log

#### API Endpoints Used:
```typescript
GET /users              // List users
GET /users/{id}         // Get user
POST /users             // Create user
PUT /users/{id}         // Update user
POST /users/{id}/change-password
POST /users/{id}/deactivate
```

#### Deliverables:
- ✅ Users CRUD complete
- ✅ Search & filters working
- ✅ Form validation working

---

### Phase 4: Branch Management Module (Week 3)

#### Features:
1. **Branches List**
   - Cards or table view
   - Filter by region, active status
   - Show balances summary

2. **Branch Details**
   - Branch info
   - Balance by currency
   - Users assigned
   - Alerts
   - Balance history

3. **Branch Operations**
   - Assign/remove users
   - Reconcile balances
   - Resolve alerts

#### API Endpoints:
```typescript
GET /branches
GET /branches/{id}
GET /branches/{id}/balances
GET /branches/{id}/users
POST /branches/{id}/balances/{currency_id}/reconcile
```

---

### Phase 5: Currency Management Module (Week 3-4)

#### Features:
1. **Currencies List**
   - Active currencies
   - Exchange rates matrix

2. **Exchange Rate Management**
   - Set/update rates
   - Rate history chart
   - Rate calculator

3. **Currency Operations**
   - Add new currency
   - Activate/deactivate
   - Rate alerts

---

### Phase 6: Customer Management Module (Week 4-5)

#### Features:
1. **Customer Search & List**
   - Advanced search (name, phone, ID)
   - Filters (type, risk, verified)
   - Pagination

2. **Customer Profile**
   - Personal information
   - KYC status
   - Documents (upload, view, verify)
   - Notes
   - Transaction history

3. **KYC Workflow**
   - Document upload
   - Verification process
   - Risk assessment

---

### Phase 7: Transaction Management Module (Week 5-6)

#### Features:
1. **Transaction List**
   - Filter by type, status, date
   - Search by customer, amount
   - Export to Excel

2. **Create Transaction**
   - Income transaction
   - Expense transaction
   - Exchange transaction (with rate preview)
   - Transfer transaction

3. **Transaction Details**
   - View transaction
   - Cancel transaction
   - Print receipt

---

### Phase 8: Vault Management Module (Week 6-7)

#### Features:
1. **Vault Overview**
   - List all vaults
   - Balance summary
   - Recent transfers

2. **Vault Transfers**
   - Vault to vault
   - Vault to branch
   - Branch to vault
   - Approve/complete transfers

3. **Reconciliation**
   - Compare balances
   - Adjust discrepancies
   - Generate reports

---

### Phase 9: Reports & Dashboard (Week 7-8)

#### Features:
1. **Dashboard**
   - Key metrics (revenue, transactions)
   - Charts (transaction volume, revenue trend)
   - Alerts
   - Recent activity

2. **Reports**
   - Daily summary
   - Monthly revenue
   - Branch performance
   - Exchange trends
   - Export (JSON, Excel, PDF)

3. **Analytics**
   - Currency distribution
   - Branch comparison
   - User activity

---

### Phase 10: Testing & Optimization (Week 8-9)

#### Tasks:
1. **Unit Tests** (Vitest + React Testing Library)
2. **E2E Tests** (Playwright or Cypress)
3. **Performance Optimization**
   - Code splitting
   - Lazy loading
   - Image optimization
4. **Accessibility** (WCAG 2.1)
5. **Security Audit**

---

### Phase 11: Deployment & Documentation (Week 9-10)

#### Tasks:
1. **Build for Production**
   ```bash
   npm run build
   ```
2. **Deploy** (Vercel, Netlify, or Nginx)
3. **User Documentation**
4. **Developer Documentation**
5. **Handover**

---

## 5. API Integration Guide

### Generate TypeScript Types

```bash
# Install generator
npm install -D @openapitools/openapi-generator-cli

# Generate types
npx openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g typescript-axios \
  -o ./src/api/generated
```

### Example API Hook (React Query)

```typescript
// src/hooks/useUsers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getUsers, createUser, updateUser } from '../api/endpoints/users';

export const useUsers = (filters) => {
  return useQuery({
    queryKey: ['users', filters],
    queryFn: () => getUsers(filters),
  });
};

export const useCreateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });
};
```

---

## 6. Authentication Flow

### Login Flow:
```typescript
1. User enters credentials
2. POST /auth/login
3. Receive access_token + refresh_token
4. Store tokens (localStorage or httpOnly cookie)
5. Setup axios interceptor
6. Redirect to dashboard
```

### Token Refresh:
```typescript
// Auto refresh when token expires
if (error.response?.status === 401) {
  const refresh_token = localStorage.getItem('refresh_token');
  const response = await POST('/auth/refresh', { refresh_token });
  localStorage.setItem('access_token', response.data.access_token);
  // Retry original request
}
```

---

## 7. Key Features by Module

### Dashboard Features:
- [ ] Overview cards (revenue, transactions, customers, branches)
- [ ] Transaction volume chart (last 7 days)
- [ ] Revenue trend chart (last 30 days)
- [ ] Currency distribution pie chart
- [ ] Branch comparison bar chart
- [ ] Real-time alerts panel
- [ ] Recent transactions table

### Users Features:
- [ ] List with search & filters
- [ ] Create/Edit user form
- [ ] Role-based permissions
- [ ] Password management
- [ ] Activity log

### Branches Features:
- [ ] Branch list/grid view
- [ ] Balance management
- [ ] User assignment
- [ ] Alert management
- [ ] Reconciliation

### Currencies Features:
- [ ] Currency list
- [ ] Exchange rate matrix
- [ ] Rate calculator
- [ ] Rate history chart
- [ ] Rate alerts

### Customers Features:
- [ ] Advanced search
- [ ] Customer profile
- [ ] Document management
- [ ] KYC verification
- [ ] Notes system
- [ ] Transaction history

### Transactions Features:
- [ ] Transaction list with advanced filters
- [ ] Create transaction wizard
- [ ] Exchange rate preview
- [ ] Transaction details
- [ ] Cancel transaction
- [ ] Print receipt
- [ ] Export to Excel

### Vault Features:
- [ ] Vault list
- [ ] Balance overview
- [ ] Transfer management
- [ ] Approval workflow
- [ ] Reconciliation
- [ ] Transfer history

### Reports Features:
- [ ] Daily summary report
- [ ] Monthly revenue report
- [ ] Branch performance
- [ ] Exchange trends
- [ ] Balance snapshot
- [ ] User activity
- [ ] Audit trail
- [ ] Export (JSON/Excel/PDF)

---

## 8. Component Library

### Common Components to Build:

1. **DataTable Component**
   - Pagination
   - Sorting
   - Filtering
   - Search
   - Actions
   - Export

2. **FormField Components**
   - TextInput
   - NumberInput
   - CurrencyInput
   - DatePicker
   - Select
   - Autocomplete
   - FileUpload
   - Switch

3. **StatusBadge Component**
   - Success (completed, active)
   - Warning (pending)
   - Error (failed, cancelled)
   - Info (in_progress)

4. **ConfirmDialog Component**
   - Delete confirmation
   - Action confirmation

5. **Chart Components**
   - LineChart
   - BarChart
   - PieChart
   - AreaChart

---

## 9. State Management

### Zustand Store Structure:

```typescript
// authStore.ts
interface AuthStore {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (credentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

// uiStore.ts
interface UIStore {
  sidebarOpen: boolean;
  language: 'ar' | 'en';
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setLanguage: (lang) => void;
}
```

### TanStack Query for Server State:
- All API data fetching
- Automatic caching
- Background refetching
- Optimistic updates

---

## 10. Deployment Strategy

### Production Build:

```bash
# Build
npm run build

# Preview
npm run preview

# Deploy
npm run deploy
```

### Environment Variables:

```env
# .env.production
VITE_API_URL=https://api.cems.com/api/v1
VITE_APP_NAME=CEMS
VITE_APP_VERSION=1.0.0
```

### Docker Deployment:

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## 📊 Project Timeline Summary

| Phase | Duration | Effort |
|-------|----------|--------|
| 1. Setup & Auth | 1 week | 40 hours |
| 2. Layout & Navigation | 1 week | 40 hours |
| 3. User Management | 1 week | 40 hours |
| 4. Branch Management | 1 week | 40 hours |
| 5. Currency Management | 1 week | 40 hours |
| 6. Customer Management | 2 weeks | 80 hours |
| 7. Transaction Management | 2 weeks | 80 hours |
| 8. Vault Management | 1 week | 40 hours |
| 9. Reports & Dashboard | 1 week | 40 hours |
| 10. Testing | 1 week | 40 hours |
| 11. Deployment | 1 week | 40 hours |
| **TOTAL** | **~12 weeks** | **480 hours** |

---

## 🎯 Success Criteria

- ✅ All 8 modules fully functional
- ✅ Mobile responsive
- ✅ Arabic & English support (RTL)
- ✅ CRUD operations for all entities
- ✅ Search & filters working
- ✅ Reports & dashboard complete
- ✅ Authentication & authorization
- ✅ Error handling
- ✅ Loading states
- ✅ User-friendly UI/UX

---

## 📚 Resources

### API Documentation:
- **OpenAPI Spec:** http://localhost:8000/openapi.json
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Backend Repository:
- **GitHub:** [CEMS Backend](link-to-repo)
- **API Version:** v1
- **Backend Status:** 98% Production Ready

### Frontend Libraries:
- [React](https://react.dev)
- [Material-UI](https://mui.com)
- [TanStack Query](https://tanstack.com/query)
- [React Hook Form](https://react-hook-form.com)
- [Zod](https://zod.dev)
- [React Router](https://reactrouter.com)

---

## 🚀 Quick Start Command

```bash
# Clone frontend template (when ready)
git clone https://github.com/your-org/cems-frontend
cd cems-frontend

# Install dependencies
npm install

# Configure API URL
cp .env.example .env
# Edit .env: VITE_API_URL=http://localhost:8000/api/v1

# Generate TypeScript types from API
npm run generate-api-types

# Start development server
npm run dev

# Open browser
open http://localhost:5173
```

---

**Last Updated:** 2025-11-10
**Maintainer:** CEMS Development Team
**Questions?** Contact technical team or refer to API documentation

---

**Good Luck Building! 🎉**
