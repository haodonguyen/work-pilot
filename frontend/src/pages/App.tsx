import {
  Bell,
  BellRing,
  Bot,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  FileText,
  Clock3,
  GitBranch,
  HelpCircle,
  History,
  LogOut,
  PlayCircle,
  Plus,
  Quote,
  Repeat2,
  Search,
  Send,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Sparkles,
  Star,
  TestTube2,
  Trash2,
  Users,
  Wallet,
  Wand2,
  XCircle,
  Zap,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { api, AutomationEvent, AutomationRule, AutomationRuleInput, clearToken, Customer, Dashboard, hasToken, Invoice, Job, MessageTemplate, QuoteRecord, setToken } from "../lib/api";

type User = { name: string; email: string; business: { name: string } };
type WorkspaceView = "dashboard" | "automations";
type JobFilter = "active" | Job["status"];
type QuoteFilter = "open" | QuoteRecord["status"];
type InvoiceFilter = "open" | "overdue" | Invoice["status"];

const EMPTY_RULE: AutomationRuleInput = {
  name: "24-hour appointment reminder",
  trigger: "job.reminder_due",
  condition: "Job is scheduled or confirmed within 24 hours",
  action: "Generate appointment reminder",
  enabled: true,
};

function dateInputValue(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function dateInputDaysFromNow(days: number) {
  const date = new Date();
  date.setDate(date.getDate() + days);
  return dateInputValue(date);
}

function dateTimeInputHoursFromNow(hours: number) {
  const date = new Date();
  date.setHours(date.getHours() + hours);
  date.setMinutes(0, 0, 0);
  return `${dateInputValue(date)}T${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

function documentNumber(prefix: string) {
  const now = new Date();
  const stamp = `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, "0")}${String(now.getDate()).padStart(2, "0")}-${String(now.getHours()).padStart(2, "0")}${String(now.getMinutes()).padStart(2, "0")}`;
  return `${prefix}-${stamp}`;
}

function Field(props: { label: string; children: React.ReactNode }) {
  return (
    <label className="field">
      <span>{props.label}</span>
      {props.children}
    </label>
  );
}

function Metric(props: { icon: React.ReactNode; label: string; value: number | string }) {
  return (
    <div className="metric">
      <div className="metricIcon">{props.icon}</div>
      <span>{props.label}</span>
      <strong>{props.value}</strong>
    </div>
  );
}

function ProofPoint(props: { value: string; label: string }) {
  return (
    <div className="proofPoint">
      <strong>{props.value}</strong>
      <span>{props.label}</span>
    </div>
  );
}

function AttentionCard(props: { icon: React.ReactNode; label: string; value: number | string; detail: string }) {
  return (
    <article className="attentionCard">
      <div className="attentionIcon">{props.icon}</div>
      <div>
        <strong>{props.value}</strong>
        <span>{props.label}</span>
        <small>{props.detail}</small>
      </div>
    </article>
  );
}

function FilterBar<T extends string>(props: { value: T; options: { value: T; label: string; count: number }[]; onChange: (value: T) => void }) {
  return (
    <div className="filterBar">
      {props.options.map((option) => (
        <button
          key={option.value}
          className={props.value === option.value ? "active" : ""}
          onClick={() => props.onChange(option.value)}
          type="button"
        >
          <span>{option.label}</span>
          <strong>{option.count}</strong>
        </button>
      ))}
    </div>
  );
}

function StatusPill(props: { status: string; tone?: "default" | "warning" | "success" | "muted" }) {
  return <span className={`statusPill ${props.tone ?? "default"}`}>{props.status.replaceAll("_", " ")}</span>;
}

function EmptyState(props: { title: string; children: React.ReactNode }) {
  return (
    <div className="emptyState">
      <ClipboardList size={24} />
      <strong>{props.title}</strong>
      <p>{props.children}</p>
    </div>
  );
}

function ConnectionState() {
  return (
    <main className="loading">
      <div className="loadingCard">
        <div className="brandMark"><Sparkles size={24} /></div>
        <strong>Reconnecting to WorkPilot</strong>
        <span>Waking your secure workspace.</span>
      </div>
    </main>
  );
}

function matchesSearch(values: Array<string | number | undefined | null>, search: string) {
  if (!search.trim()) return true;
  const query = search.trim().toLowerCase();
  return values.some((value) => String(value ?? "").toLowerCase().includes(query));
}

function isOverdueInvoice(invoice: Invoice) {
  return invoice.status === "sent" && new Date(`${invoice.due_date}T00:00:00`) < new Date(new Date().toDateString());
}

function invoiceDisplayStatus(invoice: Invoice) {
  return isOverdueInvoice(invoice) ? "overdue" : invoice.status;
}

function statusTone(status: string): "default" | "warning" | "success" | "muted" {
  if (["completed", "paid", "accepted"].includes(status)) return "success";
  if (["overdue", "sent", "scheduled", "confirmed"].includes(status)) return "warning";
  if (["declined", "void", "cancelled", "draft"].includes(status)) return "muted";
  return "default";
}

function FeatureCard(props: { className?: string; icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <article className={`featureCard ${props.className ?? ""}`}>
      <div className="featureIcon">{props.icon}</div>
      <h3>{props.title}</h3>
      <p>{props.children}</p>
    </article>
  );
}

function DashboardPreview() {
  return (
    <div className="dashboardPreview" aria-label="WorkPilot dashboard preview">
      <div className="previewTopbar">
        <span></span>
        <span></span>
        <span></span>
      </div>
      <div className="previewGrid">
        <div className="previewMetric wide"><strong>12h</strong><span>Admin saved</span></div>
        <div className="previewMetric"><strong>4</strong><span>Jobs today</span></div>
        <div className="previewPanel">
          <div className="previewLine"></div>
          <div className="previewLine short"></div>
          <div className="previewLine"></div>
        </div>
        <div className="previewPanel dark">
          <Sparkles size={22} />
          <span>AI suggestion ready</span>
        </div>
      </div>
    </div>
  );
}

function AuthScreen(props: { onAuthed: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("register");
  const [error, setError] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState({
    business_name: "",
    name: "",
    email: "",
    password: "",
  });

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setIsSaving(true);
    try {
      if (mode === "register") {
        await api.register(form);
      }
      const login = await api.login({ email: form.email, password: form.password });
      setToken(login.access_token);
      props.onAuthed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <main className="landingShell">
      <nav className="landingNav">
        <a className="wordmark" href="#home">WorkPilot</a>
        <div className="landingLinks">
          <a className="active" href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#pricing">Pricing</a>
          <a href="#stories">Success Stories</a>
        </div>
        <div className="landingActions">
          <button className="navIcon" aria-label="Search" title="Search"><Search size={20} /></button>
          <a className="primaryButton compact" href="#start">Start Free Trial</a>
        </div>
      </nav>

      <section className="heroSection" id="home">
        <div className="heroCopy">
          <div className="trustBadge"><ShieldCheck size={18} /> Built for Australian service businesses</div>
          <h1>Run bookings, quotes, and follow-ups from one calm workspace.</h1>
          <p>WorkPilot keeps local teams on top of customer admin with reminders, quote nudges, invoices, and clear next actions.</p>
          <div className="proofGrid" aria-label="WorkPilot operational highlights">
            <ProofPoint value="14h" label="admin saved weekly" />
            <ProofPoint value="3x" label="faster quote follow-up" />
            <ProofPoint value="1" label="shared customer queue" />
          </div>
          <div className="heroActions">
            <a className="primaryButton heroButton" href="#start">Start Free Trial</a>
            <a className="secondaryButton heroButton" href="#features"><PlayCircle size={20} /> Watch Demo</a>
          </div>
        </div>
        <div className="heroVisual">
          <DashboardPreview />
          <div className="floatingBadge">
            <Zap size={28} />
            <div><span>Saved this week</span><strong>14.5 Hours</strong></div>
          </div>
        </div>
      </section>

      <section className="featuresSection" id="features">
        <div className="sectionHeader">
          <h2>Powerful features for local pros</h2>
          <p>Focus on your craft while WorkPilot handles reminders, follow-ups, and customer nudges with intelligent precision.</p>
        </div>
        <div className="bentoGrid">
          <FeatureCard className="span7" icon={<BellRing size={34} />} title="Booking Reminders">
            Reduce no-shows with automated SMS and email reminders that feel personal, not robotic.
          </FeatureCard>
          <FeatureCard className="span5 primaryFeature" icon={<Quote size={34} />} title="Quote Follow-ups">
            Never let a lead go cold. WorkPilot follows up on sent quotes and prompts customers for approval.
          </FeatureCard>
          <FeatureCard className="span5 softFeature" icon={<Star size={34} />} title="Review Requests">
            Build your online reputation on autopilot after every successful job.
          </FeatureCard>
          <FeatureCard className="span7 inverseFeature" icon={<Bot size={42} />} title="AI Suggestions">
            WorkPilot analyzes your activity and suggests automations that can save billable hours.
          </FeatureCard>
        </div>
      </section>

      <section className="startSection" id="start">
        <div className="ctaPanel">
          <h2>Ready to automate your admin and win back your weekends?</h2>
          <p>Join Australian service professionals who have simplified bookings, follow-ups, and review requests.</p>
        </div>
        <form className="authPanel" onSubmit={submit}>
          <div className="segmented">
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>Register</button>
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button>
          </div>
          {mode === "register" && (
            <>
              <Field label="Business name">
                <input value={form.business_name} onChange={(event) => setForm({ ...form, business_name: event.target.value })} />
              </Field>
              <Field label="Your name">
                <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} />
              </Field>
            </>
          )}
          <Field label="Email">
            <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </Field>
          <Field label="Password">
            <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          </Field>
          {error && <p className="error">{error}</p>}
          <button className="primaryButton" type="submit" disabled={isSaving}>
            <Send size={17} /> {isSaving ? "Connecting..." : "Continue"}
          </button>
        </form>
      </section>

      <footer className="landingFooter">
        <div>
          <strong>WorkPilot</strong>
          <p>Reliable efficiency for small business. Helping Aussie pros grow.</p>
        </div>
        <div>
          <a href="#privacy">Privacy Policy</a>
          <a href="#terms">Terms of Service</a>
          <a href="#support">Contact Support</a>
        </div>
      </footer>
    </main>
  );
}

function CustomerForm(props: { onCreate: () => void | Promise<void> }) {
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [email, setEmail] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setIsSaving(true);
    try {
      await api.createCustomer({ name, phone, address, email: email || undefined, notes: "" });
      setName("");
      setPhone("");
      setAddress("");
      setEmail("");
      await props.onCreate();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="inlineForm" onSubmit={submit}>
      <Field label="Customer">
        <input required value={name} onChange={(event) => setName(event.target.value)} placeholder="Customer name" />
      </Field>
      <Field label="Email">
        <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="name@example.com" />
      </Field>
      <Field label="Phone">
        <input value={phone} onChange={(event) => setPhone(event.target.value)} placeholder="Phone number" />
      </Field>
      <Field label="Address">
        <input value={address} onChange={(event) => setAddress(event.target.value)} placeholder="Service address" />
      </Field>
      <button className="iconButton" type="submit" aria-label="Add customer" title="Add customer" disabled={isSaving}>
        <Plus size={18} />
      </button>
    </form>
  );
}

function JobForm(props: { customers: Customer[]; onCreate: () => void | Promise<void> }) {
  const firstCustomer = props.customers[0]?.id ?? 0;
  const [customerId, setCustomerId] = useState(firstCustomer);
  const [serviceType, setServiceType] = useState("");
  const [scheduledAt, setScheduledAt] = useState(() => dateTimeInputHoursFromNow(24));
  const [price, setPrice] = useState(0);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!customerId && firstCustomer) setCustomerId(firstCustomer);
  }, [customerId, firstCustomer]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!customerId) return;
    setIsSaving(true);
    try {
      await api.createJob({
        customer_id: customerId,
        service_type: serviceType,
        scheduled_at: new Date(scheduledAt).toISOString(),
        price,
        status: "scheduled",
        staff_member: "Mia",
        notes: "",
      });
      setServiceType("");
      setScheduledAt(dateTimeInputHoursFromNow(24));
      setPrice(0);
      await props.onCreate();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="inlineForm" onSubmit={submit}>
      <Field label="Customer">
        <select value={customerId} onChange={(event) => setCustomerId(Number(event.target.value))}>
          {props.customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Service">
        <input required value={serviceType} onChange={(event) => setServiceType(event.target.value)} placeholder="Service type" />
      </Field>
      <Field label="Date">
        <input type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} />
      </Field>
      <Field label="Price">
        <input type="number" value={price} onChange={(event) => setPrice(Number(event.target.value))} />
      </Field>
      <button className="iconButton" type="submit" aria-label="Add job" title="Add job" disabled={isSaving}>
        <Plus size={18} />
      </button>
    </form>
  );
}

function InvoiceForm(props: { customers: Customer[]; onCreate: () => void | Promise<void> }) {
  const firstCustomer = props.customers[0]?.id ?? 0;
  const [customerId, setCustomerId] = useState(firstCustomer);
  const [number, setNumber] = useState(() => documentNumber("INV"));
  const [amount, setAmount] = useState(0);
  const [dueDate, setDueDate] = useState(() => dateInputDaysFromNow(7));
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!customerId && firstCustomer) setCustomerId(firstCustomer);
  }, [customerId, firstCustomer]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!customerId) return;
    setIsSaving(true);
    try {
      await api.createInvoice({
        customer_id: customerId,
        number,
        amount,
        due_date: dueDate,
        status: "sent",
        notes: "",
      });
      setNumber(documentNumber("INV"));
      setAmount(0);
      setDueDate(dateInputDaysFromNow(7));
      await props.onCreate();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="inlineForm" onSubmit={submit}>
      <Field label="Customer">
        <select value={customerId} onChange={(event) => setCustomerId(Number(event.target.value))}>
          {props.customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Invoice">
        <input required value={number} onChange={(event) => setNumber(event.target.value)} />
      </Field>
      <Field label="Due">
        <input type="date" value={dueDate} onChange={(event) => setDueDate(event.target.value)} />
      </Field>
      <Field label="Amount">
        <input type="number" value={amount} onChange={(event) => setAmount(Number(event.target.value))} />
      </Field>
      <button className="iconButton" type="submit" aria-label="Add invoice" title="Add invoice" disabled={isSaving}>
        <Plus size={18} />
      </button>
    </form>
  );
}

function QuoteForm(props: { customers: Customer[]; onCreate: () => void | Promise<void> }) {
  const firstCustomer = props.customers[0]?.id ?? 0;
  const [customerId, setCustomerId] = useState(firstCustomer);
  const [number, setNumber] = useState(() => documentNumber("QUO"));
  const [serviceType, setServiceType] = useState("");
  const [amount, setAmount] = useState(0);
  const [validUntil, setValidUntil] = useState(() => dateInputDaysFromNow(14));
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!customerId && firstCustomer) setCustomerId(firstCustomer);
  }, [customerId, firstCustomer]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!customerId) return;
    setIsSaving(true);
    try {
      await api.createQuote({
        customer_id: customerId,
        number,
        service_type: serviceType,
        amount,
        valid_until: validUntil,
        status: "sent",
        notes: "",
      });
      setNumber(documentNumber("QUO"));
      setServiceType("");
      setAmount(0);
      setValidUntil(dateInputDaysFromNow(14));
      await props.onCreate();
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form className="inlineForm" onSubmit={submit}>
      <Field label="Customer">
        <select value={customerId} onChange={(event) => setCustomerId(Number(event.target.value))}>
          {props.customers.map((customer) => (
            <option key={customer.id} value={customer.id}>
              {customer.name}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Quote">
        <input required value={number} onChange={(event) => setNumber(event.target.value)} />
      </Field>
      <Field label="Service">
        <input required value={serviceType} onChange={(event) => setServiceType(event.target.value)} placeholder="Service type" />
      </Field>
      <Field label="Valid">
        <input type="date" value={validUntil} onChange={(event) => setValidUntil(event.target.value)} />
      </Field>
      <Field label="Amount">
        <input type="number" value={amount} onChange={(event) => setAmount(Number(event.target.value))} />
      </Field>
      <button className="iconButton" type="submit" aria-label="Add quote" title="Add quote" disabled={isSaving}>
        <Plus size={18} />
      </button>
    </form>
  );
}

function AutomationsBuilder(props: {
  rules: AutomationRule[];
  events: AutomationEvent[];
  suggestions: { title: string; reason: string; rule: string }[];
  onRefresh: () => Promise<void>;
}) {
  const [selectedId, setSelectedId] = useState<number | null>(props.rules[0]?.id ?? null);
  const [isCreating, setIsCreating] = useState(false);
  const selectedRule = props.rules.find((rule) => rule.id === selectedId);
  const [draft, setDraft] = useState<AutomationRuleInput>(selectedRule ?? EMPTY_RULE);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (isCreating) return;
    const nextRule = props.rules.find((rule) => rule.id === selectedId) ?? props.rules[0];
    if (nextRule) {
      setSelectedId(nextRule.id);
      setDraft({
        name: nextRule.name,
        trigger: nextRule.trigger,
        condition: nextRule.condition,
        action: nextRule.action,
        enabled: nextRule.enabled,
      });
    }
  }, [props.rules, selectedId, isCreating]);

  function edit<K extends keyof AutomationRuleInput>(key: K, value: AutomationRuleInput[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  async function saveRule(event: FormEvent) {
    event.preventDefault();
    setStatus("");
    if (selectedRule) {
      await api.updateRule(selectedRule.id, draft);
      setStatus("Automation updated.");
    } else {
      const created = await api.createRule(draft);
      setSelectedId(created.id);
      setIsCreating(false);
      setStatus("Automation created.");
    }
    await props.onRefresh();
  }

  async function createNewRule() {
    setIsCreating(true);
    setSelectedId(null);
    setDraft(EMPTY_RULE);
    setStatus("Drafting a new automation.");
  }

  async function testRule() {
    if (!selectedRule) {
      setStatus("Save this automation before testing it.");
      return;
    }
    await api.testRule(selectedRule.id);
    await props.onRefresh();
    setStatus("Test event queued in Activity.");
  }

  async function runQuoteFollowups() {
    const events = await api.runQuoteFollowups();
    await props.onRefresh();
    setStatus(events.length ? `${events.length} quote follow-up${events.length === 1 ? "" : "s"} generated.` : "No pending quotes need follow-up.");
  }

  async function deleteRule() {
    if (!selectedRule) return;
    await api.deleteRule(selectedRule.id);
    setIsCreating(false);
    setSelectedId(null);
    setDraft(EMPTY_RULE);
    await props.onRefresh();
    setStatus("Automation deleted.");
  }

  return (
    <section className="builderPage">
      <div className="builderHeader">
        <div>
          <h2>Automations Builder</h2>
          <p>Design simple trigger, condition, and action logic for repetitive admin work.</p>
        </div>
        <button className="primaryButton compact" onClick={createNewRule}><Plus size={17} /> New Automation</button>
      </div>

      <div className="builderLayout">
        <aside className="builderRules">
          <div className="panelHeader"><h3>Rules</h3><span>{props.rules.length}</span></div>
          <div className="ruleStack">
            {props.rules.map((rule) => (
              <button
                key={rule.id}
                className={`ruleButton ${rule.id === selectedId ? "active" : ""}`}
                onClick={() => {
                  setIsCreating(false);
                  setSelectedId(rule.id);
                }}
              >
                <GitBranch size={18} />
                <span>
                  <strong>{rule.name}</strong>
                  <small>{rule.trigger}</small>
                </span>
                <i>{rule.enabled ? "On" : "Off"}</i>
              </button>
            ))}
          </div>
        </aside>

        <form className="builderCanvas" onSubmit={saveRule}>
          <div className="builderNode triggerNode">
            <div className="nodeIcon"><Zap size={21} /></div>
            <Field label="Trigger">
              <select value={draft.trigger} onChange={(event) => edit("trigger", event.target.value)}>
                <option value="job.created">Booking is created</option>
                <option value="job.reminder_due">24 hours before booking</option>
                <option value="job.completed">Job is completed</option>
                <option value="quote.pending">Quote is pending</option>
                <option value="invoice.overdue">Invoice is overdue</option>
              </select>
            </Field>
          </div>

          <div className="flowConnector"></div>

          <div className="builderNode">
            <div className="nodeIcon"><SlidersHorizontal size={21} /></div>
            <Field label="Condition">
              <input value={draft.condition} onChange={(event) => edit("condition", event.target.value)} />
            </Field>
          </div>

          <div className="flowConnector"></div>

          <div className="builderNode actionNode">
            <div className="nodeIcon"><Wand2 size={21} /></div>
            <div className="builderFields">
              <Field label="Rule name">
                <input value={draft.name} onChange={(event) => edit("name", event.target.value)} />
              </Field>
              <Field label="Action">
                <input value={draft.action} onChange={(event) => edit("action", event.target.value)} />
              </Field>
            </div>
          </div>

          <div className="builderToolbar">
            <label className="toggleRow">
              <input type="checkbox" checked={draft.enabled} onChange={(event) => edit("enabled", event.target.checked)} />
              <span>{draft.enabled ? "Enabled" : "Paused"}</span>
            </label>
            <button className="secondaryButton compact" type="button" onClick={testRule}><TestTube2 size={17} /> Test</button>
            <button className="secondaryButton compact" type="button" onClick={runQuoteFollowups}><Repeat2 size={17} /> Run Quote Follow-ups</button>
            {selectedRule && <button className="dangerButton compact" type="button" onClick={deleteRule}><Trash2 size={17} /> Delete</button>}
            <button className="primaryButton compact" type="submit"><CheckCircle2 size={17} /> Save</button>
          </div>
          {status && <p className="builderStatus">{status}</p>}
        </form>

        <aside className="builderAssistant">
          <div className="assistantCard">
            <Bot size={42} />
            <h3>AI Assistant Suggestions</h3>
            <div className="assistantList">
              {props.suggestions.map((suggestion) => (
                <article key={suggestion.title}>
                  <strong>{suggestion.title}</strong>
                  <p>{suggestion.reason}</p>
                </article>
              ))}
            </div>
          </div>
          <div className="healthCard">
            <div className="panelHeader"><h3>Automation Health</h3><span>Live</span></div>
            <div className="healthBar"><span style={{ width: "94%" }}></span></div>
            <p>94% of tasks completed autonomously this week.</p>
          </div>
          <div className="healthCard" id="activity">
            <div className="panelHeader"><h3>Recent tests</h3><span>{props.events.length}</span></div>
            <div className="miniActivity">
              {props.events.slice(0, 4).map((event) => (
                <p key={event.id}>{event.message}</p>
              ))}
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}

function Workspace(props: { user: User; onLogout: () => void }) {
  const [view, setView] = useState<WorkspaceView>("dashboard");
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [quotes, setQuotes] = useState<QuoteRecord[]>([]);
  const [events, setEvents] = useState<AutomationEvent[]>([]);
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [suggestions, setSuggestions] = useState<{ title: string; reason: string; rule: string }[]>([]);
  const [workSearch, setWorkSearch] = useState("");
  const [jobFilter, setJobFilter] = useState<JobFilter>("active");
  const [quoteFilter, setQuoteFilter] = useState<QuoteFilter>("open");
  const [invoiceFilter, setInvoiceFilter] = useState<InvoiceFilter>("open");

  async function refresh() {
    const [nextDashboard, nextCustomers, nextJobs, nextInvoices, nextQuotes, nextEvents, nextRules, nextTemplates, nextSuggestions] = await Promise.all([
      api.dashboard(),
      api.customers(),
      api.jobs(),
      api.invoices(),
      api.quotes(),
      api.events(),
      api.rules(),
      api.templates(),
      api.suggestions(),
    ]);
    setDashboard(nextDashboard);
    setCustomers(nextCustomers);
    setJobs(nextJobs);
    setInvoices(nextInvoices);
    setQuotes(nextQuotes);
    setEvents(nextEvents);
    setRules(nextRules);
    setTemplates(nextTemplates);
    setSuggestions(nextSuggestions.suggestions);
  }

  useEffect(() => {
    refresh();
  }, []);

  const nextJob = useMemo(() => jobs.find((job) => job.status === "scheduled" || job.status === "confirmed"), [jobs]);
  const visibleCustomers = useMemo(
    () => customers.filter((customer) => matchesSearch([customer.name, customer.email, customer.phone, customer.address], workSearch)),
    [customers, workSearch],
  );
  const visibleJobs = useMemo(
    () => jobs.filter((job) => {
      const statusMatch = jobFilter === "active" ? ["scheduled", "confirmed"].includes(job.status) : job.status === jobFilter;
      return statusMatch && matchesSearch([job.service_type, job.customer.name, job.price, job.status], workSearch);
    }),
    [jobs, jobFilter, workSearch],
  );
  const visibleQuotes = useMemo(
    () => quotes.filter((quote) => {
      const statusMatch = quoteFilter === "open" ? quote.status === "sent" : quote.status === quoteFilter;
      return statusMatch && matchesSearch([quote.number, quote.customer.name, quote.service_type, quote.amount, quote.status], workSearch);
    }),
    [quotes, quoteFilter, workSearch],
  );
  const visibleInvoices = useMemo(
    () => invoices.filter((invoice) => {
      const displayStatus = invoiceDisplayStatus(invoice);
      const statusMatch = invoiceFilter === "open" ? ["sent", "overdue"].includes(displayStatus) : displayStatus === invoiceFilter;
      return statusMatch && matchesSearch([invoice.number, invoice.customer.name, invoice.amount, displayStatus], workSearch);
    }),
    [invoices, invoiceFilter, workSearch],
  );
  const jobFilterOptions = useMemo(
    () => [
      { value: "active" as const, label: "Active", count: jobs.filter((job) => ["scheduled", "confirmed"].includes(job.status)).length },
      { value: "scheduled" as const, label: "Scheduled", count: jobs.filter((job) => job.status === "scheduled").length },
      { value: "confirmed" as const, label: "Confirmed", count: jobs.filter((job) => job.status === "confirmed").length },
      { value: "completed" as const, label: "Completed", count: jobs.filter((job) => job.status === "completed").length },
      { value: "cancelled" as const, label: "Cancelled", count: jobs.filter((job) => job.status === "cancelled").length },
    ],
    [jobs],
  );
  const quoteFilterOptions = useMemo(
    () => [
      { value: "open" as const, label: "Open", count: quotes.filter((quote) => quote.status === "sent").length },
      { value: "draft" as const, label: "Draft", count: quotes.filter((quote) => quote.status === "draft").length },
      { value: "sent" as const, label: "Sent", count: quotes.filter((quote) => quote.status === "sent").length },
      { value: "accepted" as const, label: "Accepted", count: quotes.filter((quote) => quote.status === "accepted").length },
      { value: "declined" as const, label: "Declined", count: quotes.filter((quote) => quote.status === "declined").length },
    ],
    [quotes],
  );
  const invoiceFilterOptions = useMemo(
    () => [
      { value: "open" as const, label: "Open", count: invoices.filter((invoice) => ["sent", "overdue"].includes(invoiceDisplayStatus(invoice))).length },
      { value: "draft" as const, label: "Draft", count: invoices.filter((invoice) => invoice.status === "draft").length },
      { value: "sent" as const, label: "Sent", count: invoices.filter((invoice) => invoice.status === "sent" && !isOverdueInvoice(invoice)).length },
      { value: "overdue" as const, label: "Overdue", count: invoices.filter(isOverdueInvoice).length },
      { value: "paid" as const, label: "Paid", count: invoices.filter((invoice) => invoice.status === "paid").length },
      { value: "void" as const, label: "Void", count: invoices.filter((invoice) => invoice.status === "void").length },
    ],
    [invoices],
  );

  async function completeJob(job: Job) {
    await api.completeJob(job);
    await refresh();
  }

  async function markInvoicePaid(invoice: Invoice) {
    await api.markInvoicePaid(invoice);
    await refresh();
  }

  async function acceptQuote(quote: QuoteRecord) {
    await api.acceptQuote(quote);
    await refresh();
  }

  async function declineQuote(quote: QuoteRecord) {
    await api.declineQuote(quote);
    await refresh();
  }

  const nextActionDetail = nextJob
    ? `${nextJob.customer.name} - ${new Date(nextJob.scheduled_at).toLocaleDateString()}`
    : "No active jobs scheduled";
  const overdueTotal = invoices
    .filter(isOverdueInvoice)
    .reduce((total, invoice) => total + Number(invoice.amount), 0);

  return (
    <main className="appShell">
      <aside className="sidebar">
        <div className="brandRow"><div className="brandMark small"><Sparkles size={20} /></div><div><strong>WorkPilot AI</strong><span>Pro Plan</span></div></div>
        <button className="primaryButton newAutomation" onClick={() => setView("automations")}><Plus size={18} /> New Automation</button>
        <nav>
          <button className={view === "dashboard" ? "active" : ""} onClick={() => setView("dashboard")}><ClipboardList size={18} /> Dashboard</button>
          <button onClick={() => setView("dashboard")}><BriefcaseBusiness size={18} /> Jobs</button>
          <button onClick={() => setView("dashboard")}><Users size={18} /> Customers</button>
          <button className={view === "automations" ? "active" : ""} onClick={() => setView("automations")}><Bot size={18} /> Automations</button>
          <button onClick={() => setView("automations")}><History size={18} /> Activity</button>
          <button><Settings size={18} /> Settings</button>
        </nav>
        <button className="ghostButton" onClick={props.onLogout}><LogOut size={17} /> Logout</button>
      </aside>
      <section className="content">
        <header className="topbar">
          <div>
            <h1>{view === "automations" ? "Automations Builder" : `Welcome back, ${props.user.business.name}`}</h1>
            <p>{view === "automations" ? "Design logic to handle repetitive tasks automatically." : "Here is what's happening with your business today."}</p>
          </div>
          <div className="topbarActions">
            <button className="navIcon" aria-label="Notifications" title="Notifications"><Bell size={19} /></button>
            <button className="navIcon" aria-label="Help" title="Help"><HelpCircle size={19} /></button>
            <button className="primaryButton compact" onClick={refresh}><Clock3 size={17} /> Refresh</button>
          </div>
        </header>

        {view === "automations" ? (
          <AutomationsBuilder rules={rules} events={events} suggestions={suggestions} onRefresh={refresh} />
        ) : (
          <>
        <section className="attentionStrip" aria-label="Needs attention">
          <AttentionCard
            icon={<CalendarClock size={20} />}
            label="Next booking"
            value={nextJob ? nextJob.service_type : "Clear"}
            detail={nextActionDetail}
          />
          <AttentionCard
            icon={<Quote size={20} />}
            label="Quotes waiting"
            value={dashboard?.pending_quotes ?? 0}
            detail="Follow up while the work is warm"
          />
          <AttentionCard
            icon={<Wallet size={20} />}
            label="Overdue invoices"
            value={`$${overdueTotal}`}
            detail={`${dashboard?.overdue_invoices ?? 0} invoices need attention`}
          />
        </section>

        <section className="metrics" id="dashboard">
          <Metric icon={<CalendarClock size={20} />} label="Today's Jobs" value={dashboard?.todays_jobs ?? 0} />
          <Metric icon={<Wallet size={20} />} label="Overdue Invoices" value={dashboard?.overdue_invoices ?? 0} />
          <Metric icon={<Quote size={20} />} label="Pending Quotes" value={dashboard?.pending_quotes ?? 0} />
          <Metric icon={<Clock3 size={20} />} label="Admin Time Saved" value={`${dashboard?.estimated_admin_minutes_saved ?? 0}m`} />
        </section>

        <section className="workQueueToolbar">
          <div>
            <h2>Work Queue</h2>
            <p>Scan current work, filter by status, and act on the next customer touchpoint.</p>
          </div>
          <label className="searchField">
            <Search size={18} />
            <input
              value={workSearch}
              onChange={(event) => setWorkSearch(event.target.value)}
              placeholder="Search customers, jobs, quotes, invoices"
            />
          </label>
        </section>

        <section className="grid two">
          <div className="panel" id="customers">
            <div className="panelHeader">
              <h2>Customers</h2>
              <span>{visibleCustomers.length}/{customers.length}</span>
            </div>
            <CustomerForm onCreate={refresh} />
            <div className="list">
              {visibleCustomers.map((customer) => (
                <article key={customer.id} className="rowItem">
                  <strong>{customer.name}</strong>
                  <span>{customer.phone}</span>
                  <small>{customer.address}</small>
                </article>
              ))}
              {!visibleCustomers.length && <EmptyState title="No customers match">Try a different search or add a customer.</EmptyState>}
            </div>
          </div>

          <div className="panel" id="jobs">
            <div className="panelHeader">
              <h2>Jobs</h2>
              <span>{visibleJobs.length}/{jobs.length}</span>
            </div>
            <JobForm customers={customers} onCreate={refresh} />
            <FilterBar value={jobFilter} options={jobFilterOptions} onChange={setJobFilter} />
            <div className="list">
              {visibleJobs.map((job) => (
                <article key={job.id} className="rowItem split">
                  <div>
                    <strong>{job.service_type}</strong>
                    <span>{job.customer.name} · ${job.price}</span>
                    <small>{new Date(job.scheduled_at).toLocaleString()}</small>
                  </div>
                  <div className="rowActions">
                    <StatusPill status={job.status} tone={statusTone(job.status)} />
                    {["scheduled", "confirmed"].includes(job.status) && (
                      <button className="iconButton" onClick={() => completeJob(job)} aria-label="Mark completed" title="Mark completed">
                        <CheckCircle2 size={18} />
                      </button>
                    )}
                  </div>
                </article>
              ))}
              {!visibleJobs.length && <EmptyState title="No jobs in this view">Change the status filter or create a job.</EmptyState>}
            </div>
          </div>
        </section>

        <section className="panel" id="quotes">
          <div className="panelHeader">
            <h2>Quotes</h2>
            <span>{visibleQuotes.length}/{quotes.length}</span>
          </div>
          <QuoteForm customers={customers} onCreate={refresh} />
          <FilterBar value={quoteFilter} options={quoteFilterOptions} onChange={setQuoteFilter} />
          <div className="list">
            {visibleQuotes.map((quote) => (
              <article key={quote.id} className="rowItem split">
                <div>
                  <strong>{quote.number}</strong>
                  <span>{quote.customer.name} · {quote.service_type} · ${quote.amount}</span>
                  <small>Valid until {new Date(`${quote.valid_until}T00:00:00`).toLocaleDateString()}</small>
                </div>
                <div className="rowActions">
                  <StatusPill status={quote.status} tone={statusTone(quote.status)} />
                  {quote.status === "sent" && (
                    <>
                      <button className="iconButton" onClick={() => acceptQuote(quote)} aria-label="Accept quote" title="Accept quote">
                        <CheckCircle2 size={18} />
                      </button>
                      <button className="iconButton" onClick={() => declineQuote(quote)} aria-label="Decline quote" title="Decline quote">
                        <XCircle size={18} />
                      </button>
                    </>
                  )}
                </div>
              </article>
            ))}
            {!visibleQuotes.length && <EmptyState title="No quotes in this view">Change the status filter or create a quote.</EmptyState>}
          </div>
        </section>

        <section className="panel" id="invoices">
          <div className="panelHeader">
            <h2>Invoices</h2>
            <span>{visibleInvoices.length}/{invoices.length}</span>
          </div>
          <InvoiceForm customers={customers} onCreate={refresh} />
          <FilterBar value={invoiceFilter} options={invoiceFilterOptions} onChange={setInvoiceFilter} />
          <div className="list">
            {visibleInvoices.map((invoice) => {
              const displayStatus = invoiceDisplayStatus(invoice);
              return (
                <article key={invoice.id} className="rowItem split">
                  <div>
                    <strong>{invoice.number}</strong>
                    <span>{invoice.customer.name} · ${invoice.amount}</span>
                    <small>Due {new Date(`${invoice.due_date}T00:00:00`).toLocaleDateString()}</small>
                  </div>
                  <div className="rowActions">
                    <StatusPill status={displayStatus} tone={statusTone(displayStatus)} />
                    {invoice.status !== "paid" && invoice.status !== "void" && (
                      <button className="iconButton" onClick={() => markInvoicePaid(invoice)} aria-label="Mark invoice paid" title="Mark invoice paid">
                        <FileText size={18} />
                      </button>
                    )}
                  </div>
                </article>
              );
            })}
            {!visibleInvoices.length && <EmptyState title="No invoices in this view">Change the status filter or create an invoice.</EmptyState>}
          </div>
        </section>

        <section className="grid three" id="automations">
          <div className="panel">
            <div className="panelHeader"><h2>AI suggestions</h2><Sparkles size={18} /></div>
            <div className="list">
              {suggestions.map((suggestion) => (
                <article key={suggestion.title} className="rowItem">
                  <strong>{suggestion.title}</strong>
                  <span>{suggestion.reason}</span>
                  <small>{suggestion.rule}</small>
                </article>
              ))}
            </div>
          </div>
          <div className="panel">
            <div className="panelHeader"><h2>Rules</h2><span>{rules.length}</span></div>
            <div className="list">
              {rules.map((rule) => (
                <article key={rule.id} className="rowItem">
                  <strong>{rule.name}</strong>
                  <span>{rule.trigger}</span>
                  <small>{rule.action}</small>
                </article>
              ))}
            </div>
          </div>
          <div className="panel">
            <div className="panelHeader"><h2>Activity</h2><span>{events.length}</span></div>
            <div className="list">
              {events.map((event) => (
                <article key={event.id} className="rowItem">
                  <strong>{event.status}</strong>
                  <span>{event.message}</span>
                  <small>{new Date(event.created_at).toLocaleString()}</small>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="panelHeader"><h2>Message templates</h2><span>{templates.length}</span></div>
          <div className="templateGrid">
            {templates.map((template) => (
              <article key={template.id} className="template">
                <strong>{template.name}</strong>
                <span>{template.type.replaceAll("_", " ")}</span>
                <p>{template.body}</p>
              </article>
            ))}
          </div>
        </section>

        {nextJob && <p className="footerNote">Next booking: {nextJob.customer.name} for {nextJob.service_type}</p>}
          </>
        )}
      </section>
    </main>
  );
}

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() => hasToken());

  async function loadUser() {
    setLoading(true);
    try {
      setUser(await api.me());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (hasToken()) {
      loadUser();
    }
  }, []);

  if (loading) {
    return <ConnectionState />;
  }
  if (!user) {
    return <AuthScreen onAuthed={loadUser} />;
  }
  return (
    <Workspace
      user={user}
      onLogout={() => {
        clearToken();
        setUser(null);
      }}
    />
  );
}
