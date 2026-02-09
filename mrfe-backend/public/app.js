const state = {
    token: "",
    eventId: "",
    fingerprintId: "",
    forecastId: "",
    modelId: "",
    socket: null,
};

const dom = {
    userId: document.getElementById("userId"),
    roles: document.getElementById("roles"),
    newsSource: document.getElementById("newsSource"),
    newsContent: document.getElementById("newsContent"),
    assetSymbol: document.getElementById("assetSymbol"),
    horizon: document.getElementById("horizon"),
    riskProfile: document.getElementById("riskProfile"),
    modelName: document.getElementById("modelName"),
    modelVersion: document.getElementById("modelVersion"),
    tokenPreview: document.getElementById("tokenPreview"),
    eventId: document.getElementById("eventId"),
    fingerprintId: document.getElementById("fingerprintId"),
    forecastId: document.getElementById("forecastId"),
    modelId: document.getElementById("modelId"),
    providerMode: document.getElementById("providerMode"),
    resultConsole: document.getElementById("resultConsole"),
    systemStatus: document.getElementById("systemStatus"),
    wsLog: document.getElementById("wsLog"),
    issueTokenBtn: document.getElementById("issueTokenBtn"),
    detectBtn: document.getElementById("detectBtn"),
    fingerprintBtn: document.getElementById("fingerprintBtn"),
    forecastBtn: document.getElementById("forecastBtn"),
    intelBtn: document.getElementById("intelBtn"),
    registerModelBtn: document.getElementById("registerModelBtn"),
    runDriftBtn: document.getElementById("runDriftBtn"),
    wsConnectBtn: document.getElementById("wsConnectBtn"),
    wsPingBtn: document.getElementById("wsPingBtn"),
};

function setResult(data) {
    dom.resultConsole.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
}

function setStatus(message, healthy) {
    dom.systemStatus.textContent = `System status: ${message}`;
    dom.systemStatus.style.color = healthy ? "#79ff5f" : "#ffb347";
    dom.systemStatus.style.borderColor = healthy
        ? "rgba(121, 255, 95, 0.45)"
        : "rgba(255, 179, 71, 0.55)";
}

async function request(path, options = {}, authenticated = true) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (authenticated && state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }
    const response = await fetch(path, { ...options, headers });
    const text = await response.text();
    let data = text;
    try {
        data = text ? JSON.parse(text) : {};
    } catch (_error) {
        // Keep raw text payload when response is not JSON.
    }
    if (!response.ok) {
        throw new Error(typeof data === "string" ? data : JSON.stringify(data));
    }
    return data;
}

async function issueToken() {
    const roles = dom.roles.value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);
    const payload = { user_id: dom.userId.value.trim(), roles: roles.length > 0 ? roles : ["reader"] };
    const result = await request(
        "/api/v1/auth/token",
        {
            method: "POST",
            body: JSON.stringify(payload),
        },
        false,
    );
    state.token = result.access_token;
    dom.tokenPreview.textContent =
        `${result.access_token.slice(0, 18)}...${result.access_token.slice(-14)}`;
    setResult(result);
    await refreshCapabilities();
}

async function detectEvent() {
    const payload = {
        source: dom.newsSource.value.trim(),
        news_content: dom.newsContent.value.trim(),
    };
    const result = await request("/api/v1/events/detect", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    if (Array.isArray(result) && result.length > 0) {
        state.eventId = result[0].event_id;
        dom.eventId.textContent = state.eventId;
    }
    setResult(result);
}

async function generateFingerprint() {
    if (!state.eventId) {
        throw new Error("Detect an event first.");
    }
    const payload = {
        event_id: state.eventId,
        asset_symbol: dom.assetSymbol.value.trim().toUpperCase(),
        model_version: "v2",
    };
    const result = await request("/api/v1/fingerprints", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    state.fingerprintId = result.fingerprint_id;
    dom.fingerprintId.textContent = state.fingerprintId;
    setResult(result);
}

async function generateForecast() {
    if (!state.eventId || !state.fingerprintId) {
        throw new Error("Generate event and fingerprint first.");
    }
    const payload = {
        event_id: state.eventId,
        fingerprint_id: state.fingerprintId,
        asset_symbol: dom.assetSymbol.value.trim().toUpperCase(),
        forecast_horizon_hours: Number(dom.horizon.value),
        model_version: "v2",
    };
    const result = await request("/api/v1/forecasts", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    state.forecastId = result.forecast_id;
    dom.forecastId.textContent = state.forecastId;
    setResult(result);
}

async function generateIntel() {
    const payload = {
        symbol: dom.assetSymbol.value.trim().toUpperCase(),
        market_context: dom.newsContent.value.trim(),
        horizon_hours: Number(dom.horizon.value),
        risk_profile: dom.riskProfile.value,
    };
    const result = await request("/api/v1/intel/brief", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    setResult(result);
}

async function registerModel() {
    const modelName = dom.modelName.value.trim();
    const modelVersion = dom.modelVersion.value.trim();
    const payload = {
        name: modelName,
        version: modelVersion,
        framework: "pytorch",
        artifact_uri: `s3://mrfe/models/${modelName}/${modelVersion}`,
        tags: {
            owner: dom.userId.value.trim() || "unknown",
            source: "dashboard",
        },
    };
    const result = await request("/api/v1/ml/models/register", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    state.modelId = result.model_id;
    dom.modelId.textContent = state.modelId;
    setResult(result);
}

async function runDriftCheck() {
    const payload = {
        model_version: dom.modelVersion.value.trim(),
        baseline_distribution: {
            strong_negative: 0.08,
            negative: 0.14,
            neutral: 0.52,
            positive: 0.18,
            strong_positive: 0.08,
        },
        live_distribution: {
            strong_negative: 0.16,
            negative: 0.2,
            neutral: 0.36,
            positive: 0.19,
            strong_positive: 0.09,
        },
    };
    const result = await request("/api/v1/ml/drift/check", {
        method: "POST",
        body: JSON.stringify(payload),
    });
    setResult(result);
}

async function healthCheck() {
    try {
        const result = await request("/health/ready", {}, false);
        setStatus(result.status || "ready", true);
    } catch (_error) {
        setStatus("degraded", false);
    }
}

async function refreshCapabilities() {
    if (!state.token) {
        dom.providerMode.textContent = "token required";
        return;
    }
    try {
        const result = await request("/api/v1/intel/capabilities");
        dom.providerMode.textContent = result.llm_available
            ? `${result.provider} (${result.model})`
            : `${result.provider} with ${result.fallback_mode}`;
    } catch (_error) {
        dom.providerMode.textContent = "unavailable";
    }
}

function socketBase() {
    const isSecure = window.location.protocol === "https:";
    return `${isSecure ? "wss" : "ws"}://${window.location.host}`;
}

function connectStream() {
    if (state.socket && state.socket.readyState === WebSocket.OPEN) {
        return;
    }
    state.socket = new WebSocket(`${socketBase()}/ws/market`);
    state.socket.onopen = () => {
        dom.wsLog.textContent = "connected to topic: market";
    };
    state.socket.onmessage = (event) => {
        dom.wsLog.textContent = `${dom.wsLog.textContent}\n${event.data}`;
        dom.wsLog.scrollTop = dom.wsLog.scrollHeight;
    };
    state.socket.onclose = () => {
        dom.wsLog.textContent = `${dom.wsLog.textContent}\nconnection closed`;
    };
    state.socket.onerror = () => {
        dom.wsLog.textContent = `${dom.wsLog.textContent}\nstream error`;
    };
}

function sendStreamPing() {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
        throw new Error("Connect WebSocket stream first.");
    }
    const payload = JSON.stringify({
        ts: new Date().toISOString(),
        message: "market-ping",
    });
    state.socket.send(payload);
}

function bindAction(button, callback) {
    if (!button) {
        return;
    }
    button.addEventListener("click", async () => {
        try {
            await callback();
        } catch (error) {
            const message = error instanceof Error ? error.message : "unknown error";
            setResult({ error: message });
        }
    });
}

bindAction(dom.issueTokenBtn, issueToken);
bindAction(dom.detectBtn, detectEvent);
bindAction(dom.fingerprintBtn, generateFingerprint);
bindAction(dom.forecastBtn, generateForecast);
bindAction(dom.intelBtn, generateIntel);
bindAction(dom.registerModelBtn, registerModel);
bindAction(dom.runDriftBtn, runDriftCheck);
bindAction(dom.wsConnectBtn, async () => connectStream());
bindAction(dom.wsPingBtn, async () => sendStreamPing());

void healthCheck();
