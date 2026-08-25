import { useEffect, useRef, useState } from "react";

import CustomerJourney from "./components/CustomerJourney.jsx";
import Customer360Page from "./components/Customer360Page.jsx";
import TicketCategories from "./components/TicketCategories.jsx";
import AiInsights from "./components/AiInsights.jsx";
import Sidebar from "./components/Sidebar.jsx";
import NotificationCenter from "./components/NotificationCenter.jsx";
import LiveSimulation from "./components/LiveSimulation.jsx";
import DataSourcesPage from "./components/DataSourcesPage.jsx";
import LoginPage from "./components/LoginPage.jsx";
import {
  apiFetch,
  getApiErrorMessage,
} from "./api.js";

const NAVIGATION = [
  {
    title: "MAIN",
    items: [
      ["dashboard", "▦", "Dashboard"],
      ["sources", "▤", "Data Sources"],
      ["ingestion", "⇩", "Ingestion"],
      ["explorer", "⌕", "Data Explorer"],
    ],
  },
  {
    title: "JOURNEY",
    items: [
      ["journey", "◌", "Journey Explorer"],
      ["patterns", "⌁", "Journey Patterns"],
      ["customers", "◎", "Customer 360"],
    ],
  },
  {
    title: "ANALYTICS",
    items: [
      ["insights", "✦", "AI Insights"],
      ["risk", "△", "Risk Analysis"],
      ["reports", "▧", "Reports"],
    ],
  },
];

const PAGE_INFO = {
  dashboard: {
    title: "Dashboard",
    subtitle: "Telecom Customer Journey Analytics",
  },
  sources: {
    title: "Data Sources",
    subtitle: "Connected telecom data systems",
  },
  ingestion: {
    title: "Ingestion",
    subtitle: "Data pipeline monitoring",
  },
  explorer: {
    title: "Data Explorer",
    subtitle: "Explore TecJA analytics datasets",
  },
  journey: {
    title: "Journey Explorer",
    subtitle: "Customer journey timeline analysis",
  },
  patterns: {
    title: "Journey Patterns",
    subtitle: "Common customer journey flows",
  },
  customers: {
    title: "Customer 360",
    subtitle: "Customer-level journey analysis",
  },
  insights: {
    title: "AI Insights",
    subtitle: "AI-powered ticket and journey analysis",
  },
  risk: {
    title: "Risk Analysis",
    subtitle: "Customer risk distribution",
  },
  reports: {
    title: "Reports",
    subtitle: "Dashboard reporting tools",
  },
};

const PROFILE_AVATARS = [
  {
    id: "coral",
    label: "Coral",
    primary: "#ff8668",
    secondary: "#ffd6aa",
  },
  {
    id: "ocean",
    label: "Ocean",
    primary: "#58a6ff",
    secondary: "#9fe7ff",
  },
  {
    id: "mint",
    label: "Mint",
    primary: "#47d7c4",
    secondary: "#d3fff2",
  },
  {
    id: "violet",
    label: "Violet",
    primary: "#9a86ff",
    secondary: "#e1d8ff",
  },
  {
    id: "rose",
    label: "Rose",
    primary: "#f06f9e",
    secondary: "#ffd3e1",
  },
  {
    id: "amber",
    label: "Amber",
    primary: "#ffb84d",
    secondary: "#fff0b8",
  },
];

function AvatarArtwork({ avatarId }) {
  const avatar =
    PROFILE_AVATARS.find(
      (item) => item.id === avatarId
    ) || PROFILE_AVATARS[0];

  return (
    <span
      className="profile-avatar-art"
      style={{
        "--avatar-primary": avatar.primary,
        "--avatar-secondary": avatar.secondary,
      }}
      aria-hidden="true"
    >
      <svg viewBox="0 0 48 48">
        <circle
          className="profile-avatar-orbit"
          cx="24"
          cy="24"
          r="18"
        />
        <circle
          className="profile-avatar-head"
          cx="24"
          cy="18"
          r="7"
        />
        <path
          className="profile-avatar-body"
          d="M11 39c1.8-8.1 6.7-12.2 13-12.2S35.2 30.9 37 39"
        />
        <circle
          className="profile-avatar-accent"
          cx="37"
          cy="12"
          r="4"
        />
      </svg>
    </span>
  );
}

function UserProfile({ authUser, onLogout }) {
  const menuRef = useRef(null);
  const storageKey = `tecja_avatar_${
    authUser.email ||
    authUser.username ||
    authUser.name ||
    "user"
  }`;
  const [avatarId, setAvatarId] = useState(
    () =>
      localStorage.getItem(storageKey) ||
      PROFILE_AVATARS[0].id
  );
  const [avatarMenuOpen, setAvatarMenuOpen] =
    useState(false);

  useEffect(() => {
    if (!avatarMenuOpen) {
      return undefined;
    }

    function closeAvatarMenu(event) {
      if (
        !menuRef.current?.contains(event.target)
      ) {
        setAvatarMenuOpen(false);
      }
    }

    function closeWithEscape(event) {
      if (event.key === "Escape") {
        setAvatarMenuOpen(false);
      }
    }

    document.addEventListener(
      "pointerdown",
      closeAvatarMenu
    );
    document.addEventListener(
      "keydown",
      closeWithEscape
    );

    return () => {
      document.removeEventListener(
        "pointerdown",
        closeAvatarMenu
      );
      document.removeEventListener(
        "keydown",
        closeWithEscape
      );
    };
  }, [avatarMenuOpen]);

  function selectAvatar(nextAvatarId) {
    setAvatarId(nextAvatarId);
    localStorage.setItem(
      storageKey,
      nextAvatarId
    );
    setAvatarMenuOpen(false);
  }

  return (
    <div className="profile">
      <div
        className="avatar-picker"
        ref={menuRef}
      >
        <button
          type="button"
          className="avatar avatar-picker-trigger"
          aria-label="Choose profile avatar"
          aria-haspopup="listbox"
          aria-expanded={avatarMenuOpen}
          onClick={() =>
            setAvatarMenuOpen(
              (current) => !current
            )
          }
        >
          <AvatarArtwork avatarId={avatarId} />
        </button>

        {avatarMenuOpen && (
          <div
            className="avatar-picker-menu"
            role="listbox"
            aria-label="Profile avatars"
          >
            <div className="avatar-picker-heading">
              <strong>Choose avatar</strong>
              <small>Your choice is saved</small>
            </div>

            <div className="avatar-picker-grid">
              {PROFILE_AVATARS.map((avatar) => (
                <button
                  key={avatar.id}
                  type="button"
                  className={`avatar-option ${
                    avatar.id === avatarId
                      ? "selected"
                      : ""
                  }`}
                  role="option"
                  aria-selected={
                    avatar.id === avatarId
                  }
                  aria-label={`${avatar.label} avatar`}
                  title={avatar.label}
                  onClick={() =>
                    selectAvatar(avatar.id)
                  }
                >
                  <AvatarArtwork
                    avatarId={avatar.id}
                  />
                  {avatar.id === avatarId && (
                    <span className="avatar-option-check">
                      ✓
                    </span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="profile-copy">
        <strong>User</strong>
        <small>{authUser.role}</small>
      </div>

      <button
        type="button"
        className="logout-button"
        onClick={onLogout}
      >
        Logout
      </button>
    </div>
  );
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("tr-TR");
}

function formatHours(value) {
  return `${Number(value || 0).toFixed(1)}h`;
}

function getRiskClass(value) {
  return String(value || "").toLowerCase();
}

function customerOptionLabel(customer) {
  return `${customer.customer_id || ""} · ${
    customer.first_name || ""
  } ${customer.last_name || ""}`.trim();
}

function downloadReportFile(
  content,
  fileName,
  mimeType
) {
  const blob = new Blob([content], {
    type: mimeType,
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = fileName;
  link.click();

  URL.revokeObjectURL(url);
}

function escapeCsvValue(value) {
  const text = String(value ?? "");
  return `"${text.replaceAll('"', '""')}"`;
}

function buildReportRows({
  summary,
  riskSummary,
  patterns,
  aiData,
  categoryData,
}) {
  const rows = [
    ["TecJA Customer Journey Analytics"],
    ["Generated", new Date().toLocaleString("tr-TR")],
    [],
    ["EXECUTIVE SUMMARY"],
    ["Metric", "Value"],
    ["Total Customers", summary.total_customers],
    ["Journey Events", summary.total_journey_events],
    [
      "Problematic Customers",
      summary.problematic_customers,
    ],
    [
      "High Risk Customers",
      summary.high_risk_customers,
    ],
    ["Total Tickets", summary.total_tickets],
    [
      "Average Resolution Hours",
      summary.average_resolution_hours,
    ],
    [],
    ["RISK DISTRIBUTION"],
    ["Risk Level", "Customer Count", "Average Score"],
  ];

  riskSummary.forEach((risk) => {
    rows.push([
      risk.risk_level,
      risk.customer_count,
      risk.average_risk_score,
    ]);
  });

  rows.push([]);
  rows.push(["JOURNEY PATTERNS"]);
  rows.push(["Pattern", "Customer Count"]);

  patterns.slice(0, 5).forEach((pattern) => {
    rows.push([
      pattern.journey_pattern,
      pattern.customer_count,
    ]);
  });

  rows.push([]);
  rows.push(["AI INSIGHTS"]);

  if (aiData) {
    rows.push([
      "Detected Issue",
      aiData.detected_issue,
    ]);

    rows.push([
      "Ticket Count",
      aiData.ticket_count,
    ]);

    rows.push([
      "Affected Customers",
      aiData.affected_customers,
    ]);

    rows.push([
      "Confidence Percent",
      aiData.confidence_percent,
    ]);

    rows.push([
      "Ticket Share Percent",
      aiData.ticket_share_percent,
    ]);

    rows.push(["Impact", aiData.impact]);

    rows.push([
      "Recommended Action",
      aiData.recommended_action,
    ]);
  }

  rows.push([]);
  rows.push(["TICKET CATEGORIES"]);
  rows.push([
    "Category",
    "Ticket Count",
    "Confidence",
  ]);

  categoryData?.items?.forEach((category) => {
    rows.push([
      category.category,
      category.ticket_count,
      category.average_confidence,
    ]);
  });

  return rows;
}

function KpiCards({ summary }) {
  const cards = [
    [
      "purple",
      "Total Customers",
      summary.total_customers,
      "All registered customers",
    ],
    [
      "blue",
      "Journey Events",
      summary.total_journey_events,
      "Processed journey records",
    ],
    [
      "orange",
      "Problematic Customers",
      summary.problematic_customers,
      "Customers with detected issues",
    ],
    [
      "pink",
      "High Risk Customers",
      summary.high_risk_customers,
      "Customers requiring attention",
    ],
    [
      "mint",
      "Tickets Created",
      summary.total_tickets,
      "Customer support tickets",
    ],
    [
      "cyan",
      "Avg. Resolution Time",
      formatHours(summary.average_resolution_hours),
      "Average completed ticket time",
    ],
  ];

  return (
    <section className="kpi-grid">
      {cards.map((card) => (
        <div
          className={`kpi-card ${card[0]}`}
          key={card[1]}
        >
          <span>{card[1]}</span>

          <strong>
            {typeof card[2] === "number"
              ? formatNumber(card[2])
              : card[2]}
          </strong>

          <small>{card[3]}</small>
        </div>
      ))}
    </section>
  );
}

function PatternPanel({ patterns }) {
  const maximum = Math.max(
    ...patterns.map((item) =>
      Number(item.customer_count || 0)
    ),
    1
  );

  return (
    <div className="panel journey-panel">
      <div className="panel-header">
        <div>
          <h3>Journey Pattern Distribution</h3>
          <p>Most common customer journey flows</p>
        </div>

        <span className="panel-tag">Top 5</span>
      </div>

      <div className="pattern-list">
        {patterns.map((pattern, index) => (
          <div
            className="pattern-row"
            key={pattern.journey_pattern}
          >
            <div className="pattern-number">
              {String(index + 1).padStart(2, "0")}
            </div>

            <div className="pattern-content">
              <div className="pattern-title">
                {pattern.journey_pattern}
              </div>

              <div className="pattern-bar-background">
                <div
                  className="pattern-bar"
                  style={{
                    width: `${
                      (Number(pattern.customer_count) /
                        maximum) *
                      100
                    }%`,
                  }}
                />
              </div>
            </div>

            <strong>
              {formatNumber(pattern.customer_count)}
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskPanel({ riskSummary }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <div>
          <h3>Risk Overview</h3>
          <p>Customer distribution by risk level</p>
        </div>
      </div>

      <div className="risk-list">
        {riskSummary.map((risk) => (
          <div
            className="risk-row"
            key={risk.risk_level}
          >
            <div
              className={`risk-dot ${getRiskClass(
                risk.risk_level
              )}`}
            />

            <span>{risk.risk_level} Risk</span>

            <strong>
              {formatNumber(risk.customer_count)}
            </strong>

            <small>
              Avg. {risk.average_risk_score}
            </small>
          </div>
        ))}
      </div>
    </div>
  );
}

function RiskAnalysisPage({
  riskSummary,
  summary,
  customers,
  setSelectedCustomerId,
  setActivePage,
}) {
  const [actionCustomerId, setActionCustomerId] =
    useState("");
  const [actions, setActions] = useState([]);
  const [actionLoading, setActionLoading] =
    useState(false);
  const [actionMessage, setActionMessage] =
    useState("");
  const [actionCustomerSearch, setActionCustomerSearch] =
    useState("");
  const [actionCustomerOptions, setActionCustomerOptions] =
    useState([]);
  const [actionCustomerOptionsLoading, setActionCustomerOptionsLoading] =
    useState(false);
  const [actionCustomerMenuOpen, setActionCustomerMenuOpen] =
    useState(false);
  const actionCustomerOptionsRef = useRef(null);

  useEffect(() => {
    if (
      !actionCustomerId &&
      customers[0]?.customer_id
    ) {
      setActionCustomerId(customers[0].customer_id);
    }
  }, [customers, actionCustomerId]);

  useEffect(() => {
    let cancelled = false;
    const search = actionCustomerSearch.trim();

    const timer = setTimeout(
      async () => {
        setActionCustomerOptionsLoading(true);

        try {
          const params = new URLSearchParams({
            limit: "20",
            offset: "0",
          });

          if (search) {
            params.set("search", search);
          }

          const response = await apiFetch(
            `/customer-metrics?${params.toString()}`
          );

          if (!response.ok) {
            throw new Error("Customer search failed.");
          }

          const data = await response.json();

          if (!cancelled) {
            setActionCustomerOptions(data.items || []);
          }
        } catch {
          if (!cancelled) {
            setActionCustomerOptions([]);
          }
        } finally {
          if (!cancelled) {
            setActionCustomerOptionsLoading(false);
          }
        }
      },
      search ? 220 : 0
    );

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [actionCustomerSearch]);

  useEffect(() => {
    if (!actionCustomerMenuOpen) {
      return;
    }

    const optionsElement =
      actionCustomerOptionsRef.current;

    if (optionsElement) {
      optionsElement.scrollTop = 0;
    }
  }, [
    actionCustomerMenuOpen,
    actionCustomerSearch,
    actionCustomerOptions,
  ]);

  useEffect(() => {
    if (!actionCustomerId) {
      return undefined;
    }

    let cancelled = false;

    async function loadActions() {
      try {
        const response = await apiFetch(
          `/actions?customer_id=${encodeURIComponent(
            actionCustomerId
          )}`
        );

        if (!response.ok) {
          throw new Error("Actions could not be loaded.");
        }

        const data = await response.json();

        if (!cancelled) {
          setActions(data.items || []);
        }
      } catch {
        if (!cancelled) {
          setActions([]);
        }
      }
    }

    loadActions();

    return () => {
      cancelled = true;
    };
  }, [actionCustomerId]);

  async function createCustomerAction(actionType) {
    if (!actionCustomerId) {
      return;
    }

    setActionLoading(true);
    setActionMessage("");

    try {
      const response = await apiFetch("/actions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          customer_id: actionCustomerId,
          action_type: actionType,
          assigned_to: "Operations",
        }),
      });

      if (!response.ok) {
        throw new Error("Action could not be created.");
      }

      const action = await response.json();
      setActions((current) => [action, ...current]);
      setActionMessage("Action created successfully.");
    } catch (requestError) {
      setActionMessage(requestError.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function updateCustomerAction(actionId, status) {
    try {
      const response = await apiFetch(
        `/actions/${actionId}/status`,
        {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status }),
        }
      );

      if (!response.ok) {
        throw new Error("Action status could not be updated.");
      }

      const updatedAction = await response.json();
      setActions((current) =>
        current.map((action) =>
          action.action_id === updatedAction.action_id
            ? updatedAction
            : action
        )
      );
    } catch (requestError) {
      setActionMessage(requestError.message);
    }
  }

  const totalCustomers = Number(
    summary?.total_customers || 0
  );
  const highRisk = riskSummary.find(
    (risk) => risk.risk_level === "High"
  );
  const highRiskCount = Number(
    highRisk?.customer_count ||
      summary?.high_risk_customers ||
      0
  );
  const highRiskShare = totalCustomers
    ? Math.round((highRiskCount / totalCustomers) * 100)
    : 0;
  const highRiskChurn = Number(
    highRisk?.churned_customers || 0
  );
  const highRiskAverage = Number(
    highRisk?.average_risk_score || 0
  );

  const riskRows = [...riskSummary].sort(
    (left, right) =>
      Number(right.customer_count || 0) -
      Number(left.customer_count || 0)
  );
  const maximumRiskCount = Math.max(
    ...riskRows.map((risk) =>
      Number(risk.customer_count || 0)
    ),
    1
  );

  const priorityCustomers = [...customers]
    .sort(
      (left, right) =>
        Number(right.risk_score || 0) -
        Number(left.risk_score || 0)
    )
    .slice(0, 6);

  const selectedActionCustomer =
    customers.find(
      (customer) =>
        customer.customer_id === actionCustomerId
    ) ||
    actionCustomerOptions.find(
      (customer) =>
        customer.customer_id === actionCustomerId
    );

  const actionCustomerMenuItems =
    selectedActionCustomer &&
    !actionCustomerSearch.trim() &&
    !actionCustomerOptions.some(
      (customer) =>
        customer.customer_id === actionCustomerId
    )
      ? [selectedActionCustomer, ...actionCustomerOptions]
      : actionCustomerOptions;

  function openCustomer(customerId) {
    setSelectedCustomerId(customerId);
    setActivePage("customers");
  }

  return (
    <div className="risk-analysis-page">
      <section className="risk-analysis-hero">
        <div>
          <span className="risk-analysis-kicker">
            CUSTOMER HEALTH MONITOR
          </span>
          <h2>Risk Analysis Overview</h2>
          <p>
            Identify customers that need attention before
            service issues become churn.
          </p>
        </div>

        <div className="risk-health-score">
          <span>HIGH-RISK SHARE</span>
          <strong>{highRiskShare}%</strong>
          <small>
            {formatNumber(highRiskCount)} of{" "}
            {formatNumber(totalCustomers)} customers
          </small>
        </div>
      </section>

      <section className="risk-analysis-metrics">
        <div className="risk-analysis-metric">
          <span>High-risk customers</span>
          <strong>{formatNumber(highRiskCount)}</strong>
          <small>Immediate attention</small>
        </div>

        <div className="risk-analysis-metric">
          <span>Avg. high-risk score</span>
          <strong>{highRiskAverage.toFixed(1)}</strong>
          <small>Across high-risk segment</small>
        </div>

        <div className="risk-analysis-metric">
          <span>Churned high-risk</span>
          <strong>{formatNumber(highRiskChurn)}</strong>
          <small>Retention opportunity</small>
        </div>

        <div className="risk-analysis-metric">
          <span>Total customers</span>
          <strong>{formatNumber(totalCustomers)}</strong>
          <small>Monitored population</small>
        </div>
      </section>

      <section className="risk-analysis-content">
        <div className="panel risk-distribution-panel">
          <div className="panel-header">
            <div>
              <h3>Risk Distribution</h3>
              <p>Customer count by risk level</p>
            </div>
            <span className="panel-tag">LIVE DATA</span>
          </div>

          <div className="risk-distribution-list">
            {riskRows.map((risk) => {
              const count = Number(
                risk.customer_count || 0
              );
              const percentage = totalCustomers
                ? Math.round((count / totalCustomers) * 100)
                : 0;

              return (
                <div
                  className="risk-distribution-row"
                  key={risk.risk_level}
                >
                  <div className="risk-distribution-label">
                    <span
                      className={`risk-dot ${getRiskClass(
                        risk.risk_level
                      )}`}
                    />
                    <strong>{risk.risk_level} Risk</strong>
                    <span>{percentage}%</span>
                  </div>

                  <div className="risk-distribution-track">
                    <span
                      className={getRiskClass(
                        risk.risk_level
                      )}
                      style={{
                        width: `${
                          (count / maximumRiskCount) * 100
                        }%`,
                      }}
                    />
                  </div>

                  <div className="risk-distribution-meta">
                    <strong>{formatNumber(count)}</strong>
                    <small>
                      Avg. {risk.average_risk_score}
                    </small>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="panel risk-priority-panel">
          <div className="panel-header">
            <div>
              <h3>Priority Queue</h3>
              <p>Customers with the highest risk scores</p>
            </div>
            <span className="panel-tag">TOP 6</span>
          </div>

          <div className="risk-priority-list">
            {priorityCustomers.length > 0 ? (
              priorityCustomers.map((customer) => (
                <button
                  type="button"
                  className="risk-priority-row"
                  key={customer.customer_id}
                  onClick={() =>
                    openCustomer(customer.customer_id)
                  }
                >
                  <span className="risk-priority-avatar">
                    {`${customer.first_name?.[0] || ""}${
                      customer.last_name?.[0] || ""
                    }`}
                  </span>
                  <span className="risk-priority-name">
                    <strong>
                      {customer.first_name} {customer.last_name}
                    </strong>
                    <small>
                      {customer.customer_id} · {customer.city}
                    </small>
                  </span>
                  <span className="risk-priority-score">
                    {Number(customer.risk_score || 0)}
                  </span>
                </button>
              ))
            ) : (
              <div className="risk-priority-empty">
                Customer risk data is loading...
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="risk-analysis-note">
        <div>
          <span className="risk-analysis-note-mark">!</span>
          <div>
            <strong>Recommended focus</strong>
            <p>
              Prioritize high-risk customers with failed
              orders, open tickets, or repeated network events.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setActivePage("customers")}
        >
          Open Customer 360
        </button>
      </section>

      <section className="panel action-center-panel">
        <div className="panel-header action-center-header">
          <div>
            <span className="risk-analysis-kicker">
              RISK TO ACTION
            </span>
            <h3>Action Center</h3>
            <p>
              Turn a risk signal into a trackable operation.
            </p>
          </div>

          <div className="action-customer-picker">
            <input
              className="action-customer-search"
              type="search"
              value={actionCustomerSearch}
              placeholder={
                !actionCustomerMenuOpen &&
                selectedActionCustomer
                  ? `Selected: ${customerOptionLabel(
                      selectedActionCustomer
                    )}`
                  : "Search 5,000 customers..."
              }
              aria-label="Search customers"
              onFocus={() =>
                setActionCustomerMenuOpen(true)
              }
              onChange={(event) => {
                setActionCustomerSearch(
                  event.target.value
                );
                setActionCustomerMenuOpen(true);
                setActionMessage("");
              }}
            />

            {actionCustomerMenuOpen && (
              <div
                ref={actionCustomerOptionsRef}
                className="action-customer-options"
              >
                {actionCustomerOptionsLoading ? (
                  <div className="action-customer-option-state">
                    Searching customers...
                  </div>
                ) : actionCustomerMenuItems.length > 0 ? (
                  actionCustomerMenuItems.map((customer) => (
                    <button
                      type="button"
                      className="action-customer-option"
                      key={customer.customer_id}
                      onClick={() => {
                        setActionCustomerId(
                          customer.customer_id
                        );
                        setActionCustomerSearch("");
                        setActionCustomerMenuOpen(false);
                        setActionMessage("");
                      }}
                    >
                      <strong>
                        {customer.first_name} {customer.last_name}
                      </strong>
                      <small>
                        {customer.customer_id} · {customer.city}
                      </small>
                    </button>
                  ))
                ) : (
                  <div className="action-customer-option-state">
                    No customers found.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        <div className="action-center-body">
          <div className="action-center-customer">
            <div className="action-customer-risk">
              <span>Selected customer</span>
              <strong>
                {selectedActionCustomer?.risk_score || "—"}
              </strong>
              <small>Risk score / 100</small>
            </div>

            <div className="action-center-copy">
              <strong>
                {selectedActionCustomer?.first_name || "Customer"}{" "}
                {selectedActionCustomer?.last_name || ""}
              </strong>
              <span>
                Create an operational response and monitor its
                resolution.
              </span>
            </div>
          </div>

          <div className="action-center-buttons">
            <button
              type="button"
              disabled={actionLoading || !actionCustomerId}
              onClick={() =>
                createCustomerAction("Create support ticket")
              }
            >
              Create support ticket
            </button>
            <button
              type="button"
              disabled={actionLoading || !actionCustomerId}
              onClick={() =>
                createCustomerAction("Assign retention call")
              }
            >
              Assign retention call
            </button>
            <button
              type="button"
              disabled={actionLoading || !actionCustomerId}
              onClick={() =>
                createCustomerAction("Start investigation")
              }
            >
              Start investigation
            </button>
          </div>
        </div>

        {actionMessage && (
          <div className="action-center-message">
            {actionMessage}
          </div>
        )}

        <div className="action-history">
          <div className="action-history-heading">
            <strong>Action history</strong>
            <span>{actions.length} recorded</span>
          </div>

          {actions.length > 0 ? (
            <div className="action-history-list">
              {actions.map((action) => (
                <div
                  className="action-history-row"
                  key={action.action_id}
                >
                  <div>
                    <strong>{action.action_type}</strong>
                    <small>
                      {action.action_id} · {action.assigned_to}
                    </small>
                  </div>

                  <select
                    className={`action-status action-status-${action.status
                      .toLowerCase()
                      .replaceAll(" ", "-")}`}
                    value={action.status}
                    onChange={(event) =>
                      updateCustomerAction(
                        action.action_id,
                        event.target.value
                      )
                    }
                  >
                    <option>Pending</option>
                    <option>In Progress</option>
                    <option>Resolved</option>
                  </select>
                </div>
              ))}
            </div>
          ) : (
            <div className="action-history-empty">
              No actions yet. Choose a response above to start.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function OperationalPulse({ summary }) {
  const totalCustomers = Number(
    summary?.total_customers || 0
  );
  const highRiskCustomers = Number(
    summary?.high_risk_customers || 0
  );
  const highRiskRate = totalCustomers
    ? Math.round(
        (highRiskCustomers / totalCustomers) * 100
      )
    : 0;

  const pulseItems = [
    {
      label: "Journey events",
      value: formatNumber(
        summary?.total_journey_events || 0
      ),
      note: "processed records",
    },
    {
      label: "Support tickets",
      value: formatNumber(summary?.total_tickets || 0),
      note: "customer issues",
    },
    {
      label: "High-risk share",
      value: `${highRiskRate}%`,
      note: "of all customers",
    },
  ];

  return (
    <div className="panel operational-pulse-panel">
      <div className="panel-header operational-pulse-header">
        <div>
          <h3>Operational Pulse</h3>
          <p>Current journey activity at a glance</p>
        </div>

        <span className="pulse-status">
          <span className="pulse-status-dot" />
          Live
        </span>
      </div>

      <div className="pulse-metrics">
        {pulseItems.map((item) => (
          <div className="pulse-metric" key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
            <small>{item.note}</small>
          </div>
        ))}
      </div>

      <div className="pulse-footer">
        <span className="pulse-footer-line" />
        <span>Analytics stream is ready</span>
      </div>
    </div>
  );
}

function CustomerPanel({
  customers,
  setSelectedCustomerId,
  searchTerm,
  setSearchTerm,
  riskFilter,
  setRiskFilter,
  customerLoading,
  page,
  setPage,
  pageSize,
  totalCustomers,
}) {
  const totalPages = Math.max(
    1,
    Math.ceil(totalCustomers / pageSize)
  );

  const visibleStart = totalCustomers
    ? (page - 1) * pageSize + 1
    : 0;

  const visibleEnd = Math.min(
    page * pageSize,
    totalCustomers
  );

  return (
    <div className="panel customer-explorer-panel">
      <div className="panel-header customer-header">
        <div>
          <h3>Customer Explorer</h3>
          <p>Search and select a customer</p>
        </div>

        <div className="customer-tools">
          <div className="customer-search-wrap">
            <input
              className="customer-search"
              type="text"
              value={searchTerm}
              onChange={(event) =>
                setSearchTerm(event.target.value)
              }
              placeholder="Search customer..."
              aria-label="Search customers"
            />

            {searchTerm && (
              <button
                type="button"
                className="customer-search-clear"
                onClick={() => setSearchTerm("")}
                aria-label="Clear customer search"
                title="Clear search"
              >
                ×
              </button>
            )}
          </div>

          <select
            className="customer-filter"
            value={riskFilter}
            onChange={(event) =>
              setRiskFilter(event.target.value)
            }
          >
            <option value="">All risks</option>
            <option value="High">High risk</option>
            <option value="Medium">Medium risk</option>
            <option value="Low">Low risk</option>
          </select>
        </div>
      </div>

      <div className="customer-table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>City</th>
              <th>Risk</th>
              <th>Tickets</th>
            </tr>
          </thead>

          <tbody>
            {customerLoading && (
              <tr>
                <td
                  colSpan="4"
                  className="empty-table-state"
                >
                  Customers loading...
                </td>
              </tr>
            )}

            {!customerLoading &&
              customers.length === 0 && (
                <tr>
                  <td
                    colSpan="4"
                    className="empty-table-state"
                  >
                    No matching customers found.
                  </td>
                </tr>
              )}

            {!customerLoading &&
              customers.map((customer) => (
                <tr
                  key={customer.customer_id}
                  className="clickable-row"
                  onClick={() =>
                    setSelectedCustomerId(
                      customer.customer_id
                    )
                  }
                >
                  <td>
                    <div className="customer-name">
                      <div className="mini-avatar">
                        {customer.first_name?.charAt(0)}
                        {customer.last_name?.charAt(0)}
                      </div>

                      <div>
                        <strong>
                          {customer.first_name}{" "}
                          {customer.last_name}
                        </strong>

                        <small>
                          {customer.customer_id}
                        </small>
                      </div>
                    </div>
                  </td>

                  <td>{customer.city}</td>

                  <td>
                    <span
                      className={`risk-badge ${getRiskClass(
                        customer.risk_level
                      )}`}
                    >
                      {customer.risk_score}
                    </span>
                  </td>

                  <td>{customer.total_tickets}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="customer-pagination">
        <button
          type="button"
          disabled={page === 1}
          onClick={() =>
            setPage((current) =>
              Math.max(current - 1, 1)
            )
          }
        >
          Previous
        </button>

        <span className="customer-pagination-summary">
          Showing {visibleStart}-{visibleEnd} of{" "}
          {formatNumber(totalCustomers)} customers · Page{" "}
          {page} of {totalPages}
        </span>

        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() =>
            setPage((current) => current + 1)
          }
        >
          Next
        </button>
      </div>
    </div>
  );
}

function IngestionPage({ summary }) {
  const layers = [
    [
      "Raw",
      summary.total_customers,
      "Customer records",
    ],
    [
      "Bronze",
      summary.total_tickets,
      "Ticket records",
    ],
    [
      "Silver",
      summary.total_journey_events,
      "Clean journey events",
    ],
    [
      "Gold",
      summary.total_journey_events,
      "Analytics-ready datasets",
    ],
  ];

  return (
    <section className="ingestion-page">
      <div className="ingestion-top-grid">
        <div className="panel ingestion-flow-panel">
          <div className="panel-header">
            <div>
              <h3>Data Ingestion Pipeline</h3>
              <p>
                Customer journey data processing flow
              </p>
            </div>

            <span className="panel-tag ingestion-ready-tag">
              Pipeline Active
            </span>
          </div>

          <div className="ingestion-flow">
            {layers.map((layer, index) => (
              <div
                className="ingestion-flow-item"
                key={layer[0]}
              >
                <div className="ingestion-stage-card">
                  <span className="ingestion-stage-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <span className="ingestion-stage-name">
                    {layer[0]}
                  </span>

                  <strong>
                    {formatNumber(layer[1])}
                  </strong>

                  <small>{layer[2]}</small>

                  <span className="ingestion-stage-status">
                    Ready
                  </span>
                </div>

                {index < layers.length - 1 && (
                  <div className="ingestion-connector">
                    <span />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="panel ingestion-health-panel">
          <div className="panel-header">
            <div>
              <h3>Pipeline Health</h3>
              <p>Current processing status</p>
            </div>
          </div>

          <div className="health-status">
            <span className="health-dot" />

            <div>
              <strong>All systems healthy</strong>
              <small>
                No ingestion errors detected
              </small>
            </div>
          </div>

          <div className="health-progress">
            <div className="health-progress-label">
              <span>Pipeline completion</span>
              <strong>100%</strong>
            </div>

            <div className="health-progress-track">
              <span />
            </div>
          </div>

          <div className="health-metrics">
            <div>
              <span>Last run</span>
              <strong>Just now</strong>
            </div>

            <div>
              <span>Failed jobs</span>
              <strong>0</strong>
            </div>

            <div>
              <span>Active layers</span>
              <strong>4 / 4</strong>
            </div>

            <div>
              <span>Data quality</span>
              <strong>98.6%</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ExplorerPage({ summary }) {
  const [activeDataset, setActiveDataset] =
    useState("customers");

  const [datasetRows, setDatasetRows] = useState([]);
  const [datasetLoading, setDatasetLoading] =
    useState(false);
  const [datasetError, setDatasetError] =
    useState("");

  const [explorerPage, setExplorerPage] =
    useState(1);

  const explorerPageSize = 25;

  const [totalRows, setTotalRows] = useState(0);

  const datasetTitles = {
    customers: "Customers",
    patterns: "Journey Patterns",
    categories: "Ticket Categories",
    risk: "Risk Summary",
  };

  const datasetTitle =
    datasetTitles[activeDataset];

  const totalPages = Math.max(
    1,
    Math.ceil(totalRows / explorerPageSize)
  );

  useEffect(() => {
    setExplorerPage(1);
  }, [activeDataset]);

  useEffect(() => {
    let cancelled = false;

    async function loadDataset() {
      setDatasetLoading(true);
      setDatasetError("");

      try {
        let endpoint = "";

        if (activeDataset === "customers") {
          const offset =
            (explorerPage - 1) *
            explorerPageSize;

          endpoint =
            `/customer-metrics?limit=${explorerPageSize}` +
            `&offset=${offset}`;
        }

        if (activeDataset === "patterns") {
          endpoint =
            "/journey-patterns?limit=1000";
        }

        if (activeDataset === "categories") {
          endpoint = "/ticket-categories";
        }

        if (activeDataset === "risk") {
          endpoint = "/risk-summary";
        }

        const response = await apiFetch(endpoint);

        if (!response.ok) {
          throw new Error(
            "Dataset verileri alınamadı."
          );
        }

        const data = await response.json();

        if (cancelled) {
          return;
        }

        const items = data.items || [];

        setDatasetRows(items);

        if (activeDataset === "customers") {
          setTotalRows(
            Number(
              data.total_count ??
                data.count ??
                items.length
            )
          );
        } else {
          setTotalRows(
            Number(data.count ?? items.length)
          );
        }
      } catch (requestError) {
        if (!cancelled) {
          setDatasetRows([]);
          setTotalRows(0);
          setDatasetError(
            getApiErrorMessage(requestError)
          );
        }
      } finally {
        if (!cancelled) {
          setDatasetLoading(false);
        }
      }
    }

    loadDataset();

    return () => {
      cancelled = true;
    };
  }, [activeDataset, explorerPage]);

  const visibleRows =
    activeDataset === "customers"
      ? datasetRows
      : datasetRows.slice(
          (explorerPage - 1) *
            explorerPageSize,
          explorerPage * explorerPageSize
        );

  function renderTable() {
    if (datasetLoading) {
      return (
        <div className="explorer-empty-state">
          Dataset loading...
        </div>
      );
    }

    if (datasetError) {
      return (
        <div className="explorer-empty-state explorer-error">
          {datasetError}
        </div>
      );
    }

    if (!visibleRows.length) {
      return (
        <div className="explorer-empty-state">
          Bu dataset içerisinde kayıt bulunamadı.
        </div>
      );
    }

    if (activeDataset === "customers") {
      return (
        <table className="explorer-table">
          <thead>
            <tr>
              <th>Customer ID</th>
              <th>Name</th>
              <th>City</th>
              <th>Plan</th>
              <th>Status</th>
              <th>Risk</th>
              <th>Tickets</th>
            </tr>
          </thead>

          <tbody>
            {visibleRows.map((row) => (
              <tr key={row.customer_id}>
                <td>{row.customer_id}</td>

                <td>
                  {row.first_name} {row.last_name}
                </td>

                <td>{row.city}</td>
                <td>{row.plan}</td>
                <td>{row.status}</td>

                <td>
                  <span
                    className={`explorer-risk-badge ${getRiskClass(
                      row.risk_level
                    )}`}
                  >
                    {row.risk_score}
                  </span>
                </td>

                <td>{row.total_tickets}</td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (activeDataset === "patterns") {
      return (
        <table className="explorer-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Journey Pattern</th>
              <th>Customer Count</th>
            </tr>
          </thead>

          <tbody>
            {visibleRows.map((row, index) => (
              <tr
                key={`${row.journey_pattern}-${index}`}
              >
                <td>
                  {String(
                    (explorerPage - 1) *
                      explorerPageSize +
                      index +
                      1
                  ).padStart(2, "0")}
                </td>

                <td>{row.journey_pattern}</td>

                <td>
                  {formatNumber(
                    row.customer_count
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    if (activeDataset === "categories") {
      return (
        <table className="explorer-table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Ticket Count</th>
              <th>Average Confidence</th>
            </tr>
          </thead>

          <tbody>
            {visibleRows.map((row) => (
              <tr key={row.category}>
                <td>{row.category}</td>

                <td>
                  {formatNumber(row.ticket_count)}
                </td>

                <td>
                  {Number(
                    row.average_confidence || 0
                  ).toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      );
    }

    return (
      <table className="explorer-table">
        <thead>
          <tr>
            <th>Risk Level</th>
            <th>Customer Count</th>
            <th>Churned Customers</th>
            <th>Average Risk Score</th>
          </tr>
        </thead>

        <tbody>
          {visibleRows.map((row) => (
            <tr key={row.risk_level}>
              <td>
                <span
                  className={`explorer-risk-label ${getRiskClass(
                    row.risk_level
                  )}`}
                >
                  {row.risk_level}
                </span>
              </td>

              <td>
                {formatNumber(row.customer_count)}
              </td>

              <td>
                {formatNumber(
                  row.churned_customers
                )}
              </td>

              <td>{row.average_risk_score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  return (
    <section className="explorer-page">
      <div className="panel explorer-summary-panel">
        <div className="panel-header">
          <div>
            <h3>Data Explorer</h3>
            <p>
              Explore live TecJA analytics datasets
            </p>
          </div>

          <span className="panel-tag">
            Live database
          </span>
        </div>

        <div className="explorer-grid">
          <button
            type="button"
            className={`explorer-card ${
              activeDataset === "customers"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActiveDataset("customers")
            }
          >
            <span>Customers</span>

            <strong>
              {formatNumber(summary.total_customers)}
            </strong>

            <small>5.000 customer records</small>
          </button>

          <button
            type="button"
            className={`explorer-card ${
              activeDataset === "patterns"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActiveDataset("patterns")
            }
          >
            <span>Journey Patterns</span>

            <strong>
              {formatNumber(
                summary.total_journey_events
              )}
            </strong>

            <small>Journey event records</small>
          </button>

          <button
            type="button"
            className={`explorer-card ${
              activeDataset === "categories"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActiveDataset("categories")
            }
          >
            <span>Tickets</span>

            <strong>
              {formatNumber(summary.total_tickets)}
            </strong>

            <small>Support ticket records</small>
          </button>

          <button
            type="button"
            className={`explorer-card ${
              activeDataset === "risk"
                ? "active"
                : ""
            }`}
            onClick={() =>
              setActiveDataset("risk")
            }
          >
            <span>Risk Summary</span>

            <strong>
              {formatNumber(
                summary.high_risk_customers
              )}
            </strong>

            <small>Risk analysis records</small>
          </button>
        </div>
      </div>

      <div className="panel explorer-data-panel">
        <div className="panel-header">
          <div>
            <h3>{datasetTitle}</h3>

            <p>
              Showing live records from TecJA database
            </p>
          </div>

          <span className="explorer-record-count">
            {totalRows} total records
          </span>
        </div>

        <div className="explorer-table-wrapper">
          {renderTable()}
        </div>

        {totalPages > 1 && (
          <div className="explorer-pagination">
            <button
              type="button"
              disabled={explorerPage === 1}
              onClick={() =>
                setExplorerPage((page) =>
                  Math.max(page - 1, 1)
                )
              }
            >
              Previous
            </button>

            <span>
              Page {explorerPage} of {totalPages}
            </span>

            <button
              type="button"
              disabled={
                explorerPage >= totalPages
              }
              onClick={() =>
                setExplorerPage((page) =>
                  Math.min(page + 1, totalPages)
                )
              }
            >
              Next
            </button>
          </div>
        )}
      </div>
    </section>
  );
}

function ReportsPage({
  summary,
  riskSummary,
  patterns,
  refreshVersion,
}) {
  const [aiData, setAiData] = useState(null);
  const [categoryData, setCategoryData] =
    useState(null);
  const [reportEmail, setReportEmail] =
    useState("");
  const [emailSending, setEmailSending] =
    useState(false);
  const [emailFeedback, setEmailFeedback] =
    useState(null);

  useEffect(() => {
    async function loadReportData() {
      try {
        const [
          aiResponse,
          categoryResponse,
        ] = await Promise.all([
          apiFetch("/ai-insights"),
          apiFetch("/ticket-categories"),
        ]);

        if (
          !aiResponse.ok ||
          !categoryResponse.ok
        ) {
          return;
        }

        setAiData(await aiResponse.json());
        setCategoryData(
          await categoryResponse.json()
        );
      } catch {
        setAiData(null);
        setCategoryData(null);
      }
    }

    loadReportData();
  }, [refreshVersion]);

  function exportCsv() {
    const rows = buildReportRows({
      summary,
      riskSummary,
      patterns,
      aiData,
      categoryData,
    });

    const csv = rows
      .map((row) =>
        row
          .map((value) =>
            escapeCsvValue(value)
          )
          .join(",")
      )
      .join("\r\n");

    downloadReportFile(
      "\uFEFF" + csv,
      "tecja-customer-journey-report.csv",
      "text/csv;charset=utf-8"
    );
  }

  function exportExcel() {
    const rows = buildReportRows({
      summary,
      riskSummary,
      patterns,
      aiData,
      categoryData,
    });

    const tableRows = rows
      .map(
        (row) => `
          <tr>
            ${row
              .map(
                (value) =>
                  `<td>${String(
                    value ?? ""
                  )}</td>`
              )
              .join("")}
          </tr>
        `
      )
      .join("");

    const excelDocument = `
      <html>
        <head>
          <meta charset="UTF-8" />
        </head>
        <body>
          <table border="1">
            ${tableRows}
          </table>
        </body>
      </html>
    `;

    downloadReportFile(
      "\uFEFF" + excelDocument,
      "tecja-customer-journey-report.xls",
      "application/vnd.ms-excel"
    );
  }

  function printReport() {
    const previousTitle = document.title;

    document.documentElement.classList.add(
      "report-printing"
    );

    document.title =
      "TecJA Customer Journey Intelligence Report";

    window.setTimeout(() => {
      window.print();
    }, 0);

    window.setTimeout(() => {
      document.documentElement.classList.remove(
        "report-printing"
      );
      document.title = previousTitle;
    }, 1500);
  }

  async function emailPdfReport(event) {
    event.preventDefault();

    const recipient = reportEmail.trim();

    if (!recipient) {
      setEmailFeedback({
        type: "error",
        message: "Alıcı e-posta adresini girin.",
      });
      return;
    }

    setEmailSending(true);
    setEmailFeedback(null);

    try {
      const response = await apiFetch(
        "/reports/email",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ recipient }),
          timeoutMs: 30000,
        }
      );

      const result = await response
        .json()
        .catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          getApiErrorMessage(result)
        );
      }

      setEmailFeedback({
        type: "success",
        message:
          result.message ||
          "PDF raporu e-posta ile gönderildi.",
      });
    } catch (error) {
      setEmailFeedback({
        type: "error",
        message: getApiErrorMessage(error),
      });
    } finally {
      setEmailSending(false);
    }
  }

  const categories = categoryData?.items || [];

  return (
    <section className="report-page">
      <div className="report-toolbar">
        <form
          className="report-email-form"
          onSubmit={emailPdfReport}
        >
          <label htmlFor="report-recipient-email">
            E-posta ile gönder
          </label>

          <div className="report-email-row">
            <input
              id="report-recipient-email"
              type="email"
              value={reportEmail}
              onChange={(event) =>
                setReportEmail(event.target.value)
              }
              placeholder="E-posta adresini gir"
              autoComplete="email"
              required
            />

            <button
              type="submit"
              className="report-email-button"
              disabled={emailSending}
            >
              {emailSending
                ? "Gönderiliyor..."
                : "E-postaya gönder"}
            </button>
          </div>

          <p
            className={`report-email-feedback ${emailFeedback?.type || ""}`}
            role="status"
          >
            {emailFeedback?.message ||
              "PDF raporu yazdığınız kişisel veya kurumsal adrese gönderilir."}
          </p>
        </form>

        <div className="report-actions">
          <span className="report-actions-label">
            Raporu indir
          </span>

          <div className="report-actions-row">
            <button
              type="button"
              className="report-export-button"
              onClick={exportCsv}
            >
              CSV indir
            </button>

            <button
              type="button"
              className="report-export-button"
              onClick={exportExcel}
            >
              Excel indir
            </button>

            <button
              type="button"
              className="report-print-button"
              onClick={printReport}
            >
              PDF indir
            </button>
          </div>
        </div>
      </div>

      <article className="report-document">
        <header className="report-header">
          <div>
            <div className="report-brand">
              <img
                src="/tecja-logo.svg"
                alt="TecJA Journey Intelligence"
              />
              <span>TecJA Analytics</span>
            </div>

            <span className="report-kicker">
              TECJA ANALYTICS
            </span>

            <h1>
              Customer Journey Intelligence Report
            </h1>

            <p>
              Telecom customer journey and AI analysis
            </p>
          </div>

          <div className="report-meta">
            <strong>Generated</strong>

            <span>
              {new Date().toLocaleString("tr-TR")}
            </span>

            <small>Live analytics snapshot</small>
          </div>
        </header>

        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">
              01
            </span>

            <div>
              <h2>Executive Summary</h2>
              <p>Overall platform status.</p>
            </div>
          </div>

          <div className="report-kpi-grid">
            <div className="report-kpi">
              <span>Total Customers</span>

              <strong>
                {formatNumber(
                  summary.total_customers
                )}
              </strong>
            </div>

            <div className="report-kpi">
              <span>Journey Events</span>

              <strong>
                {formatNumber(
                  summary.total_journey_events
                )}
              </strong>
            </div>

            <div className="report-kpi">
              <span>High Risk Customers</span>

              <strong>
                {formatNumber(
                  summary.high_risk_customers
                )}
              </strong>
            </div>

            <div className="report-kpi">
              <span>Total Tickets</span>

              <strong>
                {formatNumber(
                  summary.total_tickets
                )}
              </strong>
            </div>
          </div>

          <div className="report-highlight">
            <span>Operational insight</span>

            <strong>
              {formatNumber(
                summary.problematic_customers
              )}{" "}
              customers require attention.
            </strong>

            <p>
              Average resolution time:{" "}
              {Number(
                summary.average_resolution_hours
              ).toFixed(1)}
              hours.
            </p>
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">
              02
            </span>

            <div>
              <h2>Risk Distribution</h2>
              <p>Customer risk distribution.</p>
            </div>
          </div>

          <div className="report-risk-list">
            {riskSummary.map((risk) => (
              <div
                className="report-risk-row"
                key={risk.risk_level}
              >
                <div className="report-risk-name">
                  <span
                    className={`report-risk-dot ${getRiskClass(
                      risk.risk_level
                    )}`}
                  />

                  <strong>
                    {risk.risk_level} Risk
                  </strong>
                </div>

                <span>
                  {formatNumber(
                    risk.customer_count
                  )}{" "}
                  customers
                </span>

                <strong>
                  Avg. {risk.average_risk_score}
                </strong>
              </div>
            ))}
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">
              03
            </span>

            <div>
              <h2>Journey Pattern Analysis</h2>
              <p>Most frequent journey flows.</p>
            </div>
          </div>

          <div className="report-pattern-list">
            {patterns.slice(0, 5).map((pattern, index) => (
              <div
                className="report-pattern-row"
                key={pattern.journey_pattern}
              >
                <span className="report-pattern-index">
                  {String(index + 1).padStart(2, "0")}
                </span>

                <div>
                  <strong>
                    {pattern.journey_pattern}
                  </strong>

                  <small>
                    {formatNumber(
                      pattern.customer_count
                    )}{" "}
                    customers
                  </small>
                </div>

                <span className="report-pattern-value">
                  {formatNumber(
                    pattern.customer_count
                  )}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">
              04
            </span>

            <div>
              <h2>AI Ticket Analysis</h2>
              <p>Zero-shot classification results.</p>
            </div>
          </div>

          {aiData && (
            <>
              <div className="report-ai-summary">
                <div>
                  <span>Detected issue</span>
                  <strong>
                    {aiData.detected_issue}
                  </strong>
                </div>

                <div>
                  <span>Confidence</span>
                  <strong>
                    %{aiData.confidence_percent}
                  </strong>
                </div>

                <div>
                  <span>Ticket share</span>
                  <strong>
                    %{aiData.ticket_share_percent}
                  </strong>
                </div>

                <div>
                  <span>Affected customers</span>
                  <strong>
                    {formatNumber(
                      aiData.affected_customers
                    )}
                  </strong>
                </div>
              </div>

              <div className="report-recommendation">
                <span>Recommended action</span>

                <p>
                  {aiData.recommended_action}
                </p>
              </div>
            </>
          )}
        </section>

        <section className="report-section">
          <div className="report-section-heading">
            <span className="report-section-number">
              05
            </span>

            <div>
              <h2>Ticket Category Distribution</h2>
              <p>AI-classified ticket categories.</p>
            </div>
          </div>

          <div className="report-category-list">
            {categories.map((category) => {
              const total = Number(
                categoryData?.total_tickets || 0
              );

              const percentage =
                total > 0
                  ? Math.round(
                      (Number(
                        category.ticket_count
                      ) /
                        total) *
                        100
                    )
                  : 0;

              return (
                <div
                  className="report-category-row"
                  key={category.category}
                >
                  <div>
                    <strong>
                      {category.category}
                    </strong>

                    <div className="report-category-track">
                      <span
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>

                  <span>
                    {formatNumber(
                      category.ticket_count
                    )}
                  </span>

                  <small>%{percentage}</small>
                </div>
              );
            })}
          </div>
        </section>

        <footer className="report-footer">
          <span>
            TecJA Customer Journey Analytics
          </span>

          <span>
            Confidential internal report
          </span>
        </footer>
      </article>
    </section>
  );
}

function App() {
  const [authUser, setAuthUser] = useState(() => {
    const savedToken = localStorage.getItem(
      "tecja_token"
    );
    const savedUser =
      localStorage.getItem("tecja_user");

    if (!savedToken || !savedUser) {
      localStorage.removeItem("tecja_token");
      localStorage.removeItem("tecja_user");
      return null;
    }

    try {
      return JSON.parse(savedUser);
    } catch {
      return null;
    }
  });

  const [activePage, setActivePage] =
    useState("dashboard");

  const [summary, setSummary] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [riskSummary, setRiskSummary] = useState([]);
  const [customers, setCustomers] = useState([]);

  const [
    selectedCustomerId,
    setSelectedCustomerId,
  ] = useState("");

  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("");

  const [customerLoading, setCustomerLoading] =
    useState(false);

  const [customerPage, setCustomerPage] =
    useState(1);

  const customerPageSize = 50;

  const [totalCustomers, setTotalCustomers] =
    useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [
    dataRefreshVersion,
    setDataRefreshVersion,
  ] = useState(0);

  const [retryVersion, setRetryVersion] =
    useState(0);

  useEffect(() => {
    function handleDataUpdated() {
      setDataRefreshVersion(
        (current) => current + 1
      );
    }

    window.addEventListener(
      "tecja:data-updated",
      handleDataUpdated
    );

    return () => {
      window.removeEventListener(
        "tecja:data-updated",
        handleDataUpdated
      );
    };
  }, []);

  useEffect(() => {
    function handleAuthExpired() {
      setAuthUser(null);
      setSummary(null);
      setPatterns([]);
      setRiskSummary([]);
      setCustomers([]);
      setError("");
      setLoading(false);
    }

    window.addEventListener(
      "tecja:auth-expired",
      handleAuthExpired
    );

    return () => {
      window.removeEventListener(
        "tecja:auth-expired",
        handleAuthExpired
      );
    };
  }, []);

  useEffect(() => {
    setCustomerPage(1);
  }, [searchTerm, riskFilter]);

  useEffect(() => {
    if (!authUser) {
      return;
    }

    async function loadDashboardData() {
      try {
        const [
          summaryResponse,
          patternsResponse,
          riskResponse,
        ] = await Promise.all([
          apiFetch("/summary"),
          apiFetch("/journey-patterns?limit=5"),
          apiFetch("/risk-summary"),
        ]);

        if (
          !summaryResponse.ok ||
          !patternsResponse.ok ||
          !riskResponse.ok
        ) {
          if (
            summaryResponse.status === 401 ||
            patternsResponse.status === 401 ||
            riskResponse.status === 401
          ) {
            localStorage.removeItem(
              "tecja_token"
            );
            localStorage.removeItem(
              "tecja_user"
            );
            setAuthUser(null);
            return;
          }

          throw new Error(
            "Dashboard verileri alınamadı."
          );
        }

        const summaryData =
          await summaryResponse.json();

        const patternsData =
          await patternsResponse.json();

        const riskData =
          await riskResponse.json();

        setSummary(summaryData);
        setPatterns(patternsData.items || []);
        setRiskSummary(riskData.items || []);
        setError("");
      } catch (requestError) {
        setError(getApiErrorMessage(requestError));
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, [
    authUser,
    dataRefreshVersion,
    retryVersion,
  ]);

  useEffect(() => {
    if (!authUser) {
      return;
    }

    let cancelled = false;

    async function loadCustomers() {
      setCustomerLoading(true);

      try {
        const params = new URLSearchParams();

        params.set(
          "limit",
          String(customerPageSize)
        );

        params.set(
          "offset",
          String(
            (customerPage - 1) *
              customerPageSize
          )
        );

        if (searchTerm.trim()) {
          params.set(
            "search",
            searchTerm.trim()
          );
        }

        if (riskFilter) {
          params.set(
            "risk_level",
            riskFilter
          );
        }

        const response = await apiFetch(
          `/customer-metrics?${params.toString()}`
        );

        if (!response.ok) {
          throw new Error(
            "Müşteri verileri alınamadı."
          );
        }

        const data = await response.json();

        if (cancelled) {
          return;
        }

        setCustomers(data.items || []);

        setTotalCustomers(
          Number(
            data.total_count ??
              data.count ??
              0
          )
        );

        setSelectedCustomerId((currentId) => {
          if (!data.items?.length) {
            return "";
          }

          const exists = data.items.some(
            (customer) =>
              customer.customer_id === currentId
          );

          return exists
            ? currentId
            : data.items[0].customer_id;
        });
      } catch (requestError) {
        if (!cancelled) {
          setError(getApiErrorMessage(requestError));
        }
      } finally {
        if (!cancelled) {
          setCustomerLoading(false);
        }
      }
    }

    loadCustomers();

    return () => {
      cancelled = true;
    };
  }, [
    authUser,
    searchTerm,
    riskFilter,
    customerPage,
    dataRefreshVersion,
  ]);

  if (!authUser) {
    return (
      <LoginPage
        onLogin={(user) => {
          setAuthUser(user);
          setLoading(true);
          setError("");
        }}
      />
    );
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-card">
          <span className="loading-mark">TJ</span>
          <strong>Workspace loading</strong>
          <span>Analytics workspace hazırlanıyor...</span>
          <div className="loading-track">
            <span />
          </div>
        </div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className="error-screen connection-screen">
        <div className="connection-card">
          <span className="connection-mark">!</span>
          <span className="connection-eyebrow">
            TECJA WORKSPACE
          </span>
          <h2>Dashboard verisi alınamadı</h2>
          <p>{error}</p>
          <button
            type="button"
            onClick={() => {
              setError("");
              setLoading(true);
              setRetryVersion(
                (current) => current + 1
              );
            }}
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const pageInfo =
    PAGE_INFO[activePage] || PAGE_INFO.dashboard;

  const customerPanelProps = {
    customers,
    setSelectedCustomerId,
    searchTerm,
    setSearchTerm,
    riskFilter,
    setRiskFilter,
    customerLoading,
    page: customerPage,
    setPage: setCustomerPage,
    pageSize: customerPageSize,
    totalCustomers,
  };

  function renderPage() {
    if (activePage === "dashboard") {
      return (
        <>
          <KpiCards summary={summary} />

          <section className="main-grid">
            <PatternPanel patterns={patterns} />

            <AiInsights
              refreshVersion={dataRefreshVersion}
            />
          </section>

          <section className="bottom-grid">
            <div className="bottom-left-stack">
              <RiskPanel riskSummary={riskSummary} />

              <OperationalPulse summary={summary} />
            </div>

            <CustomerPanel
              {...customerPanelProps}
            />
          </section>
        </>
      );
    }

    if (activePage === "sources") {
      return (
        <DataSourcesPage summary={summary} />
      );
    }

    if (activePage === "ingestion") {
      return (
        <IngestionPage summary={summary} />
      );
    }

    if (activePage === "explorer") {
      return (
        <ExplorerPage summary={summary} />
      );
    }

    if (activePage === "journey") {
      return (
        <div className="page-stack">
          <CustomerJourney
            customerId={selectedCustomerId}
            refreshVersion={dataRefreshVersion}
          />
        </div>
      );
    }

    if (activePage === "patterns") {
      return (
        <PatternPanel patterns={patterns} />
      );
    }

    if (activePage === "customers") {
      const selectedCustomer = customers.find(
        (customer) =>
          customer.customer_id ===
          selectedCustomerId
      );

      return (
        <div className="page-stack">
          <CustomerPanel
            {...customerPanelProps}
          />

          <Customer360Page
            customer={selectedCustomer}
            refreshVersion={dataRefreshVersion}
          />
        </div>
      );
    }

    if (activePage === "insights") {
      return (
        <div className="page-stack">
          <AiInsights
            refreshVersion={dataRefreshVersion}
          />

          <TicketCategories
            refreshVersion={dataRefreshVersion}
          />
        </div>
      );
    }

    if (activePage === "risk") {
      return (
        <RiskAnalysisPage
          riskSummary={riskSummary}
          summary={summary}
          customers={customers}
          setSelectedCustomerId={setSelectedCustomerId}
          setActivePage={setActivePage}
        />
      );
    }

    if (activePage === "reports") {
      return (
        <ReportsPage
          summary={summary}
          riskSummary={riskSummary}
          patterns={patterns}
          refreshVersion={dataRefreshVersion}
          defaultEmail={authUser?.email || ""}
        />
      );
    }

    return null;
  }

  return (
    <div className="app-shell">
      <Sidebar
        navigation={NAVIGATION}
        activePage={activePage}
        setActivePage={setActivePage}
      />

      <main className="main-content">
        <header className="topbar">
          <div>
            <h2>{pageInfo.title}</h2>
            <p>{pageInfo.subtitle}</p>
          </div>

          <div className="topbar-actions">
            {authUser.role === "admin" && (
              <LiveSimulation />
            )}

            <div className="topbar-divider" />

            <NotificationCenter
              onOpenCustomer={(customerId) => {
                setSearchTerm(customerId);
                setRiskFilter("");
                setCustomerPage(1);
                setSelectedCustomerId(customerId);
                setActivePage("customers");
              }}
            />

            <UserProfile
              authUser={authUser}
              onLogout={() => {
                localStorage.removeItem(
                  "tecja_token"
                );

                localStorage.removeItem(
                  "tecja_user"
                );

                setAuthUser(null);
                setSummary(null);
                setLoading(true);
              }}
            />
          </div>
        </header>

        {error && summary && (
          <div
            className="global-error-banner"
            role="alert"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => {
                setError("");
                setRetryVersion(
                  (current) => current + 1
                );
              }}
            >
              Retry
            </button>
          </div>
        )}

        {renderPage()}
      </main>
    </div>
  );
}

export default App;
