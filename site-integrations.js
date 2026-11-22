(() => {
  "use strict";
  const config = window.portfolioIntegrations || {};
  const consentKey = "portfolio-analytics-consent";
  const readConsent = () => {
    try { return localStorage.getItem(consentKey) === "allow"; }
    catch { return false; }
  };

  // The Google tag is never loaded before a visitor chooses to allow analytics.
  const id = config.analyticsId;
  if (/^G-[A-Z0-9]+$/.test(id || "") && location.protocol === "https:") {
    let started = false;
    const disableKey = "ga-disable-" + id;
    const section = document.createElement("section");
    section.className = "shell privacy-controls";
    section.setAttribute("aria-label", "Analytics preferences");
    const button = document.createElement("button");
    button.type = "button";
    const status = document.createElement("span");
    status.setAttribute("role", "status");
    section.append(button, status);
    document.querySelector("footer")?.before(section);

    function startAnalytics() {
      window[disableKey] = false;
      if (started) return;
      started = true;
      const dataLayer = window.dataLayer = window.dataLayer || [];
      function gtag() { dataLayer.push(arguments); }
      const path = location.pathname === "/index.html" ? "/" : location.pathname;
      const page = location.origin + path;
      gtag("consent", "default", {
        analytics_storage: "granted",
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied",
      });
      gtag("js", new Date());
      gtag("config", id, {
        allow_google_signals: false,
        allow_ad_personalization_signals: false,
        send_page_view: false,
        page_location: page,
        page_referrer: "",
      });
      gtag("event", "page_view", {page_location: page, page_referrer: "", send_to: id});
      const script = document.createElement("script");
      script.async = true;
      script.referrerPolicy = "no-referrer";
      script.src = "https://www.googletagmanager.com/gtag/js?id=" + id;
      document.head.append(script);
    }

    function syncPreferences(allowed) {
      button.textContent = allowed ? "Turn off analytics" : "Allow optional analytics";
      status.textContent = allowed
        ? "Google Analytics is allowed for this browser."
        : "Optional Google Analytics is off.";
      if (allowed) startAnalytics();
      else window[disableKey] = true;
    }
    syncPreferences(readConsent());
    button.addEventListener("click", () => {
      const next = !readConsent();
      try { localStorage.setItem(consentKey, next ? "allow" : "deny"); }
      catch {
        window[disableKey] = true;
        status.textContent = "Could not save this setting. Analytics is off on this page.";
        return;
      }
      if (!next) {
        for (const cookie of document.cookie.split(";")) {
          const name = cookie.split("=")[0].trim();
          if (/^_ga(?:_[A-Z0-9]+)?$/.test(name)) {
            document.cookie = name + "=; Max-Age=0; Path=/; SameSite=Lax; Secure";
            document.cookie = name + "=; Max-Age=0; Path=/; Domain=" + location.hostname + "; SameSite=Lax; Secure";
          }
        }
      }
      syncPreferences(next);
    });
    window.addEventListener("storage", (event) => {
      if (event.key === consentKey || event.key === null) syncPreferences(readConsent());
    });
  }

  const form = document.querySelector("[data-contact-form]");
  const service = config.emailServiceId;
  const template = config.emailTemplateId;
  const publicKey = config.emailPublicKey;
  const publicToken = (value) => typeof value === "string" && /^[\w-]{5,100}$/.test(value);
  if (!form || ![service, template, publicKey].every(publicToken) ||
      location.protocol !== "https:") return;

  const button = form.querySelector("button[type=submit]");
  const status = form.querySelector("[data-form-status]");
  let sending = false;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (sending || !form.reportValidity()) return;
    const data = new FormData(form);
    if (data.get("website")) return;
    data.delete("website");
    for (const field of ["from_name", "reply_to", "message"]) {
      const cleaned = String(data.get(field) || "").trim();
      if (!cleaned) {
        status.textContent = "Please fill out all three fields.";
        form.elements.namedItem(field)?.focus();
        return;
      }
      data.set(field, cleaned);
    }
    data.set("service_id", service);
    data.set("template_id", template);
    data.set("user_id", publicKey);
    sending = true;
    button.disabled = true;
    status.textContent = "Sending…";
    try {
      const response = await fetch("https://api.emailjs.com/api/v1.0/email/send-form", {
        method: "POST",
        body: data,
        credentials: "omit",
        referrerPolicy: "strict-origin",
      });
      if (!response.ok) throw new Error("Email service unavailable");
      form.reset();
      status.textContent = "Sent! Thanks for getting in touch.";
    } catch {
      status.textContent = "Couldn’t send your message. Your draft is still here. Try again or use Email me.";
    } finally {
      sending = false;
      button.disabled = false;
    }
  });
  form.hidden = false;
})();
