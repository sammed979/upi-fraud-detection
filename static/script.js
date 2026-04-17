// ── State ─────────────────────────────────────────────────────────────────────
let isNew    = true;
let qrScanner = null;
let lastUpiId = "";

// ── Toggle first-time receiver ────────────────────────────────────────────────
function toggleNew() {
    isNew = !isNew;
    document.getElementById("is_new").value = isNew;
    const btn = document.getElementById("toggle-btn");
    const dot = document.getElementById("toggle-dot");
    if (isNew) {
        btn.classList.replace("bg-gray-600", "bg-blue-600");
        dot.classList.replace("left-1", "right-1");
    } else {
        btn.classList.replace("bg-blue-600", "bg-gray-600");
        dot.classList.replace("right-1", "left-1");
    }
}

// ── QR Scanner ────────────────────────────────────────────────────────────────
function toggleQR() {
    const container = document.getElementById("qr-container");
    if (container.classList.contains("hidden")) {
        container.classList.remove("hidden");
        qrScanner = new Html5Qrcode("qr-reader");
        qrScanner.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: 200 },
            (text) => {
                // Extract UPI ID from QR text (pa=upi_id)
                const match = text.match(/pa=([^&]+)/);
                if (match) {
                    document.getElementById("upi_id").value = decodeURIComponent(match[1]);
                } else {
                    document.getElementById("upi_id").value = text;
                }
                stopQR();
            }
        ).catch(console.error);
    } else {
        stopQR();
    }
}

function stopQR() {
    if (qrScanner) {
        qrScanner.stop().then(() => {
            document.getElementById("qr-container").classList.add("hidden");
            qrScanner = null;
        });
    }
}

// ── Analyze ───────────────────────────────────────────────────────────────────
async function analyze() {
    const upi_id  = document.getElementById("upi_id").value.trim();
    const amount  = parseFloat(document.getElementById("amount").value);
    const purpose = document.getElementById("purpose").value;
    const btn     = document.getElementById("analyze-btn");

    // Basic validation
    if (!upi_id) { alert("Please enter a UPI ID"); return; }
    if (!amount || amount <= 0) { alert("Please enter a valid amount"); return; }

    lastUpiId = upi_id;
    btn.textContent = "Analyzing...";
    btn.disabled    = true;

    try {
        const res  = await fetch("/analyze", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ upi_id, amount, purpose, is_new_receiver: isNew }),
        });
        const data = await res.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        showResult(data);
        appendLogRow(upi_id, amount, purpose, data);

    } catch (e) {
        alert("Server error. Make sure Flask is running.");
    } finally {
        btn.textContent = "Analyze Transaction";
        btn.disabled    = false;
    }
}

// ── Show result ───────────────────────────────────────────────────────────────
function showResult(data) {
    document.getElementById("empty-state").classList.add("hidden");
    document.getElementById("result-panel").classList.remove("hidden");

    const score = data.risk_score;
    const level = data.risk_level;

    // Score circle colour
    const circle = document.getElementById("score-circle");
    circle.className = "w-24 h-24 rounded-full border-4 flex flex-col items-center justify-center shrink-0 ";
    if (level === "HIGH RISK")    circle.className += "border-red-500 text-red-400";
    else if (level === "SUSPICIOUS") circle.className += "border-yellow-500 text-yellow-400";
    else                          circle.className += "border-green-500 text-green-400";

    document.getElementById("score-number").textContent = score;

    // Risk badge
    const badge = document.getElementById("risk-badge");
    badge.textContent = level === "SAFE" ? "SAFE" : level === "SUSPICIOUS" ? "SUSPICIOUS" : "HIGH RISK";
    badge.className   = "text-lg font-bold mb-1 " +
        (level === "HIGH RISK" ? "text-red-400" : level === "SUSPICIOUS" ? "text-yellow-400" : "text-green-400");

    document.getElementById("explanation").textContent = data.explanation;

    // Breakdown
    document.getElementById("rule-score").textContent = data.rule_score + " / 100";
    document.getElementById("ml-score").textContent   = data.ml_score   + " / 100";
    const finalRow = document.getElementById("final-score-row");
    finalRow.textContent  = score + " / 100";
    finalRow.className    = "font-bold " +
        (level === "HIGH RISK" ? "text-red-400" : level === "SUSPICIOUS" ? "text-yellow-400" : "text-green-400");

    // Trust bar (inverted — high score = low trust)
    const trust     = Math.max(0, 100 - score);
    const trustBar  = document.getElementById("trust-bar");
    const trustLabel = document.getElementById("trust-label");
    trustBar.style.width = trust + "%";
    trustBar.className   = "h-full rounded-full transition-all duration-700 " +
        (trust >= 60 ? "bg-green-500" : trust >= 30 ? "bg-yellow-500" : "bg-red-500");
    trustLabel.textContent = trust + "% Trust";

    // Reported badge
    const repBadge = document.getElementById("reported-badge");
    data.reported ? repBadge.classList.remove("hidden") : repBadge.classList.add("hidden");
}

// ── Report fraud ──────────────────────────────────────────────────────────────
async function reportFraud() {
    if (!lastUpiId) { alert("Analyze a transaction first"); return; }
    const reason = prompt("Reason for reporting (optional):") || "Reported by user";

    const res  = await fetch("/report", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ upi_id: lastUpiId, reason }),
    });
    const data = await res.json();
    if (data.status === "reported") {
        alert(lastUpiId + " has been reported. Thank you!");
        document.getElementById("reported-badge").classList.remove("hidden");
    }
}

// ── Reset form ────────────────────────────────────────────────────────────────
function resetForm() {
    document.getElementById("upi_id").value  = "";
    document.getElementById("amount").value  = "";
    document.getElementById("result-panel").classList.add("hidden");
    document.getElementById("empty-state").classList.remove("hidden");
    lastUpiId = "";
}

// ── Append new row to logs table without page reload ─────────────────────────
function appendLogRow(upi_id, amount, purpose, data) {
    const tbody = document.getElementById("logs-body");
    const level = data.risk_level;
    const colourScore = level === "HIGH RISK" ? "text-red-400" : level === "SUSPICIOUS" ? "text-yellow-400" : "text-green-400";
    const colourBadge = level === "HIGH RISK"
        ? "bg-red-900 text-red-400"
        : level === "SUSPICIOUS"
        ? "bg-yellow-900 text-yellow-400"
        : "bg-green-900 text-green-400";

    const now = new Date().toISOString().slice(0, 16).replace("T", " ");
    const tr  = document.createElement("tr");
    tr.className = "border-b border-gray-800 hover:bg-gray-800 transition-colors";
    tr.innerHTML = `
        <td class="py-3 text-gray-300">${upi_id}</td>
        <td class="py-3 text-gray-300">Rs.${Math.round(amount)}</td>
        <td class="py-3 text-gray-400 capitalize">${purpose}</td>
        <td class="py-3 font-medium ${colourScore}">${data.risk_score}</td>
        <td class="py-3"><span class="px-2 py-1 rounded-full text-xs font-semibold ${colourBadge}">${level}</span></td>
        <td class="py-3 text-gray-500 text-xs">${now}</td>`;

    // Remove "no checks yet" row if present
    const empty = tbody.querySelector("td[colspan]");
    if (empty) empty.parentElement.remove();

    tbody.insertBefore(tr, tbody.firstChild);
}
