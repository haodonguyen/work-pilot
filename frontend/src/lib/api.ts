const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Customer = {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  notes?: string;
};

export type Job = {
  id: number;
  customer_id: number;
  service_type: string;
  scheduled_at: string;
  price: number;
  status: "scheduled" | "confirmed" | "completed" | "cancelled";
  staff_member?: string;
  notes?: string;
  customer: Customer;
};

export type Invoice = {
  id: number;
  customer_id: number;
  number: string;
  amount: number;
  due_date: string;
  status: "draft" | "sent" | "paid" | "void";
  notes?: string;
  customer: Customer;
};

export type QuoteRecord = {
  id: number;
  customer_id: number;
  number: string;
  service_type: string;
  amount: number;
  valid_until: string;
  status: "draft" | "sent" | "accepted" | "declined";
  notes?: string;
  customer: Customer;
};

export type Dashboard = {
  todays_jobs: number;
  upcoming_bookings: number;
  pending_quotes: number;
  overdue_invoices: number;
  automation_events: number;
  estimated_admin_minutes_saved: number;
};

export type AutomationEvent = {
  id: number;
  rule_id: number | null;
  job_id: number | null;
  message: string;
  status: string;
  created_at: string;
};

export type AutomationRule = {
  id: number;
  name: string;
  trigger: string;
  condition: string;
  action: string;
  enabled: boolean;
};

export type AutomationRuleInput = Omit<AutomationRule, "id">;

export type MessageTemplate = {
  id: number;
  type: string;
  name: string;
  body: string;
};

let token = localStorage.getItem("workpilot_token") ?? "";

export function setToken(nextToken: string) {
  token = nextToken;
  localStorage.setItem("workpilot_token", nextToken);
}

export function clearToken() {
  token = "";
  localStorage.removeItem("workpilot_token");
}

export function hasToken() {
  return Boolean(token);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail ?? "Request failed");
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json();
}

export const api = {
  register: (body: { business_name: string; name: string; email: string; password: string }) =>
    request("/auth/register", { method: "POST", body: JSON.stringify(body) }),
  login: (body: { email: string; password: string }) =>
    request<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => request<{ name: string; email: string; business: { name: string } }>("/auth/me"),
  dashboard: () => request<Dashboard>("/dashboard"),
  customers: () => request<Customer[]>("/customers"),
  createCustomer: (body: Omit<Customer, "id">) =>
    request<Customer>("/customers", { method: "POST", body: JSON.stringify(body) }),
  updateCustomer: (id: number, body: Partial<Omit<Customer, "id">>) =>
    request<Customer>(`/customers/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  jobs: () => request<Job[]>("/jobs"),
  createJob: (body: Omit<Job, "id" | "customer">) =>
    request<Job>("/jobs", { method: "POST", body: JSON.stringify(body) }),
  completeJob: (job: Job) =>
    request<Job>(`/jobs/${job.id}/complete`, { method: "POST" }),
  invoices: () => request<Invoice[]>("/invoices"),
  createInvoice: (body: Omit<Invoice, "id" | "customer">) =>
    request<Invoice>("/invoices", { method: "POST", body: JSON.stringify(body) }),
  markInvoicePaid: (invoice: Invoice) =>
    request<Invoice>(`/invoices/${invoice.id}/mark-paid`, { method: "POST" }),
  quotes: () => request<QuoteRecord[]>("/quotes"),
  createQuote: (body: Omit<QuoteRecord, "id" | "customer">) =>
    request<QuoteRecord>("/quotes", { method: "POST", body: JSON.stringify(body) }),
  acceptQuote: (quote: QuoteRecord) =>
    request<QuoteRecord>(`/quotes/${quote.id}/accept`, { method: "POST" }),
  declineQuote: (quote: QuoteRecord) =>
    request<QuoteRecord>(`/quotes/${quote.id}/decline`, { method: "POST" }),
  events: () => request<AutomationEvent[]>("/automation-events"),
  rules: () => request<AutomationRule[]>("/automation-rules"),
  createRule: (body: AutomationRuleInput) =>
    request<AutomationRule>("/automation-rules", { method: "POST", body: JSON.stringify(body) }),
  updateRule: (id: number, body: Partial<AutomationRuleInput>) =>
    request<AutomationRule>(`/automation-rules/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteRule: (id: number) =>
    request<void>(`/automation-rules/${id}`, { method: "DELETE" }),
  testRule: (id: number) =>
    request<AutomationEvent>(`/automation-rules/${id}/test`, { method: "POST" }),
  runQuoteFollowups: () =>
    request<AutomationEvent[]>("/automation-rules/run-quote-followups", { method: "POST" }),
  templates: () => request<MessageTemplate[]>("/templates"),
  suggestions: () => request<{ suggestions: { title: string; reason: string; rule: string }[] }>("/ai/suggest-automations", { method: "POST" }),
};
