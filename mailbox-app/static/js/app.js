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
      const values = JSON.parse(
        window.localStorage.getItem(STORAGE_KEY) || "[]",
      );
      notified = new Set(
        Array.isArray(values) ? values.slice(-MAX_NOTIFIED) : [],
      );
    } catch (_error) {
      notified = new Set();
    }
  }

  function saveNotified() {
    try {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(Array.from(notified).slice(-MAX_NOTIFIED)),
      );
    } catch (_error) {
      // Private browsing or storage restrictions must not break live updates.
    }
  }

  function markNotified(uuid) {
    if (notified.has(uuid)) return false;
    notified.add(uuid);
    if (notified.size > MAX_NOTIFIED)
      notified.delete(notified.values().next().value);
    saveNotified();
    if (channel) channel.postMessage({ type: "notified", uuid });
    return true;
  }

  async function claimNotification(uuid) {
    if (navigator.locks?.request) {
      let claimed = false;
      await navigator.locks.request(
        `vibmail-notification-${uuid}`,
        async () => {
          loadNotified();
          claimed = markNotified(uuid);
        },
      );
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

  function buildCloudflareZone(records, domain, header) {
    const quoteTxt = (value) =>
      `"${String(value).replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"`;
    const lines = [
      `;; ${header} ${domain}`,
      `$ORIGIN ${domain}.`,
      "$TTL 1",
      "",
    ];
    records
      .filter((record) => record.copyable !== false)
      .forEach((record) => {
        const type = String(record.type).split(" ")[0];
        let value = String(record.value);
        if (type === "MX") {
          value = `${record.priority}\t${value.replace(/\.$/, "")}.`;
        } else if (type === "TXT") {
          value = quoteTxt(value);
        }
        lines.push(`${record.cf_host || "@"}\tIN\t${type}\t${value}`);
      });
    return `${lines.join("\n")}\n`;
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
      document
        .querySelectorAll(`[data-live-summary="${key}"]`)
        .forEach((node) => {
          node.textContent =
            key === "last_received"
              ? formatDate(value, "No email yet")
              : String(value);
        });
    });
  }

  function updateMailbox(mailbox) {
    const uuid = mailbox.uuid;
    document
      .querySelectorAll(`[data-live-mailbox-total="${uuid}"]`)
      .forEach((node) => {
        node.textContent = String(mailbox.total_messages);
      });
    document
      .querySelectorAll(`[data-live-mailbox-unread="${uuid}"]`)
      .forEach((node) => {
        node.textContent = String(mailbox.unread_messages);
      });
    document
      .querySelectorAll(`[data-live-mailbox-last="${uuid}"]`)
      .forEach((node) => {
        node.textContent = formatDate(mailbox.last_received_at);
      });
    document
      .querySelectorAll(`[data-live-mailbox-status="${uuid}"]`)
      .forEach((node) => {
        node.textContent =
          mailbox.status.charAt(0).toUpperCase() + mailbox.status.slice(1);
        node.className = `badge badge-${mailbox.status}`;
      });
  }

  function buildMessageRow(message) {
    const link = document.createElement("a");
    link.className = `message-row${message.is_read ? "" : " unread"}`;
    link.href = message.detail_url;
    link.dataset.messageUuid = message.uuid;

    const status = document.createElement("span");
    status.className = "message-status";
    status.setAttribute("aria-label", message.is_read ? "Read" : "Unread");
    status.title = message.is_read ? "Read" : "Unread";

    const sender = document.createElement("span");
    sender.className = "message-sender";
    const senderStrong = document.createElement("strong");
    senderStrong.className = "truncate";
    senderStrong.textContent =
      message.sender_name || message.sender_address || "Unknown sender";
    const senderSmall = document.createElement("small");
    senderSmall.className = "truncate";
    senderSmall.textContent = message.sender_address || "";
    sender.append(senderStrong, senderSmall);

    const content = document.createElement("span");
    content.className = "message-content";
    const subjectLine = document.createElement("span");
    subjectLine.className = "message-subject-line";
    const subjectStrong = document.createElement("strong");
    subjectStrong.className = "message-subject-text";
    subjectStrong.textContent = message.subject || "(No subject)";
    subjectLine.append(subjectStrong);
    if (message.preview) {
      const preview = document.createElement("span");
      preview.className = "message-preview";
      preview.textContent = ` — ${message.preview}`;
      subjectLine.append(preview);
    }
    const secondary = document.createElement("small");
    secondary.className = "message-secondary";
    if (message.has_attachments) {
      const attachment = document.createElement("span");
      attachment.className = "message-attachment";
      attachment.textContent = "Attachment";
      secondary.append(attachment, document.createTextNode(" · "));
    }
    secondary.append(document.createTextNode(formatBytes(message.size_bytes)));
    content.append(subjectLine, secondary);

    const time = document.createElement("time");
    time.className = "message-time";
    time.textContent = formatShortDate(message.received_at);
    if (message.received_at) time.dateTime = message.received_at;
    link.append(status, sender, content, time);
    return link;
  }

  function addToInbox(message) {
    const inbox = document.querySelector(
      `[data-live-inbox="${message.mailbox_uuid}"]`,
    );
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
    if (!list || list.querySelector(`[data-message-uuid="${message.uuid}"]`))
      return;
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
    while (list.querySelectorAll(".list-row").length > 8)
      list.querySelector(".list-row:last-child")?.remove();
  }

  async function notify(message) {
    if (!(await claimNotification(message.uuid))) return;
    const subject = message.subject || "(No subject)";
    toast(`${message.mailbox}: ${subject}`, {
      href: message.detail_url,
      tone: "success",
    });
    if ("Notification" in window && Notification.permission === "granted") {
      try {
        const notification = new Notification(
          `New email in ${message.mailbox}`,
          {
            body: `${message.sender_address || "Unknown sender"} — ${subject}`,
            tag: `vibmail-${message.uuid}`,
          },
        );
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
            "[data-live-mailbox-last], [data-live-mailbox-status]",
        )
        .forEach((node) => {
          const attribute = Array.from(node.attributes).find((item) =>
            item.name.startsWith("data-live-mailbox-"),
          );
          if (attribute?.value) visibleMailboxUuids.add(attribute.value);
        });
      if (visibleMailboxUuids.size) {
        params.set(
          "mailboxes",
          Array.from(visibleMailboxUuids).slice(0, 50).join(","),
        );
      }
      const response = await fetch(`${url}?${params.toString()}`, {
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-MailStack-Live-Request": "1",
        },
        cache: "no-store",
        signal: controller.signal,
      });
      if (
        response.redirected &&
        new URL(response.url).pathname.startsWith("/accounts/login/")
      ) {
        window.location.assign(response.url);
        return;
      }
      if (!response.ok)
        throw new Error(`Live update failed: ${response.status}`);
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json"))
        throw new Error("Live update returned non-JSON data");
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
        "a, button, input, select, textarea, summary, [tabindex]",
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
      toggle.setAttribute(
        "aria-label",
        shouldOpen ? "Close navigation" : "Open navigation",
      );
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
          shouldCollapse ? "Expand navigation" : "Collapse navigation",
        );
      }
    }

    function synchronizeViewport() {
      setDrawerOpen(false);
      updateCollapseState(readSidebarPreference());
    }

    toggle.addEventListener("click", () => {
      setDrawerOpen(!body.classList.contains("shell-open"), {
        moveFocus: true,
      });
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

    const brandLockup = sidebar.querySelector(".brand-lockup");
    brandLockup?.addEventListener("click", (event) => {
      if (body.classList.contains("sidebar-collapsed") && desktop.matches) {
        event.preventDefault();
        saveSidebarPreference(false);
        updateCollapseState(false);
      }
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

  function setupMailboxCreateModal() {
    const modal = document.querySelector("[data-mailbox-create-modal]");
    if (!modal) return;
    const localPart = modal.querySelector("[name='local_part']");
    const suggestions = modal.querySelector("[data-mailbox-suggestions]");
    const selectedCounter = modal.querySelector(
      "[data-mailbox-selected-counter]",
    );
    const firstNames = [
      "james",
      "olivia",
      "liam",
      "emma",
      "noah",
      "charlotte",
      "ethan",
      "amelia",
      "lucas",
      "sophia",
      "mason",
      "isabella",
      "logan",
      "harper",
      "elijah",
      "evelyn",
      "aiden",
      "abigail",
      "jackson",
      "emily",
      "henry",
      "elizabeth",
      "alex",
      "chloe",
    ];
    const lastNames = [
      "smith",
      "johnson",
      "williams",
      "brown",
      "jones",
      "miller",
      "davis",
      "garcia",
      "rodriguez",
      "wilson",
      "martinez",
      "anderson",
      "taylor",
      "thomas",
      "moore",
      "jackson",
      "martin",
      "lee",
      "perez",
      "thompson",
      "white",
      "harris",
      "clark",
    ];
    const randomItem = (items) =>
      items[Math.floor(Math.random() * items.length)];
    const randomName = () =>
      `${randomItem(firstNames)}.${randomItem(lastNames)}`;
    const getFinalAddress = () => {
      const value = localPart?.value.trim() || randomName();
      if (localPart && !localPart.value.trim()) localPart.value = value;
      const domain =
        modal.querySelector("[name='domain']")?.value ||
        modal.dataset.defaultDomain ||
        "";
      return `${value}@${domain}`;
    };
    const renderSuggestions = () => {
      if (!suggestions) return;
      suggestions.replaceChildren();
      const names = new Set();
      while (names.size < 3) names.add(randomName());
      names.forEach((name) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "mailbox-suggestion";
        button.textContent = name;
        button.addEventListener("click", () => {
          localPart.value = name;
          localPart.focus();
        });
        suggestions.append(button);
      });
    };
    const updateSelectedCounter = () => {
      if (!selectedCounter) return;
      const count = modal.querySelectorAll(
        "[name='assigned_users']:checked",
      ).length;
      selectedCounter.textContent = `${count} selected`;
    };
    let returnFocus = null;
    const open = (trigger) => {
      returnFocus = trigger || document.activeElement;
      if (typeof modal.showModal === "function") modal.showModal();
      else modal.setAttribute("open", "");
      modal.querySelector("input, select, button")?.focus();
      renderSuggestions();
    };
    const close = () => {
      if (typeof modal.close === "function") modal.close();
      else modal.removeAttribute("open");
      returnFocus?.focus();
    };
    document.addEventListener("click", (event) => {
      const trigger = event.target.closest("[data-open-mailbox-modal]");
      if (trigger) {
        event.preventDefault();
        open(trigger);
      }
      if (event.target.closest("[data-close-mailbox-modal]")) close();
    });
    modal.addEventListener("click", (event) => {
      if (event.target === modal) close();
    });
    modal.addEventListener("cancel", (event) => {
      event.preventDefault();
      close();
    });
    modal
      .querySelector("[data-mailbox-random]")
      ?.addEventListener("click", () => {
        localPart.value = `${randomName()}${Math.floor(10 + Math.random() * 90)}`;
        localPart.focus();
      });
    modal
      .querySelector("[data-mailbox-refresh]")
      ?.addEventListener("click", renderSuggestions);
    modal
      .querySelectorAll("[name='assigned_users']")
      .forEach((checkbox) =>
        checkbox.addEventListener("change", updateSelectedCounter),
      );
    localPart?.addEventListener("input", () => {
      localPart.value = localPart.value
        .toLowerCase()
        .replace(/[^a-z0-9._-]/g, "");
    });
    modal.querySelector("form")?.addEventListener("submit", async (event) => {
      if (!event.submitter?.matches("[data-mailbox-create-copy]")) return;
      event.preventDefault();
      await copyText(getFinalAddress());
      HTMLFormElement.prototype.submit.call(event.currentTarget);
    });
    updateSelectedCounter();
    if (modal.hasAttribute("data-open-on-load")) open();
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
          {
            tone: permission === "granted" ? "success" : "info",
            timeout: 5000,
          },
        );
      } catch (_error) {
        toast(
          "Browser notifications could not be enabled; in-app alerts remain active.",
          {
            tone: "info",
            timeout: 5000,
          },
        );
      }
    });
  }

  function setupUserForm() {
    const form = document.querySelector("[data-user-form]");
    if (!form) return;
    const username = form.querySelector("[name='username']");
    const password = form.querySelector("[name='password1']");
    const confirmation = form.querySelector("[name='password2']");
    const mailboxes = Array.from(
      form.querySelectorAll("[name='assigned_mailboxes']"),
    );
    const count = form.querySelector("[data-user-mailbox-count]");
    const firstNames = [
      "james",
      "ethan",
      "olivia",
      "chloe",
      "liam",
      "emma",
      "noah",
      "abigail",
    ];
    const lastNames = ["smith", "miller", "davis", "clark", "wilson", "jones"];
    const updateCount = () => {
      if (count)
        count.textContent = `${mailboxes.filter((item) => item.checked).length} selected`;
    };
    form.querySelector("[data-user-random]")?.addEventListener("click", () => {
      const first = firstNames[Math.floor(Math.random() * firstNames.length)];
      const last = lastNames[Math.floor(Math.random() * lastNames.length)];
      if (username)
        username.value = `${first}.${last}${Math.floor(10 + Math.random() * 90)}`;
      username?.focus();
    });
    form
      .querySelector("[data-user-generate-password]")
      ?.addEventListener("click", () => {
        const chars =
          "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789!@#$%^&*";
        const value = Array.from(
          { length: 14 },
          () => chars[Math.floor(Math.random() * chars.length)],
        ).join("");
        if (password) password.value = value;
        if (confirmation) confirmation.value = value;
        if (password) password.type = "text";
        if (confirmation) confirmation.type = "text";
      });
    form
      .querySelector("[data-user-toggle-password]")
      ?.addEventListener("click", (event) => {
        const visible = password?.type === "text";
        if (password) password.type = visible ? "password" : "text";
        if (confirmation) confirmation.type = visible ? "password" : "text";
        event.currentTarget.setAttribute(
          "aria-label",
          visible ? "Show password" : "Hide password",
        );
      });
    mailboxes.forEach((item) => item.addEventListener("change", updateCount));
    form
      .querySelector("[data-user-mailbox-filter]")
      ?.addEventListener("input", (event) => {
        const query = event.currentTarget.value.toLowerCase();
        form.querySelectorAll("[data-mailbox-item]").forEach((item) => {
          item.hidden = !item.textContent.toLowerCase().includes(query);
        });
      });
    form.addEventListener("submit", (event) => {
      if (!event.submitter?.matches("[data-user-create-copy]")) return;
      const credentials = `MailStack Credentials:\nUsername: ${username?.value.trim() || ""}\nPassword: ${password?.value || ""}`;
      const button = event.submitter;
      const label = button.querySelector("[data-user-copy-label]");
      event.preventDefault();
      copyText(credentials).finally(() => {
        if (label) label.textContent = "Copied!";
        button.classList.add("user-copy-complete");
        window.setTimeout(() => {
          HTMLFormElement.prototype.submit.call(form);
        }, 150);
      });
    });
    updateCount();
  }

  function setupDomainForm() {
    const page = document.querySelector("[data-domain-form]");
    if (!page) return;
    const input = page.querySelector("#id_name");
    const getDns = page.querySelector("[data-get-dns]");
    const error = page.querySelector("[data-domain-error]");
    const body = page.querySelector("[data-dns-body]");
    const exportButton = page.querySelector("[data-export-dns]");
    const confirmation = page.querySelector("[data-dns-confirm]");
    const submit = page.querySelector("[data-domain-submit]");
    const getDnsLabel = getDns?.querySelector("span");
    const validDomainPattern =
      /^(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
    let records = [];

    function showError(message) {
      error.textContent = message;
      error.hidden = false;
      input.classList.add("is-invalid");
      input.focus();
    }

    function renderRows() {
      body.replaceChildren();
      records.forEach((record) => {
        const row = document.createElement("tr");
        const values = [
          record.type,
          record.host,
          record.value,
          record.priority || "-",
        ];
        values.forEach((value, index) => {
          const cell = document.createElement("td");
          cell.textContent = value;
          if (index === 1 || index === 2) cell.title = value;
          row.appendChild(cell);
        });
        const action = document.createElement("td");
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "domain-copy";
        copy.textContent = record.copyable ? "Copy" : "Unavailable";
        copy.disabled = !record.copyable;
        copy.addEventListener("click", async () => {
          await copyText(record.value);
          copy.textContent = "Copied!";
          window.setTimeout(() => {
            copy.textContent = "Copy";
          }, 1200);
        });
        action.appendChild(copy);
        row.appendChild(action);
        body.appendChild(row);
      });
    }

    getDns?.addEventListener("click", async () => {
      const domain = input.value.trim();
      if (!validDomainPattern.test(domain))
        return showError(
          "Enter a valid domain name before getting DNS records.",
        );
      error.hidden = true;
      input.classList.remove("is-invalid");
      getDns.disabled = true;
      if (getDnsLabel) getDnsLabel.textContent = "Resolving...";
      try {
        const response = await fetch(
          `${page.dataset.previewUrl}?domain=${encodeURIComponent(domain)}`,
          {
            headers: { Accept: "application/json" },
          },
        );
        const result = await response.json();
        if (!response.ok)
          throw new Error(
            result.error || "DNS records could not be generated.",
          );
        records = result.records;
        renderRows();
        exportButton.disabled = false;
        if (confirmation) confirmation.disabled = false;
      } catch (requestError) {
        showError(requestError.message);
      } finally {
        getDns.disabled = false;
        if (getDnsLabel) getDnsLabel.textContent = "Get DNS";
      }
    });

    confirmation?.addEventListener("change", () => {
      submit.disabled = !confirmation.checked;
    });
    exportButton?.addEventListener("click", () => {
      const domain = input.value.trim().toLowerCase();
      const url = URL.createObjectURL(
        new Blob(
          [
            buildCloudflareZone(
              records,
              domain,
              "BIND Zone File for Cloudflare DNS Import",
            ),
          ],
          {
            type: "text/plain;charset=utf-8",
          },
        ),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = `${domain}-cloudflare-dns.txt`;
      link.click();
      URL.revokeObjectURL(url);
    });
  }

  function setupDomainsPage() {
    const page = document.querySelector("[data-domains-page]");
    if (!page) return;
    const rows = [...page.querySelectorAll("[data-domain-row]")];
    const search = page.querySelector("[data-domain-search]");
    const count = page.querySelector("[data-domain-count]");
    const toggleTemplate = page.dataset.dnsToggleTemplate;
    const csrfToken = page.querySelector(
      "[data-domain-csrf-token] input[name=csrfmiddlewaretoken]",
    )?.value;
    rows.forEach((row) => {
      const actions = row.querySelector(".domain-row-actions");
      const uuid = row.querySelector("[data-domain-uuid]")?.dataset.domainUuid;
      if (
        !actions ||
        !uuid ||
        !toggleTemplate ||
        actions.querySelector("[data-domain-toggle]")
      )
        return;
      const form = document.createElement("form");
      form.method = "post";
      form.action = toggleTemplate.replace(
        "00000000-0000-0000-0000-000000000000",
        uuid,
      );
      const token = document.createElement("input");
      token.type = "hidden";
      token.name = "csrfmiddlewaretoken";
      token.value = csrfToken || "";
      const button = document.createElement("button");
      button.type = "submit";
      button.className = "domain-icon-action";
      button.dataset.domainToggle = "true";
      const active = row.querySelector(".domain-status-active");
      button.title = `${active ? "Disable" : "Enable"} domain`;
      button.setAttribute(
        "aria-label",
        `${active ? "Disable" : "Enable"} ${row.querySelector("[data-dns-open]")?.dataset.domainName || "domain"}`,
      );
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        button.disabled = true;
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            Accept: "text/html",
            "X-CSRFToken": csrfToken || "",
          },
          credentials: "same-origin",
        });
        if (response.ok) window.location.reload();
        else button.disabled = false;
      });
      const iconHref = row
        .querySelector("[data-dns-open] use")
        ?.getAttribute("href")
        ?.replace("#icon-globe", "#icon-refresh-cw");
      const svgNamespace = row.querySelector("svg")?.namespaceURI;
      const icon = document.createElementNS(svgNamespace, "svg");
      icon.classList.add("ui-icon");
      icon.setAttribute("aria-hidden", "true");
      const iconUse = document.createElementNS(svgNamespace, "use");
      if (iconHref) iconUse.setAttribute("href", iconHref);
      icon.append(iconUse);
      button.append(icon);
      form.append(token, button);
      actions.prepend(form);
      if (
        row.querySelector(".domain-default") &&
        !actions.querySelector("[data-domain-default]")
      ) {
        const defaultButton = document.createElement("button");
        defaultButton.type = "button";
        defaultButton.className = "domain-icon-action domain-default-action";
        defaultButton.dataset.domainDefault = "true";
        defaultButton.disabled = true;
        defaultButton.title = "Current default domain";
        defaultButton.setAttribute(
          "aria-label",
          `${row.querySelector("[data-dns-open]")?.dataset.domainName || "Domain"} is the current default domain`,
        );
        const svgNamespace = row.querySelector("svg")?.namespaceURI;
        const icon = document.createElementNS(svgNamespace, "svg");
        icon.classList.add("ui-icon");
        icon.setAttribute("aria-hidden", "true");
        const iconUse = document.createElementNS(svgNamespace, "use");
        const iconHref = row
          .querySelector("[data-dns-open] use")
          ?.getAttribute("href")
          ?.replace("#icon-globe", "#icon-star");
        if (iconHref) iconUse.setAttribute("href", iconHref);
        icon.append(iconUse);
        defaultButton.append(icon);
        actions.insertBefore(defaultButton, actions.firstElementChild);
      }
    });
    const modal = document.querySelector("[data-dns-modal]");
    if (!modal) return;
    const title = modal.querySelector("[data-dns-title]");
    const body = modal.querySelector("[data-dns-modal-rows]");
    const statusTemplate = page.dataset.dnsStatusTemplate;
    const checkTemplate = page.dataset.dnsCheckTemplate;
    const csrfToken = page.querySelector(
      "[data-domain-csrf-token] input[name=csrfmiddlewaretoken]",
    )?.value;
    const progress = modal.querySelector("[data-dns-progress]");
    const tag = modal.querySelector("[data-dns-tag]");
    const check = modal.querySelector("[data-dns-check]");
    const exportButton = modal.querySelector("[data-dns-export]");
    let records = [];
    let domain = "";

    const setTag = (text, tone) => {
      tag.textContent = text;
      tag.className = `domain-dns-tag domain-dns-tag-${tone}`;
    };
    const render = (results = []) => {
      body.replaceChildren();
      results.forEach((record) => {
        const row = document.createElement("tr");
        [record.type, record.host, record.value].forEach((value) => {
          const cell = document.createElement("td");
          cell.textContent = value;
          cell.title = value;
          row.append(cell);
        });
        const status = document.createElement("td");
        const statusLabels = {
          checking: "Testing",
          missing: "Missing",
          pending: "Pending",
          verified: "OK",
        };
        status.textContent = statusLabels[record.status] || "Pending";
        status.className = `domain-dns-${record.status || "pending"}`;
        row.append(status);
        const action = document.createElement("td");
        const copy = document.createElement("button");
        copy.type = "button";
        copy.className = "domain-copy";
        copy.textContent = record.copyable === false ? "Unavailable" : "Copy";
        copy.disabled = record.copyable === false;
        if (record.copyable !== false) {
          copy.addEventListener("click", () => copyText(record.value));
        }
        action.append(copy);
        row.append(action);
        body.append(row);
      });
    };
    const loadRecords = async (uuid, name, verificationStatus) => {
      domain = name;
      title.textContent = name;
      setTag("Loading", "loading");
      progress.style.width = "20%";
      const response = await fetch(
        `${page.dataset.dnsPreviewUrl}?domain=${encodeURIComponent(name)}`,
        { headers: { Accept: "application/json" } },
      );
      if (!response.ok) throw new Error("DNS records could not be loaded.");
      const result = await response.json();
      records = result.records.map((record) => ({
        ...record,
        status: "pending",
      }));
      render(records);
      exportButton.disabled = false;
      setTag(
        verificationStatus === "verified"
          ? "Last check passed"
          : "Ready to check",
        verificationStatus === "verified" ? "success" : "warning",
      );
      progress.style.width = "0%";
      modal.dataset.domainUuid = uuid;
    };
    page.querySelectorAll("[data-dns-open]").forEach((button) =>
      button.addEventListener("click", async () => {
        modal.showModal();
        try {
          await loadRecords(
            button.dataset.domainUuid,
            button.dataset.domainName,
            button.dataset.domainStatus,
          );
        } catch (error) {
          setTag(error.message, "error");
        }
      }),
    );
    modal
      .querySelectorAll("[data-dns-close]")
      .forEach((button) =>
        button.addEventListener("click", () => modal.close()),
      );
    check.addEventListener("click", async () => {
      check.disabled = true;
      setTag("Checking...", "loading");
      progress.style.width = "35%";
      try {
        const url = statusTemplate.replace(
          "00000000-0000-0000-0000-000000000000",
          modal.dataset.domainUuid,
        );
        const response = await fetch(url, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) throw new Error("DNS check failed.");
        const result = await response.json();
        const verified = Boolean(result.verified);
        if (verified && checkTemplate && csrfToken) {
          const persistUrl = checkTemplate.replace(
            "00000000-0000-0000-0000-000000000000",
            modal.dataset.domainUuid,
          );
          const persistResponse = await fetch(persistUrl, {
            method: "POST",
            headers: {
              Accept: "text/html",
              "X-CSRFToken": csrfToken,
            },
            credentials: "same-origin",
          });
          if (!persistResponse.ok)
            throw new Error("DNS verification could not be saved.");
        }
        const checkedRecords =
          result.records ||
          records.map((record) => ({
            ...record,
            status: verified ? "verified" : "missing",
          }));
        let step = 0;
        const renderNextRecord = () => {
          records = checkedRecords.map((record, index) => ({
            ...record,
            status:
              index < step
                ? record.status
                : index === step
                  ? "checking"
                  : "pending",
          }));
          render(records);
          progress.style.width = `${Math.round((step / checkedRecords.length) * 100)}%`;
          if (step < checkedRecords.length) {
            step += 1;
            window.setTimeout(renderNextRecord, 350);
            return;
          }
          progress.style.width = verified ? "100%" : "60%";
          setTag(
            verified ? "All verified" : "Records missing",
            verified ? "success" : "warning",
          );
          check.disabled = false;
          if (verified) window.setTimeout(() => window.location.reload(), 500);
        };
        renderNextRecord();
      } catch (error) {
        setTag(error.message, "error");
        check.disabled = false;
      }
    });
    exportButton.addEventListener("click", () => {
      const url = URL.createObjectURL(
        new Blob(
          [buildCloudflareZone(records, domain, "Cloudflare Zone File for")],
          {
            type: "text/plain;charset=utf-8",
          },
        ),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = `${domain}-cloudflare-dns.txt`;
      link.click();
      URL.revokeObjectURL(url);
    });
    search?.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
      let visible = 0;
      rows.forEach((row) => {
        const shown = row.dataset.searchText.toLowerCase().includes(query);
        row.hidden = !shown;
        if (shown) visible += 1;
      });
      count.textContent = `${visible} domain${visible === 1 ? "" : "s"}`;
    });
  }

  function init() {
    loadNotified();
    if ("BroadcastChannel" in window) {
      channel = new BroadcastChannel("vibmail-live");
      channel.addEventListener("message", (event) => {
        if (event.data?.type === "notified" && event.data.uuid)
          notified.add(event.data.uuid);
      });
    }

    setupAppShell();
    setupUserMenu();
    setupMailboxCreateModal();
    setupUserForm();
    setupDomainForm();
    setupDomainsPage();

    document.querySelectorAll(".status-form").forEach((form) => {
      form.addEventListener("submit", (event) => {
        const action =
          form.querySelector("input[name='action']")?.value || "change";
        const mailbox = form.dataset.mailbox || "this mailbox";
        if (!window.confirm(`Confirm ${action} for ${mailbox}?`))
          event.preventDefault();
      });
    });

    document.addEventListener("click", (event) => {
      const target = event.target.closest("[data-copy-email]");
      if (target) copyText(target.dataset.copyEmail || "");
      const dnsTarget = event.target.closest("[data-copy-dns]");
      if (dnsTarget) copyText(dnsTarget.dataset.copyDns || "");
    });

    setupNotifications();
    if (document.body.dataset.liveUrl) schedule(250);
    document.addEventListener("visibilitychange", () =>
      schedule(document.hidden ? 15000 : 500),
    );
  }

  return { init };
})();

document.addEventListener("DOMContentLoaded", VibMail.init);
