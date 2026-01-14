# Skill 08: Admin Dashboard (Next.js)

## Objective
Build a multi-tenant admin dashboard for managing tenants, users, credits, and monitoring calls.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Admin Dashboard (Next.js)                              │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Super Admin Views                                 │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │    │
│  │  │  Tenant   │ │   User    │ │  Credit   │ │  System   │               │    │
│  │  │ Manage    │ │ Manage    │ │ Manage    │ │  Config   │               │    │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Tenant Admin Views                                │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │    │
│  │  │ Dashboard │ │ Call Logs │ │   Users   │ │ Knowledge │               │    │
│  │  │  Stats    │ │  History  │ │   RBAC    │ │   Base    │               │    │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │    │
│  │                                                                          │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐               │    │
│  │  │  Agent    │ │  Phone    │ │ Campaign  │ │  Credit   │               │    │
│  │  │  Config   │ │  Numbers  │ │  Manager  │ │  Usage    │               │    │
│  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Create Next.js Project

```bash
cd ~/voice-ai-platform/src

# Create Next.js app with TypeScript, Tailwind, App Router
npx create-next-app@latest admin-ui --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

cd admin-ui

# Install additional dependencies
pnpm add @tanstack/react-query axios date-fns lucide-react recharts
pnpm add @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs
pnpm add @radix-ui/react-select @radix-ui/react-toast @radix-ui/react-avatar
pnpm add class-variance-authority clsx tailwind-merge
pnpm add -D @types/node
```

---

## Step 2: Project Structure

```bash
mkdir -p src/{components,lib,hooks,types,app}
mkdir -p src/components/{ui,layout,dashboard,tenants,users,calls,credits,kb}
mkdir -p src/app/{(auth),dashboard,tenants,users,calls,credits,settings}
mkdir -p src/app/dashboard/{calls,credits,kb,settings}
```

---

## Step 3: Setup Utility Functions

Create `src/lib/utils.ts`:

```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(amount);
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(date));
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
```

---

## Step 4: API Client

Create `src/lib/api.ts`:

```typescript
// src/lib/api.ts
import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem("refresh_token");
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        
        const { access_token } = response.data;
        localStorage.setItem("access_token", access_token);
        
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.href = "/login";
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API Functions
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  
  me: () => api.get("/auth/me"),
  
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};

export const tenantsApi = {
  list: () => api.get("/tenants"),
  get: (id: string) => api.get(`/tenants/${id}`),
  create: (data: any) => api.post("/tenants", data),
  update: (id: string, data: any) => api.put(`/tenants/${id}`, data),
  delete: (id: string) => api.delete(`/tenants/${id}`),
  addCredits: (id: string, amount: number, notes?: string) =>
    api.post(`/tenants/${id}/credits`, { amount, notes }),
};

export const usersApi = {
  list: () => api.get("/users"),
  get: (id: string) => api.get(`/users/${id}`),
  create: (data: any) => api.post("/users", data),
  update: (id: string, data: any) => api.put(`/users/${id}`, data),
  delete: (id: string) => api.delete(`/users/${id}`),
};

export const callsApi = {
  list: (params?: any) => api.get("/calls", { params }),
  get: (id: string) => api.get(`/calls/${id}`),
  getStats: (params?: any) => api.get("/calls/stats", { params }),
};

export const creditsApi = {
  getBalance: () => api.get("/credits/balance"),
  getTransactions: (params?: any) => api.get("/credits/transactions", { params }),
  getRates: () => api.get("/credits/rates"),
};

export const kbApi = {
  query: (query: string) => api.post("/kb/query", { query }),
  listDocuments: () => api.get("/kb/documents"),
  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/kb/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteDocument: (id: string) => api.delete(`/kb/documents/${id}`),
};

export const campaignsApi = {
  list: () => api.get("/campaigns"),
  get: (id: string) => api.get(`/campaigns/${id}`),
  create: (data: any) => api.post("/campaigns", data),
  start: (id: string) => api.post(`/campaigns/${id}/start`),
  pause: (id: string) => api.post(`/campaigns/${id}/pause`),
};
```

---

## Step 5: Auth Context

Create `src/lib/auth-context.tsx`:

```typescript
"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "./api";

interface User {
  id: string;
  email: string;
  full_name: string;
  tenant_id?: string;
  is_superadmin: boolean;
  roles: string[];
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await authApi.me();
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await authApi.login(email, password);
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    
    const userResponse = await authApi.me();
    setUser(userResponse.data);
    
    router.push("/dashboard");
  };

  const logout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
    router.push("/login");
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.is_superadmin) return true;
    // Check user roles for permission
    return true; // Simplified - implement proper permission check
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, hasPermission }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
```

---

## Step 6: Layout Components

Create `src/components/layout/sidebar.tsx`:

```typescript
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import {
  LayoutDashboard,
  Phone,
  Users,
  CreditCard,
  BookOpen,
  Settings,
  Building2,
  PhoneOutgoing,
  LogOut,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Call History", href: "/dashboard/calls", icon: Phone },
  { name: "Campaigns", href: "/dashboard/campaigns", icon: PhoneOutgoing },
  { name: "Knowledge Base", href: "/dashboard/kb", icon: BookOpen },
  { name: "Credits", href: "/dashboard/credits", icon: CreditCard },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

const adminNavigation = [
  { name: "Tenants", href: "/tenants", icon: Building2 },
  { name: "Users", href: "/users", icon: Users },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full w-64 flex-col bg-gray-900">
      {/* Logo */}
      <div className="flex h-16 items-center px-6">
        <span className="text-xl font-bold text-white">Voice AI</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}

        {/* Admin section */}
        {user?.is_superadmin && (
          <>
            <div className="my-4 border-t border-gray-700" />
            <p className="px-3 text-xs font-semibold uppercase text-gray-500">
              Admin
            </p>
            {adminNavigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-gray-800 text-white"
                      : "text-gray-400 hover:bg-gray-800 hover:text-white"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* User section */}
      <div className="border-t border-gray-700 p-4">
        <div className="flex items-center gap-3">
          <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
            <span className="text-sm font-medium text-white">
              {user?.full_name?.charAt(0) || "U"}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.full_name}
            </p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="text-gray-400 hover:text-white"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 7: Dashboard Page

Create `src/app/dashboard/page.tsx`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { callsApi, creditsApi } from "@/lib/api";
import { formatCurrency, formatDuration } from "@/lib/utils";
import {
  Phone,
  PhoneIncoming,
  PhoneOutgoing,
  CreditCard,
  TrendingUp,
  Clock,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Stats {
  total_calls: number;
  inbound_calls: number;
  outbound_calls: number;
  total_duration: number;
  credits_used: number;
  credit_balance: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, balanceRes] = await Promise.all([
        callsApi.getStats(),
        creditsApi.getBalance(),
      ]);

      setStats({
        ...statsRes.data,
        credit_balance: balanceRes.data.balance,
      });

      // Generate chart data (last 7 days)
      const days = [];
      for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        days.push({
          date: date.toLocaleDateString("en-US", { weekday: "short" }),
          calls: Math.floor(Math.random() * 50) + 10, // Replace with real data
          credits: Math.floor(Math.random() * 100) + 20,
        });
      }
      setChartData(days);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Calls"
          value={stats?.total_calls || 0}
          icon={Phone}
          color="blue"
        />
        <StatCard
          title="Inbound"
          value={stats?.inbound_calls || 0}
          icon={PhoneIncoming}
          color="green"
        />
        <StatCard
          title="Outbound"
          value={stats?.outbound_calls || 0}
          icon={PhoneOutgoing}
          color="purple"
        />
        <StatCard
          title="Credit Balance"
          value={formatCurrency(stats?.credit_balance || 0)}
          icon={CreditCard}
          color="yellow"
        />
      </div>

      {/* Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">Call Activity (Last 7 Days)</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="calls"
                stroke="#3b82f6"
                strokeWidth={2}
                name="Calls"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="credits"
                stroke="#10b981"
                strokeWidth={2}
                name="Credits Used"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Recent Calls</h2>
        </div>
        <RecentCallsList />
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: any;
  color: string;
}) {
  const colors = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    yellow: "bg-yellow-500",
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center">
        <div className={`${colors[color]} rounded-lg p-3`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-semibold">{value}</p>
        </div>
      </div>
    </div>
  );
}

function RecentCallsList() {
  const [calls, setCalls] = useState<any[]>([]);

  useEffect(() => {
    callsApi.list({ limit: 5 }).then((res) => setCalls(res.data));
  }, []);

  return (
    <div className="divide-y">
      {calls.map((call) => (
        <div key={call.id} className="px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {call.direction === "inbound" ? (
              <PhoneIncoming className="h-5 w-5 text-green-500" />
            ) : (
              <PhoneOutgoing className="h-5 w-5 text-blue-500" />
            )}
            <div>
              <p className="font-medium">{call.from_number}</p>
              <p className="text-sm text-gray-500">
                {formatDuration(call.duration_seconds)}
              </p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-500">
              {new Date(call.created_at).toLocaleString()}
            </p>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                call.status === "completed"
                  ? "bg-green-100 text-green-800"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              {call.status}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Step 8: Tenant Management (Super Admin)

Create `src/app/tenants/page.tsx`:

```typescript
"use client";

import { useEffect, useState } from "react";
import { tenantsApi } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { Plus, Edit, Trash2, CreditCard } from "lucide-react";

interface Tenant {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
  credit_balance: number;
  inbound_calls_enabled: boolean;
  outbound_calls_enabled: boolean;
  created_at: string;
}

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreditModal, setShowCreditModal] = useState<string | null>(null);

  useEffect(() => {
    loadTenants();
  }, []);

  const loadTenants = async () => {
    try {
      const response = await tenantsApi.list();
      setTenants(response.data);
    } catch (error) {
      console.error("Failed to load tenants:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddCredits = async (tenantId: string, amount: number, notes: string) => {
    try {
      await tenantsApi.addCredits(tenantId, amount, notes);
      loadTenants();
      setShowCreditModal(null);
    } catch (error) {
      console.error("Failed to add credits:", error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Tenants</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          <Plus className="h-5 w-5" />
          Add Tenant
        </button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Tenant
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Features
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                Credits
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tenants.map((tenant) => (
              <tr key={tenant.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="font-medium text-gray-900">{tenant.name}</div>
                    <div className="text-sm text-gray-500">{tenant.slug}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      tenant.is_active
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}
                  >
                    {tenant.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex gap-2">
                    {tenant.inbound_calls_enabled && (
                      <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                        Inbound
                      </span>
                    )}
                    {tenant.outbound_calls_enabled && (
                      <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
                        Outbound
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="font-medium">
                    {formatCurrency(tenant.credit_balance)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => setShowCreditModal(tenant.id)}
                      className="text-green-600 hover:text-green-900"
                      title="Add Credits"
                    >
                      <CreditCard className="h-5 w-5" />
                    </button>
                    <button
                      className="text-blue-600 hover:text-blue-900"
                      title="Edit"
                    >
                      <Edit className="h-5 w-5" />
                    </button>
                    <button
                      className="text-red-600 hover:text-red-900"
                      title="Delete"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Credits Modal */}
      {showCreditModal && (
        <AddCreditsModal
          tenantId={showCreditModal}
          onClose={() => setShowCreditModal(null)}
          onSubmit={handleAddCredits}
        />
      )}
    </div>
  );
}

function AddCreditsModal({
  tenantId,
  onClose,
  onSubmit,
}: {
  tenantId: string;
  onClose: () => void;
  onSubmit: (tenantId: string, amount: number, notes: string) => void;
}) {
  const [amount, setAmount] = useState("");
  const [notes, setNotes] = useState("");

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-lg font-semibold mb-4">Add Credits</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Amount
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              placeholder="100.00"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
              rows={3}
              placeholder="Optional notes..."
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
          <button
            onClick={() => onSubmit(tenantId, parseFloat(amount), notes)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Credits
          </button>
        </div>
      </div>
    </div>
  );
}
```

---

## Step 9: Run the Admin UI

```bash
cd ~/voice-ai-platform/src/admin-ui

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local

# Run development server
pnpm dev
```

Access at: http://localhost:3000

---

## Step 10: Build for Production

```bash
# Build
pnpm build

# Start production server
pnpm start

# Or export static files
pnpm build && pnpm export
```

---

## Key Pages Summary

| Page | Path | Description |
|------|------|-------------|
| Login | `/login` | Authentication |
| Dashboard | `/dashboard` | Overview & stats |
| Call History | `/dashboard/calls` | View all calls |
| Campaigns | `/dashboard/campaigns` | Outbound campaigns |
| Knowledge Base | `/dashboard/kb` | Document management |
| Credits | `/dashboard/credits` | Usage & transactions |
| Settings | `/dashboard/settings` | Agent config |
| Tenants (Admin) | `/tenants` | Manage tenants |
| Users (Admin) | `/users` | Manage users |

---

## Next Step

Proceed to: `.claude/skills/09-CREDIT-SYSTEM.md`
