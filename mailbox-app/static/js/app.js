"use strict";

const VibMail = (() => {
  const MAX_NOTIFIED = 200;
  const STORAGE_KEY = "vibmail-notified-message-uuids";
  const SIDEBAR_STORAGE_KEY = "mailstack-sidebar-collapsed";
  let cursor = 0;
  let bootstrapped = false;
  let polling = false;
  let backoff = 5000;
  let timer = null;
  let notified = new Set();
  let channel = null;

  function loadNotified() {
    try {
      const values = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
      notified = new Set(Array.isArray(values) ? values.slice(-MAX_NOTIFIED) : []);
    } catch (_error) {
      notified = new Set();
    }
  }

  function saveNotified() {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(notified).slice(-MAX_NOTIFIED)));
    } catch (_error) {
      // Private browsing or storage restrictions must not break live updates.
    }
  }

  function markNotified(uuid) {
    if (notified.has(uuid)) return false;
    notified.add(uuid);
    if (notified.size > MAX_NOTIFIED) notified.delete(notified.values().next().value);
    saveNotified();
    if (channel) channel.postMessage({ type: "notified", uuid });
    return true;
  }

  async function claimNotification(uuid) {
    if (navigator.locks?.request) {
      let claimed = false;
      await navigator.locks.request(`vibmail-notification-${uuid}`, async () => {
        loadNotified();
        claimed = markNotified(uuid);
      });
      return claimed;
    }
    loadNotified();
    return markNotified(uuid);
  }

  function toast(message, { href = "", tone = "info", timeout = 7000 } = {}) {
    const region = document.querySelector("#toast-region");
    if (!region) return;
    const item = document.createElement(href ? "a" : "div");
    item.className = `toast toast-${tone}`;
    if (href) item.href = href;
    const text = document.createElement("span");
    text.textContent = message;
    item.append(text);
    region.append(item);
    window.setTimeout(() => item.remove(), timeout);
  }

  async function copyText(value) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        const input = document.createElement("textarea");
        input.value = value;
        input.setAttribute("readonly", "");
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.append(input);
        input.select();
        const copied = document.execCommand("copy");
        input.remove();
        if (!copied) throw new Error("Copy command failed");
      }
      toast(`Copied ${value}`, { tone: "success", timeout: 3000 });
    } catch (_error) {
      toast("Unable to copy the address.", { tone: "error", timeout: 4000 });
    }
  }

  function formatDate(value, fallback = "—") {
    if (!value) return fallback;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return fallback;
    return new Intl.DateTimeFormat(undefined, {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  function formatShortDate(value) {
    if (!value) return "Unknown date";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "Unknown date";
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  function formatBytes(bytes) {
    const value = Number(bytes || 0);
    if (value < 1024) return `${value} bytes`;
    if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
    return `${(value / (1024 * 1024)).toFixed(1)} MB`;
  }

  function updateSummary(summary) {
    Object.entries(summary || {}).forEach(([key, value]) => {
      document.querySelectorAll(`[data-live-summary="${key}"]`).forEach((node) => {
        node.textContent = key === "last_received" ? formatDate(value, "No email yet") : String(value);
      });
    });
  }

  function updateMailbox(mailbox) {
    const uuid = mailbox.uuid;
    document.querySelectorAll(`[data-live-mailbox-total="${uuid}"]`).forEach((node) => {
      node.textContent = String(mailbox.total_messages);
    });
    document.querySelectorAll(`[data-live-mailbox-unread="${uuid}"]`).forEach((node) => {
      node.textContent = String(mailbox.unread_messages);
    });
    document.querySelectorAll(`[data-live-mailbox-last="${uuid}"]`).forEach((node) => {
      node.textContent = formatDate(mailbox.last_received_at);
    });
    document.querySelectorAll(`[data-live-mailbox-status="${uuid}"]`).forEach((node) => {
      node.textContent = mailbox.status.charAt(0).toUpperCase() + mailbox.status.slice(1);
      node.className = `badge badge-${mailbox.status}`;
    });
  }

  function buildMessageRow(message) {
    const link = document.createElement("a");
    link.className = `message-row${message.is_read ? "" : " unread"}`;
    link.href = message.detail_url;
    link.dataset.messageUuid = message.uuid;

    const status = document.createElement("div");
    status.className = "message-status";
    status.setAttribute("aria-label", message.is_read ? "Read" : "Unread");

    const sender = document.createElement("div");
    sender.className = "message-sender";
    const senderStrong = document.createElement("strong");
    senderStrong.className = "truncate";
    senderStrong.textContent = message.sender_name || message.sender_address || "Unknown sender";
    const senderSmall = document.createElement("small");
    senderSmall.className = "truncate";
    senderSmall.textContent = message.sender_address || "";
    sender.append(senderStrong, senderSmall);

    const subject = document.createElement("div");
    subject.className = "message-subject";
    const subjectStrong = document.createElement("strong");
    subjectStrong.className = "truncate";
    subjectStrong.textContent = message.subject || "(No subject)";
    const subjectSmall = document.createElement("small");
    subjectSmall.textContent = `${formatBytes(message.size_bytes)}${message.has_attachments ? " · Attachment" : ""}`;
    subject.append(subjectStrong, subjectSmall);

    const time = document.createElement("time");
    time.textContent = formatDate(message.received_at, "Unknown date");
    link.append(status, sender, subject, time);
    return link;
  }

  function addToInbox(message) {
    const inbox = document.querySelector(`[data-live-inbox="${message.mailbox_uuid}"]`);
    if (!inbox || inbox.dataset.liveInboxEnabled !== "true") return;
    if (inbox.querySelector(`[data-message-uuid="${message.uuid}"]`)) return;
    inbox.querySelector("[data-empty]")?.remove();
    inbox.prepend(buildMessageRow(message));
    while (inbox.querySelectorAll(".message-row").length > 30) {
      inbox.querySelector(".message-row:last-child")?.remove();
    }
  }

  function addToRecent(message) {
    const list = document.querySelector("[data-live-recent-messages]");
    if (!list || list.querySelector(`[data-message-uuid="${message.uuid}"]`)) return;
    list.querySelector("[data-empty]")?.remove();
    const link = document.createElement("a");
    link.className = "list-row";
    link.dataset.messageUuid = message.uuid;
    link.href = message.detail_url;
    const content = document.createElement("span");
    content.className = "truncate";
    const subject = document.createElement("strong");
    subject.textContent = message.subject || "(No subject)";
    const metadata = document.createElement("small");
    metadata.textContent = `${message.sender_address || "Unknown sender"} · ${message.mailbox}`;
    content.append(subject, metadata);
    const time = document.createElement("time");
    time.textContent = formatShortDate(message.received_at);
    link.append(content, time);
    list.prepend(link);
    while (list.querySelectorAll(".list-row").length > 8) list.querySelector(".list-row:last-child")?.remove();
  }

  async function notify(message) {
    if (!(await claimNotification(message.uuid))) return;
    const subject = message.subject || "(No subject)";
    toast(`${message.mailbox}: ${subject}`, { href: message.detail_url, tone: "success" });
    if ("Notification" in window && Notification.permission === "granted") {
      try {
        const notification = new Notification(`New email in ${message.mailbox}`, {
          body: `${message.sender_address || "Unknown sender"} — ${subject}`,
          tag: `vibmail-${message.uuid}`,
        });
        notification.onclick = () => {
          window.focus();
          window.location.href = message.detail_url;
        };
      } catch (_error) {
        // Browser notification failure must not interrupt in-app live updates.
      }
    }
  }

  async function poll() {
    const url = document.body.dataset.liveUrl;
    if (!url || polling) return;
    polling = true;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 12000);
    try {
      const params = new URLSearchParams({ cursor: String(cursor) });
      if (!bootstrapped) params.set("bootstrap", "1");
      const visibleMailboxUuids = new Set();
      document
        .querySelectorAll(
          "[data-live-mailbox-total], [data-live-mailbox-unread], " +
            "[data-live-mailbox-last], [data-live-mailbox-status]"
        )
        .forEach((node) => {
          const attribute = Array.from(node.attributes).find((item) =>
            item.name.startsWith("data-live-mailbox-")
          );
          if (attribute?.value) visibleMailboxUuids.add(attribute.value);
        });
      if (visibleMailboxUuids.size) {
        params.set("mailboxes", Array.from(visibleMailboxUuids).slice(0, 50).join(","));
      }
      const response = await fetch(`${url}?${params.toString()}`, {
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: controller.signal,
      });
      if (response.redirected && new URL(response.url).pathname.startsWith("/accounts/login/")) {
        window.location.assign(response.url);
        return;
      }
      if (!response.ok) throw new Error(`Live update failed: ${response.status}`);
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) throw new Error("Live update returned non-JSON data");
      const payload = await response.json();
      const firstPoll = !bootstrapped;
      cursor = Number(payload.cursor || 0);
      bootstrapped = true;
      updateSummary(payload.summary);
      (payload.mailboxes || []).forEach(updateMailbox);
      (payload.messages || []).forEach((message) => {
        addToInbox(message);
        addToRecent(message);
        if (!firstPoll) void notify(message);
      });
      backoff = 5000;
      schedule(payload.has_more ? 250 : document.hidden ? 15000 : 5000);
    } catch (_error) {
      backoff = Math.min(backoff * 2, 60000);
      schedule(backoff);
    } finally {
      window.clearTimeout(timeout);
      polling = false;
    }
  }

  function schedule(delay) {
    window.clearTimeout(timer);
    timer = window.setTimeout(poll, delay);
  }

  function readSidebarPreference() {
    try {
      return window.localStorage.getItem(SIDEBAR_STORAGE_KEY) === "true";
    } catch (_error) {
      return false;
    }
  }

  function saveSidebarPreference(collapsed) {
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
    } catch (_error) {
      // Storage restrictions must not make navigation unusable.
    }
  }

  function setupAppShell() {
    const body = document.body;
    const sidebar = document.querySelector("[data-app-sidebar]");
    const toggle = document.querySelector("[data-shell-toggle]");
    const closeButton = document.querySelector("[data-shell-close]");
    const collapseButton = document.querySelector("[data-sidebar-collapse]");
    if (!sidebar || !toggle) return;

    const desktop = window.matchMedia("(min-width: 1200px)");
    let returnFocus = null;

    function setSidebarInteractive(interactive) {
      const focusable = sidebar.querySelectorAll(
        "a, button, input, select, textarea, summary, [tabindex]"
      );
      if ("inert" in sidebar) sidebar.inert = !interactive;
      focusable.forEach((element) => {
        if (interactive) {
          if (element.dataset.shellTabindex === "none") {
            element.removeAttribute("tabindex");
          } else if (element.dataset.shellTabindex !== undefined) {
            element.setAttribute("tabindex", element.dataset.shellTabindex);
          }
          delete element.dataset.shellTabindex;
          return;
        }
        if (element.dataset.shellTabindex === undefined) {
          element.dataset.shellTabindex = element.hasAttribute("tabindex")
            ? element.getAttribute("tabindex")
            : "none";
        }
        element.setAttribute("tabindex", "-1");
      });
      if (interactive) {
        sidebar.removeAttribute("aria-hidden");
      } else {
        sidebar.setAttribute("aria-hidden", "true");
      }
    }

    function setDrawerOpen(open, { moveFocus = false } = {}) {
      const wasOpen = body.classList.contains("shell-open");
      const shouldOpen = Boolean(open && !desktop.matches);

      if (!shouldOpen && wasOpen && returnFocus) {
        const focusTarget = returnFocus;
        returnFocus = null;
        window.requestAnimationFrame(() => {
          if (focusTarget.isConnected) focusTarget.focus();
        });
      }

      body.classList.toggle("shell-open", shouldOpen);
      toggle.setAttribute("aria-expanded", String(shouldOpen));
      toggle.setAttribute("aria-label", shouldOpen ? "Close navigation" : "Open navigation");
      if (closeButton) closeButton.tabIndex = shouldOpen ? 0 : -1;
      setSidebarInteractive(desktop.matches || shouldOpen);

      if (shouldOpen && moveFocus) {
        returnFocus = document.activeElement;
        window.requestAnimationFrame(() => {
          sidebar.querySelector("a, button:not([hidden])")?.focus();
        });
      }
    }

    function updateCollapseState(collapsed) {
      const shouldCollapse = Boolean(collapsed && desktop.matches);
      body.classList.toggle("sidebar-collapsed", shouldCollapse);
      if (collapseButton) {
        collapseButton.setAttribute("aria-pressed", String(shouldCollapse));
        collapseButton.setAttribute(
          "aria-label",
          shouldCollapse ? "Expand navigation" : "Collapse navigation"
        );
      }
    }

    function synchronizeViewport() {
      setDrawerOpen(false);
      updateCollapseState(readSidebarPreference());
    }

    toggle.addEventListener("click", () => {
      setDrawerOpen(!body.classList.contains("shell-open"), { moveFocus: true });
    });
    closeButton?.addEventListener("click", () => setDrawerOpen(false));
    sidebar.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (!desktop.matches) setDrawerOpen(false);
      });
    });

    collapseButton?.addEventListener("click", () => {
      const collapsed = !body.classList.contains("sidebar-collapsed");
      saveSidebarPreference(collapsed);
      updateCollapseState(collapsed);
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && body.classList.contains("shell-open")) {
        event.preventDefault();
        setDrawerOpen(false);
      }
    });

    if (desktop.addEventListener) {
      desktop.addEventListener("change", synchronizeViewport);
    } else {
      desktop.addListener(synchronizeViewport);
    }
    synchronizeViewport();
  }

  function setupUserMenu() {
    const menu = document.querySelector("[data-user-menu]");
    if (!menu) return;
    const summary = menu.querySelector("summary");

    document.addEventListener("click", (event) => {
      if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    menu.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !menu.open) return;
      event.preventDefault();
      menu.open = false;
      summary?.focus();
    });
  }

  function setupNotifications() {
    const button = document.querySelector("[data-enable-notifications]");
    if (!button || !("Notification" in window)) return;
    if (Notification.permission === "default") button.hidden = false;
    button.addEventListener("click", async () => {
      try {
        const permission = await Notification.requestPermission();
        button.hidden = permission !== "default";
        toast(
          permission === "granted"
            ? "Browser notifications enabled."
            : "Browser notifications were not enabled; in-app alerts remain active.",
          { tone: permission === "granted" ? "success" : "info", timeout: 5000 }
        );
      } catch (_error) {
        toast("Browser notifications could not be enabled; in-app alerts remain active.", {
          tone: "info",
          timeout: 5000,
        });
      }
    });
  }

  function init() {
    loadNotified();
    if ("BroadcastChannel" in window) {
      channel = new BroadcastChannel("vibmail-live");
      channel.addEventListener("message", (event) => {
        if (event.data?.type === "notified" && event.data.uuid) notified.add(event.data.uuid);
      });
    }

    setupAppShell();
    setupUserMenu();

    document.querySelectorAll("[data-tabs]").forEach((tabList) => {
      const buttons = tabList.querySelectorAll("[data-tab-target]");
      buttons.forEach((button) => {
        button.addEventListener("click", () => {
          buttons.forEach((item) => item.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
          button.classList.add("active");
          document.querySelector(`#tab-${button.dataset.tabTarget}`)?.classList.add("active");
        });
      });
    });

    document.querySelectorAll(".status-form").forEach((form) => {
      form.addEventListener("submit", (event) => {
        const action = form.querySelector("input[name='action']")?.value || "change";
        const mailbox = form.dataset.mailbox || "this mailbox";
        if (!window.confirm(`Confirm ${action} for ${mailbox}?`)) event.preventDefault();
      });
    });

    document.addEventListener("click", (event) => {
      const target = event.target.closest("[data-copy-email]");
      if (target) copyText(target.dataset.copyEmail || "");
    });

    setupNotifications();
    if (document.body.dataset.liveUrl) schedule(250);
    document.addEventListener("visibilitychange", () => schedule(document.hidden ? 15000 : 500));
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", VibMail.init);
