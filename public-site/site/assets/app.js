(() => {
  "use strict";

  const settingsEndpoint = window.MAILSTACK_SETTINGS_ENDPOINT;
  if (settingsEndpoint) {
    fetch(settingsEndpoint, { credentials: "omit" })
      .then((response) => (response.ok ? response.json() : null))
      .then((siteSettings) => {
        if (!siteSettings) return;
        if (siteSettings.site_name && siteSettings.site_tagline) {
          document.title = `${siteSettings.site_name} — ${siteSettings.site_tagline}`;
        }
        document
          .querySelectorAll('meta[name="description"]')
          .forEach((node) => {
            if (siteSettings.site_tagline)
              node.content = siteSettings.site_tagline;
          });
        document
          .querySelectorAll(".brand > span:last-child")
          .forEach((node) => {
            node.textContent = siteSettings.site_name;
          });
        document
          .querySelectorAll("[data-footer-description]")
          .forEach((node) => {
            if (siteSettings.footer_description)
              node.textContent = siteSettings.footer_description;
          });
        document.querySelectorAll("[data-footer-copyright]").forEach((node) => {
          if (siteSettings.copyright_text)
            node.textContent = siteSettings.copyright_text;
        });
        document.querySelectorAll("[data-support-email]").forEach((node) => {
          if (siteSettings.support_email) {
            node.textContent = siteSettings.support_email;
            node.href = `mailto:${siteSettings.support_email}`;
          }
        });
        document.querySelectorAll("[data-contact-phone]").forEach((node) => {
          node.textContent = siteSettings.contact_phone;
        });
        document.querySelectorAll("[data-office-address]").forEach((node) => {
          node.textContent = siteSettings.office_address;
        });
        document.querySelectorAll("[data-source-code-url]").forEach((node) => {
          if (siteSettings.source_code_url)
            node.href = siteSettings.source_code_url;
        });
        document.querySelectorAll("[data-privacy-url]").forEach((node) => {
          if (siteSettings.privacy_url) node.href = siteSettings.privacy_url;
        });
        if (siteSettings.logo_url)
          document.querySelectorAll(".brand-mark").forEach((node) => {
            const image = document.createElement("img");
            image.src = siteSettings.logo_url;
            image.alt = "";
            image.className = "brand-mark-image";
            node.replaceChildren(image);
          });
        if (siteSettings.favicon_url)
          document.querySelectorAll('link[rel="icon"]').forEach((node) => {
            node.href = siteSettings.favicon_url;
          });
      })
      .catch(() => {});
  }

  document.documentElement.classList.remove("no-js");

  const header = document.querySelector("[data-header]");
  const navToggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-nav]");

  const closeNav = () => {
    if (!navToggle || !nav) return;
    navToggle.setAttribute("aria-expanded", "false");
    nav.classList.remove("is-open");
    document.body.classList.remove("nav-open");
  };

  if (navToggle && nav) {
    navToggle.addEventListener("click", () => {
      const open = navToggle.getAttribute("aria-expanded") === "true";
      navToggle.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
      document.body.classList.toggle("nav-open", !open);
    });

    nav
      .querySelectorAll("a")
      .forEach((link) => link.addEventListener("click", closeNav));
    window.addEventListener("resize", () => {
      if (window.innerWidth > 860) closeNav();
    });
  }

  const updateHeader = () => {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 18);
  };
  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  document.querySelectorAll("[data-year]").forEach((node) => {
    node.textContent = String(new Date().getFullYear());
  });

  const revealItems = document.querySelectorAll("[data-reveal]");
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  if (reducedMotion || !("IntersectionObserver" in window)) {
    revealItems.forEach((item) => item.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver(
      (entries, currentObserver) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          currentObserver.unobserve(entry.target);
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px" },
    );

    revealItems.forEach((item) => observer.observe(item));
  }

  const contactForm = document.querySelector("[data-contact-form]");
  if (!contactForm) return;

  const statusNode = document.querySelector("[data-form-status]");
  const submitButton = contactForm.querySelector('button[type="submit"]');
  const submitLabel = contactForm.querySelector("[data-submit-label]");
  const messageField = contactForm.querySelector("#message");
  const messageCount = document.querySelector("[data-message-count]");
  const startedField = contactForm.querySelector('[name="form_started_at"]');

  let csrfToken = "";
  let csrfPromise = null;

  startedField.value = String(Date.now());

  const setStatus = (type, message) => {
    statusNode.hidden = false;
    statusNode.className = `form-status ${type}`;
    statusNode.textContent = message;
  };

  const clearStatus = () => {
    statusNode.hidden = true;
    statusNode.className = "form-status";
    statusNode.textContent = "";
  };

  const setLoading = (loading) => {
    submitButton.disabled = loading;
    submitButton.classList.toggle("is-loading", loading);
    submitLabel.textContent = loading ? "Sending inquiry…" : "Send inquiry";
  };

  const clearErrors = () => {
    contactForm.querySelectorAll(".field-error").forEach((node) => {
      node.textContent = "";
    });
    contactForm.querySelectorAll("[aria-invalid='true']").forEach((node) => {
      node.removeAttribute("aria-invalid");
    });
  };

  const showErrors = (errors) => {
    Object.entries(errors || {}).forEach(([field, message]) => {
      const input = contactForm.elements.namedItem(field);
      const error = contactForm.querySelector(`[data-error-for="${field}"]`);
      if (input) input.setAttribute("aria-invalid", "true");
      if (error) error.textContent = String(message);
    });
  };

  const loadCsrf = async () => {
    if (csrfToken) return csrfToken;
    if (!csrfPromise) {
      csrfPromise = fetch("/api/contact/csrf/", {
        method: "GET",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        cache: "no-store",
      })
        .then(async (response) => {
          if (!response.ok)
            throw new Error("Unable to initialize secure form.");
          const data = await response.json();
          if (!data.token) throw new Error("Invalid form security response.");
          csrfToken = data.token;
          return csrfToken;
        })
        .finally(() => {
          csrfPromise = null;
        });
    }
    return csrfPromise;
  };

  loadCsrf().catch(() => {
    setStatus(
      "error",
      "The secure contact form is temporarily unavailable. Please reload the page and try again.",
    );
  });

  if (messageField && messageCount) {
    const updateCount = () => {
      messageCount.textContent = String(messageField.value.length);
    };
    messageField.addEventListener("input", updateCount);
    updateCount();
  }

  const queryService = new URLSearchParams(window.location.search).get(
    "service",
  );
  if (
    queryService &&
    ["personal", "team", "business", "other"].includes(queryService)
  ) {
    contactForm.elements.service_type.value = queryService;
  }

  contactForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    clearStatus();

    if (!contactForm.checkValidity()) {
      contactForm.reportValidity();
      setStatus(
        "error",
        "Please complete all required fields before submitting.",
      );
      return;
    }

    setLoading(true);

    try {
      const token = await loadCsrf();
      const formData = new FormData(contactForm);
      const payload = Object.fromEntries(formData.entries());
      payload.consent = formData.get("consent") === "on";

      const response = await fetch("/api/contact/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-VibMail-CSRF": token,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (data.errors) showErrors(data.errors);
        throw new Error(data.message || "Your inquiry could not be submitted.");
      }

      setStatus(
        "success",
        "Thank you. Your inquiry has been sent to the MailStack administration team.",
      );
      contactForm.reset();
      startedField.value = String(Date.now());
      if (messageCount) messageCount.textContent = "0";
      statusNode.scrollIntoView({
        behavior: reducedMotion ? "auto" : "smooth",
        block: "center",
      });
    } catch (error) {
      setStatus(
        "error",
        error.message || "Something went wrong. Please try again.",
      );
    } finally {
      csrfToken = "";
      loadCsrf().catch(() => {});
      setLoading(false);
    }
  });
})();
