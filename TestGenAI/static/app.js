(() => {
    const state = { testFile: "", codeFile: "", language: "python", tests: "", explanation: "" };
    const el = (id) => document.getElementById(id);
    const prismLanguage = { python: "python", java: "java", javascript: "javascript" };

    // --- tabs ---
    document.querySelectorAll(".tab-btn").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach((item) => {
                item.classList.remove("active");
                item.setAttribute("aria-selected", "false");
            });
            document.querySelectorAll(".tab-panel").forEach((item) => { item.hidden = true; });

            button.classList.add("active");
            button.setAttribute("aria-selected", "true");
            el("tab-" + button.dataset.tab).hidden = false;
        });
    });

    // --- file upload ---
    el("file").addEventListener("change", () => {
        const file = el("file").files[0];
        el("fileName").textContent = file ? file.name : "No file selected";
        if (!file) return;
        const reader = new FileReader();
        reader.onload = () => { el("code").value = reader.result; };
        reader.readAsText(file);
    });

    // --- generate tests ---
    el("generate").addEventListener("click", async () => {
        if (!el("code").value.trim() && !el("file").files[0]) {
            showAlert("Please paste code or upload a file first.");
            return;
        }

        setBusy(true, "Generating tests…");
        clearAlert();
        el("output").textContent = "No tests run yet.";
        el("explanation-section").hidden = true;
        resetCounters();

        const form = new FormData();
        form.append("language", el("language").value);
        form.append("code", el("code").value);
        form.append("requirements", el("requirements").value);
        form.append("mode", el("mode").value);
        if (el("file").files[0]) form.append("code_file", el("file").files[0]);

        try {
            const data = await postForm("/generate_tests", form);
            state.testFile = data.test_file;
            state.codeFile = data.code_file;
            state.language = data.language;
            state.tests = data.tests;
            state.explanation = data.explanation || "";
            renderTests(data.tests, data.language);
            setActions(true);
            setStatus("ok", "Generated " + data.test_file);
        } catch (error) {
            showAlert(error.message);
            setActions(false);
            setStatus("error", "Generation failed");
        } finally {
            setBusy(false);
        }
    });

    // --- explain ---
    el("explainBtn").addEventListener("click", () => {
        if (!state.explanation) {
            showAlert("Generate tests first.");
            return;
        }
        el("explanation-content").textContent = state.explanation;
        el("explanation-section").hidden = false;
    });

    // --- pre-check / analyze ---
    el("analyzeBtn").addEventListener("click", async () => {
        if (!el("code").value.trim()) {
            showAlert("Please paste code in the Code tab first.");
            return;
        }

        setBusy(true, "Checking…");
        clearAlert();
        try {
            const data = await postJson("/analyze_code", {
                code: el("code").value,
                language: el("language").value,
                description: el("description").value,
            });
            renderAnalysis(data.analysis);
            setStatus("ok", "Pre-check complete");
        } catch (error) {
            showAlert(error.message);
            setStatus("error", "Pre-check failed");
        } finally {
            setBusy(false);
        }
    });

    // --- copy / download ---
    el("copy").addEventListener("click", async () => {
        await navigator.clipboard.writeText(state.tests);
        setStatus("ok", "Copied to clipboard");
    });

    el("download").addEventListener("click", () => {
        if (state.testFile) window.location.href = "/download_test/" + encodeURIComponent(state.testFile);
    });

    // --- run tests ---
    el("run").addEventListener("click", async () => {
        setBusy(true, "Running tests…");
        clearAlert();
        try {
            const data = await postJson("/run_tests", {
                language: state.language,
                test_file: state.testFile,
                code_file: state.codeFile,
            });
            el("output").textContent = data.output || data.error || "No output.";
            updateCounters(data);
            setStatus(data.success ? "ok" : "error", data.success ? "Tests passed" : "Tests failed");
            if (!data.success && data.error) showAlert(data.error);
        } catch (error) {
            showAlert(error.message);
            setStatus("error", "Run failed");
        } finally {
            setBusy(false);
        }
    });

    // --- render helpers ---

    function renderTests(code, language) {
        const codeEl = el("tests");
        codeEl.className = "language-" + (prismLanguage[language] || "python");
        codeEl.textContent = code;
        if (window.Prism) Prism.highlightElement(codeEl);
    }

    function renderAnalysis(analysis) {
        const box = el("analysis-output");
        box.hidden = false;
        box.innerHTML = `
            <h2>Pre-check result</h2>
            <p><strong>Quality score:</strong> ${analysis.quality_score}/100</p>
            <p><strong>Strengths:</strong> ${listText(analysis.strengths)}</p>
            <p><strong>Weaknesses:</strong> ${listText(analysis.weaknesses)}</p>
            <p><strong>Suggestions:</strong> ${listText(analysis.suggestions)}</p>
            <p><strong>Suggested reading:</strong> ${listText(analysis.readings)}</p>
        `;
    }

    function listText(items) {
        return items && items.length ? escapeHtml(items.join(", ")) : "None";
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function pad(value) {
        return String(value).padStart(3, "0");
    }

    function resetCounters() {
        ["countPassed", "countFailed", "countTotal"].forEach((id) => {
            el(id).textContent = "000";
            el(id).classList.remove("lit");
        });
    }

    function updateCounters(data) {
        el("countPassed").textContent = pad(data.passed || 0);
        el("countFailed").textContent = pad(data.failed || 0);
        el("countTotal").textContent = pad(data.total || 0);
        ["countPassed", "countFailed", "countTotal"].forEach((id) => el(id).classList.add("lit"));
    }

    // --- networking ---

    async function postForm(url, body) {
        return parseResponse(await fetch(url, { method: "POST", body }));
    }

    async function postJson(url, body) {
        return parseResponse(await fetch(url, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        }));
    }

    async function parseResponse(response) {
        let data;
        try {
            data = await response.json();
        } catch {
            throw new Error("Server returned an invalid response.");
        }
        if (!response.ok || data.success === false) throw new Error(data.error || "Request failed.");
        return data;
    }

    // --- status / busy state ---

    function setBusy(isBusy, text) {
        el("generate").disabled = isBusy;
        el("analyzeBtn").disabled = isBusy;
        el("run").disabled = isBusy || !state.testFile;
        if (isBusy) setStatus("busy", text);
    }

    function setActions(enabled) {
        el("copy").disabled = !enabled;
        el("download").disabled = !enabled;
        el("run").disabled = !enabled;
    }

    function setStatus(kind, message) {
        const chip = el("statusChip");
        chip.textContent = message;
        chip.dataset.state = kind;
    }

    function showAlert(message) {
        el("alert").textContent = message;
        el("alert").hidden = false;
    }

    function clearAlert() {
        el("alert").hidden = true;
        el("alert").textContent = "";
    }
})();
