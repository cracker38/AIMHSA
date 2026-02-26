(() => {
  // Get API URL from configuration
  const getAPIBaseUrl = () => {
    if (window.AIMHSA && window.AIMHSA.Config) {
      return window.AIMHSA.Config.getApiBaseUrl();
    }
    // Fallback to auto-detection
    return window.location.origin;
  };
  
  const API_BASE_URL = getAPIBaseUrl();
  
  // Display emergency booking notification
  function displayEmergencyBooking(bookingData) {
    const emergencyCard = document.createElement("div");
    emergencyCard.className = "emergency-booking-card";
    emergencyCard.innerHTML = `
      <div class="emergency-booking-content">
        <div class="emergency-icon">🚨</div>
        <h3>Emergency Support Scheduled</h3>
        <p>Based on our conversation, I've automatically scheduled you with a mental health professional for immediate support.</p>
        <div class="emergency-details">
          <div class="detail-item">
            <strong>Professional:</strong> ${bookingData.professional?.first_name || 'Dr. Professional'} ${bookingData.professional?.last_name || ''}
          </div>
          <div class="detail-item">
            <strong>Specialization:</strong> ${bookingData.professional?.specialization || 'Mental Health Professional'}
          </div>
          <div class="detail-item">
            <strong>Booking ID:</strong> ${bookingData.booking_id || 'N/A'}
          </div>
        </div>
        <div class="emergency-info">
          <p><strong>You will receive SMS confirmation shortly.</strong></p>
          <p>If this is a life-threatening emergency, please call 112 or go to your nearest emergency room.</p>
        </div>
      </div>
    `;
    
    // Add styling
    emergencyCard.style.cssText = `
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
      color: white;
      padding: 20px;
      border-radius: 12px;
      margin: 16px 0;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
      animation: slideIn 0.3s ease-out;
      border-left: 4px solid #fbbf24;
    `;
    
    // Add emergency-specific CSS
    if (!document.getElementById('emergency-animations')) {
      const style = document.createElement('style');
      style.id = 'emergency-animations';
      style.textContent = `
        .emergency-booking-content {
          text-align: center;
        }
        .emergency-icon {
          font-size: 48px;
          margin-bottom: 16px;
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.1); }
        }
        .emergency-booking-content h3 {
          margin: 0 0 12px 0;
          font-size: 18px;
          font-weight: 600;
        }
        .emergency-booking-content p {
          margin: 0 0 20px 0;
          opacity: 0.9;
          line-height: 1.5;
        }
        .emergency-details {
          background: rgba(255,255,255,0.1);
          padding: 16px;
          border-radius: 8px;
          margin: 16px 0;
          text-align: left;
        }
        .detail-item {
          margin-bottom: 8px;
        }
        .detail-item:last-child {
          margin-bottom: 0;
        }
        .emergency-info {
          background: rgba(251, 191, 36, 0.2);
          padding: 12px;
          border-radius: 8px;
          margin-top: 16px;
        }
        .emergency-info p {
          margin: 8px 0;
          font-size: 14px;
        }
      `;
      document.head.appendChild(style);
    }
    
    chatContainer.appendChild(emergencyCard);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
  
  // Request booking function
  async function requestBooking() {
    try {
      const payload = { conv_id: convId };
      if (account) payload.account = account;
      
      const resp = await api("/api/request-booking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (resp.success) {
        // Remove booking prompt
        const bookingCard = document.querySelector('.booking-prompt-card');
        if (bookingCard) bookingCard.remove();
        
        // Show success message
        appendMessage("assistant", `✅ ${resp.message}`);
        
        // Show booking details
        const bookingDetails = document.createElement("div");
        bookingDetails.className = "booking-success-card";
        bookingDetails.innerHTML = `
          <div class="booking-success-content">
            <div class="success-icon">✅</div>
            <h3>Booking Confirmed!</h3>
            <div class="booking-details">
              <p><strong>Professional:</strong> ${resp.professional.first_name} ${resp.professional.last_name}</p>
              <p><strong>Specialization:</strong> ${resp.professional.specialization}</p>
              <p><strong>Booking ID:</strong> ${resp.booking_id}</p>
              <p><strong>Risk Level:</strong> ${resp.risk_level}</p>
            </div>
            <p class="success-message">You will receive SMS confirmation shortly with session details.</p>
          </div>
        `;
        
        bookingDetails.style.cssText = `
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          padding: 20px;
          border-radius: 12px;
          margin: 16px 0;
          box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
          animation: slideIn 0.3s ease-out;
        `;
        
        chatContainer.appendChild(bookingDetails);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
      } else {
        appendMessage("assistant", `❌ ${resp.error || 'Booking request failed. Please try again.'}`);
      }
    } catch (error) {
      console.error("Booking request error:", error);
      appendMessage("assistant", "❌ Unable to process booking request. Please try again later.");
    }
  }
  
  // Decline booking function
  function declineBooking() {
    const bookingCard = document.querySelector('.booking-prompt-card');
    if (bookingCard) bookingCard.remove();
    
    appendMessage("assistant", "No problem! I'm here to continue our conversation. Feel free to reach out anytime if you'd like to speak with a professional.");
  }
  
  // Make functions globally available
  window.requestBooking = requestBooking;
  window.declineBooking = declineBooking;
  
  // Check authentication
  const account = localStorage.getItem("aimhsa_account");
  const professionalData = localStorage.getItem("aimhsa_professional");
  const adminData = localStorage.getItem("aimhsa_admin");
  
  if (professionalData) {
      alert('You are logged in as a professional. Please logout and login as a regular user to use the chat.');
      window.location.href = '/professional_dashboard.html';
      return;
  }
  
  if (adminData) {
      alert('You are logged in as an admin. Please logout and login as a regular user to use the chat.');
      window.location.href = '/admin_dashboard.html';
      return;
  }
  
  if (!account) {
      window.location.href = '/login';
      return;
  }
  
  // Elements
  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("form");
  const queryInput = document.getElementById("query");
  const sendBtn = document.getElementById("send");
  const fileInput = document.getElementById("file");
  const composer = form; // composer container (used for inserting preview)
  const historyList = document.getElementById("historyList");
  const newChatBtn = document.getElementById("newChatBtn");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const clearHistoryBtn = document.getElementById("clearHistoryBtn");
  const logoutBtn = document.getElementById("logoutBtn");
  const usernameEl = document.getElementById("username");
  const archivedList = document.getElementById("archivedList");
  
  let convId = localStorage.getItem("aimhsa_conv") || null;
  let typingEl = null;
  let currentPreview = null;
  const archivedPwById = new Map();
  // Model selection: via URL (?model=xyz) or localStorage (aimhsa_model)
  const urlParams = new URLSearchParams(window.location.search || "");
  const urlModel = (urlParams.get('model') || '').trim();
  if (urlModel) {
    try { localStorage.setItem('aimhsa_model', urlModel); } catch (_) {}
  }
  function getSelectedModel() {
    try { return (localStorage.getItem('aimhsa_model') || '').trim() || null; } catch (_) { return null; }
  }
  
  // Set username
  usernameEl.textContent = account === 'null' ? 'Guest' : account;
  
  // Inject runtime CSS for animations & preview (keeps frontend simple)
  (function injectStyles(){
    const css = `
      @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity:1; transform:none; } }
      .fade-in { animation: fadeIn 280ms ease both; }
      .typing { display:flex; align-items:center; gap:8px; padding:8px 12px; border-radius:10px; width:fit-content; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.03); }
      .dots { display:inline-block; width:36px; text-align:center; }
      .dot { display:inline-block; width:6px; height:6px; margin:0 2px; background:var(--muted); border-radius:50%; opacity:0.25; animation: blink 1s infinite; }
      .dot:nth-child(2){ animation-delay: .2s; } .dot:nth-child(3){ animation-delay: .4s; }
      @keyframes blink { 0%{opacity:.25} 50%{opacity:1} 100%{opacity:.25} }
      .upload-preview { display:flex; align-items:center; gap:12px; padding:8px 10px; border-radius:8px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.03); margin-right:auto; max-width:420px; }
      .upload-meta { display:flex; flex-direction:column; gap:4px; font-size:13px; color:var(--muted); }
      .upload-filename { font-weight:600; color:var(--text); }
      .upload-actions { display:flex; gap:8px; align-items:center; }
      .progress-bar { width:160px; height:8px; background:rgba(255,255,255,0.03); border-radius:6px; overflow:hidden; }
      .progress-inner { height:100%; width:0%; background:linear-gradient(90deg,var(--accent), #5b21b6); transition:width .2s ease; }
      .btn-small { padding:6px 8px; border-radius:8px; background:transparent; border:1px solid rgba(255,255,255,0.04); color:var(--muted); cursor:pointer; font-size:12px; }
      .sending { opacity:0.7; transform:scale(.98); transition:transform .12s ease, opacity .12s ease; }
      .msg.fade-in { transform-origin: left top; }
    `;
    const s = document.createElement("style");
    s.textContent = css;
    document.head.appendChild(s);
  })();

  // helper: ensure messages container scrolls to bottom after layout updates
  function ensureScroll() {
    const doScroll = () => {
      try {
        const last = messagesEl.lastElementChild;
        if (last && typeof last.scrollIntoView === "function") {
          last.scrollIntoView({ behavior: "smooth", block: "end", inline: "nearest" });
        } else {
          messagesEl.scrollTop = messagesEl.scrollHeight;
        }
      } catch (e) {
        try { messagesEl.scrollTop = messagesEl.scrollHeight; } catch (_) {}
      }
    };
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setTimeout(doScroll, 40);
      });
    });
  }

  // Logout handler
  logoutBtn.addEventListener("click", () => {
    localStorage.removeItem("aimhsa_account");
    localStorage.removeItem("aimhsa_conv");
    localStorage.removeItem("aimhsa_professional");
    localStorage.removeItem("aimhsa_admin");
    window.location.href = '/login';
  });
  
  // Modern message display
  function appendMessage(role, text) {
      const msgDiv = document.createElement("div");
      msgDiv.className = `msg ${role === "user" ? "user" : "bot"}`;
      
      const contentDiv = document.createElement("div");
      contentDiv.className = "msg-content";
      
      const metaDiv = document.createElement("div");
      metaDiv.className = "msg-meta";
      metaDiv.textContent = role === "user" ? "You" : "AIMHSA";
      
      const textDiv = document.createElement("div");
      textDiv.className = "msg-text";
      textDiv.textContent = text;
      
      contentDiv.appendChild(metaDiv);
      contentDiv.appendChild(textDiv);
      msgDiv.appendChild(contentDiv);
      
      messagesEl.appendChild(msgDiv);
      ensureScroll();
      return msgDiv;
  }
  
  function createTypingIndicator() {
      if (typingEl) return;
      typingEl = document.createElement("div");
      typingEl.className = "msg bot";
      
      const contentDiv = document.createElement("div");
      contentDiv.className = "typing";
      
      const dotsDiv = document.createElement("div");
      dotsDiv.className = "typing-dots";
      dotsDiv.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
      
      contentDiv.appendChild(dotsDiv);
      typingEl.appendChild(contentDiv);
      messagesEl.appendChild(typingEl);
      ensureScroll();
  }
  
  function removeTypingIndicator() {
      if (!typingEl) return;
      typingEl.remove();
      typingEl = null;
  }
  
  async function api(path, opts) {
    const base = (typeof API_BASE_URL === 'string' && API_BASE_URL) ? API_BASE_URL : (window.location.origin || '');
    const endpoints = [
      base + path,
      base + '/api' + path
    ];
    console.log('[AIMHSA API] Base URL:', base, '| Path:', path, '| Will try:', endpoints[0]);
    let lastError;
    for (const url of endpoints) {
      try {
        const res = await fetch(url, opts);
        console.log('[AIMHSA API] Response:', url, 'Status:', res.status, res.statusText);
        if (res.ok) {
          const data = await res.json();
          console.log('[AIMHSA API] Success:', path, 'answer length:', (data.answer && data.answer.length) || 0);
          return data;
        }
        const txt = await res.text();
        console.error('[AIMHSA API] Error response:', res.status, url, txt.substring(0, 500));
        const err = new Error(txt || res.statusText);
        err.status = res.status;
        err.body = txt;
        throw err;
      } catch (error) {
        lastError = error;
        if (url === endpoints[0] && (error.message && error.message.includes('404') || (error.status === 404))) {
          console.warn('[AIMHSA API] 404 on first endpoint, trying next');
          continue;
        }
        throw error;
      }
    }
    throw lastError || new Error('All API endpoints failed');
  }

  async function initSession(useAccount = false) {
    const payload = {};
    if (useAccount && account) payload.account = account;
    try {
      const resp = await api("/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      convId = resp.id;
      localStorage.setItem("aimhsa_conv", convId);
      await loadHistory();
      await updateHistoryList();
    } catch (err) {
      console.error("session error", err);
      // Fallback: create a client-side conversation ID if server session fails
      if (!convId) {
        convId = newConvId();
        localStorage.setItem("aimhsa_conv", convId);
      }
      appendMessage("bot", "Session initialized. How can I help you today?");
    }
  }

  // helper to generate a client-side conv id when needed (fallback)
  function newConvId() {
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
    return "conv-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2,8);
  }

  async function loadHistory() {
    if (!convId) return;
    try {
      const pw = archivedPwById.get(convId);
      const url = "/history?id=" + encodeURIComponent(convId) + (pw ? ("&password=" + encodeURIComponent(pw)) : "");
      const resp = await api(url);
      messagesEl.innerHTML = "";
      const hist = resp.history || [];
      for (const m of hist) {
        appendMessage(m.role, m.content);
      }
      if (resp.attachments && resp.attachments.length) {
        resp.attachments.forEach(a => {
          appendMessage("bot", `Attachment (${a.filename}):\n` + (a.text.slice(0,400) + (a.text.length>400?"...[truncated]":"")));
        });
      }
      ensureScroll();
    } catch (err) {
      console.error("history load error", err);
      // If history fails to load, just show a welcome message
      if (messagesEl.children.length === 0) {
        appendMessage("bot", "Welcome! How can I help you today?");
      }
    }
  }

  // Auto-resize textarea
  function autoResizeTextarea() {
    queryInput.style.height = 'auto';
    const scrollHeight = queryInput.scrollHeight;
    const maxHeight = 120; // Match CSS max-height
    queryInput.style.height = Math.min(scrollHeight, maxHeight) + 'px';
  }

  // Add textarea auto-resize listener
  queryInput.addEventListener('input', autoResizeTextarea);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.dispatchEvent(new Event('submit'));
    }
  });

  async function sendMessage(query) {
    if (!query) return;
    disableComposer(true);
    appendMessage("user", query);
    createTypingIndicator();
    queryInput.value = "";
    autoResizeTextarea(); // Reset textarea height
    
    const payload = { id: convId, query, history: [] };
    if (account) payload.account = account;
    const model = getSelectedModel();
    if (model) payload.model = model;
    console.log('[AIMHSA] Sending /ask to', (typeof API_BASE_URL !== 'undefined' && API_BASE_URL) ? API_BASE_URL : window.location.origin, 'query:', query.substring(0, 60));

    try {
      const resp = await api("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      removeTypingIndicator();

      if (resp.answer && resp.answer.indexOf("rephrase your question") !== -1) {
        console.warn("[AIMHSA] Server returned 200 but answer is the generic fallback. AI may be unavailable or key not used.");
      }

      // Handle scope rejection with special styling
      if (resp.scope_rejection) {
        const botMessage = appendMessage("assistant", resp.answer);
        botMessage.classList.add("scope-rejection");
        // Add visual indicator for scope rejection
        const indicator = document.createElement("div");
        indicator.className = "scope-indicator";
        indicator.innerHTML = "🎯 Mental Health Focus";
        indicator.style.cssText = `
          font-size: 12px;
          color: #f59e0b;
          background: rgba(245, 158, 11, 0.1);
          padding: 4px 8px;
          border-radius: 4px;
          margin-top: 8px;
          display: inline-block;
        `;
        botMessage.querySelector('.msg-content').appendChild(indicator);
      } else {
        // Ensure we got a valid response
        if (!resp.answer || resp.answer.trim() === '') {
          appendMessage("assistant", "I'm here to help. Could you please rephrase your question?");
        } else {
          appendMessage("assistant", resp.answer);
        }
      }
      
      // Risk assessment is handled in backend only (no display)
      // But show booking confirmation to user
      if (resp.emergency_booking) {
        displayEmergencyBooking(resp.emergency_booking);
      }
      
      // Handle booking question from backend
      if (resp.ask_booking) {
        displayBookingQuestion(resp.booking_question || {
          message: "Based on our conversation, I believe you might benefit from speaking with a qualified mental health professional. Would you like me to schedule a session for you?",
          options: ["Yes, Schedule Session", "No, Continue Chat"]
        });
      }
      
      // Handle automatic booking creation
      if (resp.booking_created) {
        displayEmergencyBooking({
          booking_id: resp.booking_id,
          professional_name: resp.professional_name,
          specialization: resp.specialization,
          session_type: resp.session_type,
          scheduled_datetime: resp.scheduled_datetime
        });
      }
      
      if (resp.id && resp.id !== convId) {
        convId = resp.id;
        localStorage.setItem("aimhsa_conv", convId);
      }
      // refresh server-side conversation list for signed-in users
      if (account) await updateHistoryList();
    } catch (err) {
      console.error("[AIMHSA] /ask error:", err);
      console.error("[AIMHSA] message:", err && err.message);
      console.error("[AIMHSA] status:", err && err.status);
      console.error("[AIMHSA] body:", err && err.body);
      removeTypingIndicator();

      var errorDetail = (err && err.message) ? String(err.message) : String(err);
      if (err && err.status) errorDetail = "HTTP " + err.status + ": " + errorDetail;
      if (err && err.body) errorDetail += "\n\nResponse: " + (err.body ? err.body.substring(0, 500) : "(empty)");

      var userMsg = "Could not reach the server. Open browser console (F12 → Console) for details.";
      if (err && err.status === 500) userMsg = "Server error (500). Check server terminal and browser console.";
      if (err && err.message && (err.message.indexOf("Failed to fetch") !== -1 || err.message.indexOf("NetworkError") !== -1)) userMsg = "Network error. Is the server running?";

      appendMessage("bot", userMsg + "\n\n[Debug] " + errorDetail);
    } finally {
      disableComposer(false);
    }
  }

  // show upload preview block when a file is selected
  function showUploadPreview(file) {
    clearUploadPreview();
    const preview = document.createElement("div");
    preview.className = "upload-preview fade-in";
    preview.dataset.name = file.name;

    const icon = document.createElement("div");
    icon.style.fontSize = "20px";
    icon.textContent = "📄";

    const meta = document.createElement("div");
    meta.className = "upload-meta";
    const fname = document.createElement("div");
    fname.className = "upload-filename";
    fname.textContent = file.name;
    const fsize = document.createElement("div");
    fsize.className = "small";
    fsize.textContent = `${(file.size/1024).toFixed(1)} KB`;

    meta.appendChild(fname);
    meta.appendChild(fsize);

    const actions = document.createElement("div");
    actions.className = "upload-actions";
    const progress = document.createElement("div");
    progress.className = "progress-bar";
    const inner = document.createElement("div");
    inner.className = "progress-inner";
    progress.appendChild(inner);

    const removeBtn = document.createElement("button");
    removeBtn.className = "btn-small";
    removeBtn.type = "button";
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", () => {
      fileInput.value = "";
      clearUploadPreview();
    });

    actions.appendChild(progress);
    actions.appendChild(removeBtn);

    preview.appendChild(icon);
    preview.appendChild(meta);
    preview.appendChild(actions);

    // insert preview at left of composer (before send button)
    composer.insertBefore(preview, composer.firstChild);
    currentPreview = { el: preview, inner };
  }

  function updateUploadProgress(pct) {
    if (!currentPreview) return;
    currentPreview.inner.style.width = Math.max(0, Math.min(100, pct)) + "%";
  }

  function clearUploadPreview() {
    if (currentPreview && currentPreview.el) currentPreview.el.remove();
    currentPreview = null;
  }

  // Use XHR for upload to track progress
  function uploadPdf(file) {
    if (!file) return;
    disableComposer(true);
    showUploadPreview(file);

    // Try both endpoint patterns
    const tryUpload = (url) => {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", url, true);

        xhr.upload.onprogress = function(e) {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100);
            updateUploadProgress(pct);
          }
        };

        xhr.onload = function() {
          try {
            const resText = xhr.responseText || "{}";
            const data = JSON.parse(resText);
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(data);
            } else {
              reject(new Error(data.error || xhr.statusText));
            }
          } catch (err) {
            reject(new Error("Upload parsing error"));
          }
        };

        xhr.onerror = function() {
          reject(new Error("Upload network error"));
        };

        const fd = new FormData();
        fd.append("file", file, file.name);
        if (convId) fd.append("id", convId);
        if (account) fd.append("account", account);
        const model = getSelectedModel();
        if (model) fd.append("model", model);
        xhr.send(fd);
      });
    };

    // Try upload_pdf endpoint first, then api/upload_pdf as fallback
    tryUpload(API_BASE_URL + "/upload_pdf")
      .catch(() => tryUpload(API_BASE_URL + "/api/upload_pdf"))
      .then((data) => {
        disableComposer(false);
        convId = data.id;
        localStorage.setItem("aimhsa_conv", convId);
        appendMessage("bot", `Uploaded ${data.filename}. What would you like to know about this document?`);
        clearUploadPreview();
        if (account) updateHistoryList();
      })
      .catch((error) => {
        disableComposer(false);
        console.error("PDF upload failed:", error);
        appendMessage("bot", "PDF upload failed: " + error.message);
        clearUploadPreview();
      });
  }

  function disableComposer(disabled) {
    if (disabled) {
      sendBtn.disabled = true;
      sendBtn.classList.add("sending");
      fileInput.disabled = true;
      queryInput.disabled = true;
    } else {
      sendBtn.disabled = false;
      sendBtn.classList.remove("sending");
      fileInput.disabled = false;
      queryInput.disabled = false;
    }
  }

  // New chat: require account (server enforces too)
  newChatBtn.addEventListener('click', async () => {
    if (!account) {
      appendMessage("bot", "Please sign in to create and view saved conversations.");
      return;
    }
    try {
      const payload = { account };
      const resp = await api("/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (resp && resp.id) {
        convId = resp.id;
        localStorage.setItem("aimhsa_conv", convId);
        messagesEl.innerHTML = '';
        await updateHistoryList();
      }
    } catch (e) {
      console.error("failed to create conversation", e);
      appendMessage("bot", "Could not start new conversation. Try again.");
    }
  });

  // Clear only visual messages
  clearChatBtn.addEventListener("click", () => {
    if (!convId) return;
    
    if (confirm("Clear current messages? This will only clear the visible chat.")) {
      messagesEl.innerHTML = "";
      appendMessage("bot", "Messages cleared. How can I help you?");
    }
  });

  // Clear server-side history
  clearHistoryBtn.addEventListener("click", async () => {
    if (!convId) return;
    
    if (confirm("Are you sure? This will permanently clear all saved messages and attachments.")) {
      try {
        await api("/clear_chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: convId })
        });
        
        // Clear both messages and conversation history
        messagesEl.innerHTML = "";
        historyList.innerHTML = "";
        
        // Add default "no conversations" message
        const note = document.createElement('div');
        note.className = 'small';
        note.style.padding = '12px';
        note.style.color = 'var(--muted)';
        note.textContent = 'No conversations yet. Start a new chat!';
        historyList.appendChild(note);
        
        appendMessage("bot", "Chat history cleared. How can I help you?");
        
        // Start a new conversation if account exists
        if (account && account !== 'null') {
          const payload = { account };
          const resp = await api("/conversations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          });
          
          if (resp && resp.id) {
            convId = resp.id;
            localStorage.setItem("aimhsa_conv", convId);
            await updateHistoryList();
          }
        }
      } catch (err) {
        console.error("Failed to clear chat history", err);
        appendMessage("bot", "Failed to clear chat history on server. Try again.");
      }
    }
  });

  // show preview when file selected
  fileInput.addEventListener("change", (e) => {
    const f = fileInput.files[0];
    if (f) showUploadPreview(f);
    else clearUploadPreview();
  });

  const app = document.querySelector('.app');
  
  // Replace existing drag/drop handlers with:
  document.addEventListener('dragenter', (e) => {
    e.preventDefault();
    if (!e.dataTransfer.types.includes('Files')) return;
    app.classList.add('dragging');
  });

  document.addEventListener('dragleave', (e) => {
    e.preventDefault();
    // Only remove if actually leaving the app
    if (e.target === document || e.target === app) {
      app.classList.remove('dragging');
    }
  });

  document.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  document.addEventListener('drop', (e) => {
    e.preventDefault();
    app.classList.remove('dragging');
    
    const files = Array.from(e.dataTransfer.files);
    const pdfFile = files.find(f => f.type === 'application/pdf');
    
    if (pdfFile) {
      fileInput.files = e.dataTransfer.files;
      const event = new Event('change');
      fileInput.dispatchEvent(event);
      uploadPdf(pdfFile);
    } else {
      appendMessage('bot', 'Please drop a PDF file.');
    }
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = queryInput.value.trim();
    if (!q && !fileInput.files[0]) return;
    
    const file = fileInput.files[0];
    if (file) {
      uploadPdf(file);
      fileInput.value = "";
    } else {
      // ensure a convId exists for anonymous users too
      if (!convId) {
        convId = newConvId();
        localStorage.setItem("aimhsa_conv", convId);
      }
      sendMessage(q);
    }
  });

  // require signed-in account for server-backed conversations; otherwise show prompt
  async function updateHistoryList() {
    historyList.innerHTML = '';
    if (archivedList) archivedList.innerHTML = '';
    if (!account || account === 'null') {
      const note = document.createElement('div');
      note.className = 'small';
      note.style.padding = '12px';
      note.style.color = 'var(--text-muted)';
      note.textContent = 'Sign in to view and manage your conversation history.';
      historyList.appendChild(note);
      newChatBtn.disabled = true;
      newChatBtn.title = "Sign in to create server-backed conversations";
      return;
    }
    newChatBtn.disabled = false;
    newChatBtn.title = "";

    try {
      const q = "?account=" + encodeURIComponent(account);
      const resp = await api("/conversations" + q, { method: "GET" });
      const entries = resp.conversations || [];
      for (const historyData of entries) {
        const item = document.createElement('div');
        item.className = 'history-item' + (historyData.id === convId ? ' active' : '');

        const preview = document.createElement('div');
        preview.className = 'history-preview';
        preview.textContent = historyData.preview || 'New chat';
        preview.title = historyData.preview || 'New chat';

        // three-dot menu button
        const menuBtn = document.createElement('button');
        menuBtn.className = 'history-menu-btn';
        menuBtn.setAttribute('aria-label', 'Conversation actions');
        menuBtn.title = 'More';
        menuBtn.textContent = '...';

        // dropdown menu
        const menu = document.createElement('div');
        menu.className = 'history-menu';
        const renameBtn = document.createElement('button');
        renameBtn.textContent = 'Rename';
        const archiveBtn = document.createElement('button');
        archiveBtn.textContent = 'Archive';
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'danger';
        menu.appendChild(renameBtn);
        menu.appendChild(archiveBtn);
        menu.appendChild(deleteBtn);
        // rename
        renameBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const title = prompt('Rename conversation to:');
          if (title == null || title.trim() === '') return;
          try {
            await api('/conversations/rename', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ account, id: historyData.id, preview: title })
            });
            await updateHistoryList();
          } catch (err) {
            appendMessage('bot', 'Failed to rename conversation.');
          }
        });

        // selection
        item.addEventListener('click', () => switchConversation(historyData.id));

        // open/close menu
        menuBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          const isOpen = menu.classList.contains('open');
          document.querySelectorAll('.history-menu.open').forEach(m => m.classList.remove('open'));
          if (!isOpen) menu.classList.add('open');
        });

        document.addEventListener('click', () => {
          menu.classList.remove('open');
        });

        // archive (password required)
        archiveBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          let pw = prompt('Set a password to archive this conversation (required).');
          if (pw == null || pw.trim() === '') { appendMessage('bot', 'Archive cancelled: password required.'); return; }
          try {
            await api('/conversations/archive', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ account, id: historyData.id, archived: true, password: pw || '' })
            });
            if (historyData.id === convId) {
              messagesEl.innerHTML = '';
              convId = null;
              localStorage.removeItem('aimhsa_conv');
            }
            await updateHistoryList();
          } catch (err) {
            console.error('archive conversation failed', err);
            appendMessage('bot', 'Failed to archive conversation.');
          }
        });

        // delete
        deleteBtn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (!confirm('Delete this conversation? This cannot be undone.')) return;
          try {
            await api('/conversations/delete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ account, id: historyData.id })
            });
            if (historyData.id === convId) {
              messagesEl.innerHTML = '';
              convId = null;
              localStorage.removeItem('aimhsa_conv');
            }
            await updateHistoryList();
          } catch (err) {
            console.error('delete conversation failed', err);
            appendMessage('bot', 'Failed to delete conversation.');
          }
        });

        item.appendChild(preview);
        item.appendChild(menuBtn);
        item.appendChild(menu);
        historyList.appendChild(item);
      }
      // load archived
      try {
        const ar = await api('/conversations/archived' + q, { method: 'GET' });
        const archivedEntries = ar.conversations || [];
        for (const h of archivedEntries) {
          const item = document.createElement('div');
          item.className = 'history-item';
          const preview = document.createElement('div');
          preview.className = 'history-preview';
          preview.textContent = h.preview || 'New chat';
          preview.title = h.preview || 'New chat';

          const menuBtn = document.createElement('button');
          menuBtn.className = 'history-menu-btn';
          menuBtn.textContent = '...';
          const menu = document.createElement('div');
          menu.className = 'history-menu';
          const unarchiveBtn = document.createElement('button');
          unarchiveBtn.textContent = 'Unarchive';
          const deleteBtn = document.createElement('button');
          deleteBtn.textContent = 'Delete';
          deleteBtn.className = 'danger';
          // do not allow rename for archived
          menu.appendChild(unarchiveBtn);
          menu.appendChild(deleteBtn);

          item.addEventListener('click', async () => {
            try {
              await api('/history?id=' + encodeURIComponent(h.id));
              archivedPwById.delete(h.id);
              await switchConversation(h.id);
            } catch (e) {
              try {
                const pw = prompt('Enter password to open this archived conversation:');
                if (pw == null) return;
                await api('/history?id=' + encodeURIComponent(h.id) + '&password=' + encodeURIComponent(pw));
                archivedPwById.set(h.id, pw);
                await switchConversation(h.id);
              } catch (e2) {
                appendMessage('bot', 'Incorrect or missing password.');
              }
            }
          });
          menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = menu.classList.contains('open');
            document.querySelectorAll('.history-menu.open').forEach(m => m.classList.remove('open'));
            if (!isOpen) menu.classList.add('open');
          });
          document.addEventListener('click', () => { menu.classList.remove('open'); });

          unarchiveBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const pw = prompt('Enter archive password to unarchive:');
            if (pw == null || pw.trim() === '') { appendMessage('bot', 'Unarchive cancelled: password required.'); return; }
            try {
              await api('/conversations/archive', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account, id: h.id, archived: false, password: pw })
              });
              await updateHistoryList();
            } catch (err) {
              appendMessage('bot', 'Failed to unarchive conversation.');
            }
          });
          deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('Delete this conversation? This cannot be undone.')) return;
            const pw = prompt('Enter archive password to delete:');
            if (pw == null || pw.trim() === '') { appendMessage('bot', 'Delete cancelled: password required.'); return; }
            try {
              await api('/conversations/delete', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ account, id: h.id, password: pw })
              });
              await updateHistoryList();
            } catch (err) {
              appendMessage('bot', 'Failed to delete conversation.');
            }
          });

          item.appendChild(preview);
          item.appendChild(menuBtn);
          item.appendChild(menu);
          if (archivedList) archivedList.appendChild(item);
        }
      } catch (e2) {
        // ignore archived load errors, show main list anyway
      }
    } catch (e) {
      console.warn("failed to load conversations", e);
      const errNote = document.createElement('div');
      errNote.className = 'small';
      errNote.style.padding = '12px';
      errNote.style.color = 'var(--muted)';
      errNote.textContent = 'Unable to load conversations.';
      historyList.appendChild(errNote);
    }
  }

  // switch conversation -> set convId, persist selection and load history
  async function switchConversation(newConvId) {
    if (!newConvId || newConvId === convId) return;
    convId = newConvId;
    localStorage.setItem("aimhsa_conv", convId);
    await loadHistory();
    await updateHistoryList();
  }

  // Risk assessment is handled in backend only (no display)
  // But show booking confirmation to user
  function displayBookingQuestion(bookingQuestion) {
    // Safety check for undefined parameter
    if (!bookingQuestion) {
      bookingQuestion = {
        message: "Based on our conversation, I believe you might benefit from speaking with a qualified mental health professional. Would you like me to schedule a session for you?",
        options: ["Yes, Schedule Session", "No, Continue Chat"]
      };
    }
    
    // Ensure required properties exist
    if (!bookingQuestion.message) {
      bookingQuestion.message = "Based on our conversation, I believe you might benefit from speaking with a qualified mental health professional. Would you like me to schedule a session for you?";
    }
    if (!bookingQuestion.options || !Array.isArray(bookingQuestion.options) || bookingQuestion.options.length < 2) {
      bookingQuestion.options = ["Yes, Schedule Session", "No, Continue Chat"];
    }
    
    // Create booking question card
    const questionCard = document.createElement('div');
    questionCard.className = 'booking-question-card';
    questionCard.style.cssText = `
      margin: 12px 0;
      padding: 20px;
      border-radius: 8px;
      background: linear-gradient(135deg, #3b82f6, #1d4ed8);
      color: white;
      border: 2px solid #2563eb;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    `;
    
    questionCard.innerHTML = `
      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <div style="font-size: 24px; margin-right: 12px;">💬</div>
        <h3 style="margin: 0; font-size: 18px; font-weight: 700;">Professional Support Available</h3>
      </div>
      <p style="margin: 0 0 16px 0; font-size: 16px; opacity: 0.9;">
        ${bookingQuestion.message}
      </p>
      <div style="display: flex; gap: 12px;">
        <button id="booking-yes" style="
          padding: 12px 24px;
          border: none;
          border-radius: 6px;
          background: white;
          color: #3b82f6;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        ">${bookingQuestion.options[0]}</button>
        <button id="booking-no" style="
          padding: 12px 24px;
          border: 2px solid white;
          border-radius: 6px;
          background: transparent;
          color: white;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        ">${bookingQuestion.options[1]}</button>
      </div>
    `;
    
    // Insert after the last message
    const lastMessage = messagesEl.lastElementChild;
    if (lastMessage) {
      lastMessage.parentNode.insertBefore(questionCard, lastMessage.nextSibling);
    }
    
    // Add event listeners
    document.getElementById('booking-yes').addEventListener('click', () => {
      handleBookingResponse('yes');
      questionCard.remove();
    });
    
    document.getElementById('booking-no').addEventListener('click', () => {
      handleBookingResponse('no');
      questionCard.remove();
    });
    
    // Scroll to show the question
    questionCard.scrollIntoView({ behavior: 'smooth' });
  }
  
  async function handleBookingResponse(response) {
    try {
      const res = await api('/booking_response', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: convId,
          response: response,
          account: localStorage.getItem('aimhsa_account')
        })
      });
      
      const data = res; // api() already returns parsed JSON
      
      if (response === 'yes' && data.booking) {
        // Show booking confirmation
        displayEmergencyBooking(data.booking);
      } else {
        // Show acknowledgment message
        appendMessage("assistant", data.message || "No problem! I'm here whenever you need support.");
      }
    } catch (error) {
      console.error('Booking response error:', error);
      appendMessage("assistant", "Sorry, there was an error processing your response. Please try again.");
    }
  }
  
  // Removed language indicator UI for a cleaner experience
  
  function displayEmergencyBooking(booking) {
    // Support both scheduled_time and scheduled_datetime
    const scheduledTime = new Date((booking.scheduled_time || booking.scheduled_datetime) * 1000).toLocaleString();
    
    // Create emergency booking notification
    const bookingCard = document.createElement('div');
    bookingCard.className = 'emergency-booking-card';
    bookingCard.style.cssText = `
      margin: 12px 0;
      padding: 20px;
      border-radius: 8px;
      background: linear-gradient(135deg, #dc2626, #b91c1c);
      color: white;
      border: 2px solid #ef4444;
      box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
    `;
    
    bookingCard.innerHTML = `
      <div style="display: flex; align-items: center; margin-bottom: 12px;">
        <div style="font-size: 24px; margin-right: 12px;">🚨</div>
        <h3 style="margin: 0; font-size: 18px; font-weight: 700;">Emergency Session Scheduled</h3>
      </div>
      <div style="background: rgba(255, 255, 255, 0.1); padding: 12px; border-radius: 6px; margin-bottom: 12px;">
        <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Professional:</strong> ${booking.professional_name || (booking.professional ? `${booking.professional.first_name || ''} ${booking.professional.last_name || ''}` : 'Being assigned')}</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Specialization:</strong> ${booking.specialization || (booking.professional ? booking.professional.specialization : 'Mental Health Professional')}</p>
        <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Scheduled:</strong> ${scheduledTime}</p>
        <p style="margin: 0; font-size: 14px;"><strong>Session Type:</strong> ${booking.session_type || booking.professional?.session_type || 'Emergency Consultation'}</p>
      </div>
      <p style="margin: 0; font-size: 14px; opacity: 0.9;">
        A mental health professional has been automatically assigned to provide immediate support. 
        They will contact you shortly to confirm the session details.
      </p>
    `;
    
    // Insert after the last message
    const lastMessage = messagesEl.lastElementChild;
    if (lastMessage) {
      lastMessage.parentNode.insertBefore(bookingCard, lastMessage.nextSibling);
    }
    
    // Scroll to show the notification
    bookingCard.scrollIntoView({ behavior: 'smooth' });
  }

  // initial load: start session (account-bound when available) and refresh history list
  (async () => {
    if (account) {
      await initSession(true);
    } else {
      await initSession(false);
    }
    await updateHistoryList();
  })();
})();