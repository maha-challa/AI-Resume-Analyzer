/* ==========================================================================
   AI Resume Analyzer - Client-side Interactive Logic & MySQL History
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements - Upload & Form
    const dropZone = document.getElementById("dropZone");
    const fileInput = document.getElementById("resumeFileInput");
    const browseBtn = document.getElementById("browseBtn");
    const fileSelectedCard = document.getElementById("fileSelectedCard");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileSize = document.getElementById("selectedFileSize");
    const removeFileBtn = document.getElementById("removeFileBtn");

    const jdTextarea = document.getElementById("jobDescriptionInput");
    const jdWordCount = document.getElementById("jdWordCount");
    const sampleJdBtn = document.getElementById("sampleJdBtn");

    const form = document.getElementById("resumeForm");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const loadingIndicator = document.getElementById("loadingIndicator");
    const errorAlert = document.getElementById("errorAlert");
    const errorMessage = document.getElementById("errorMessage");

    // Results DOM Elements
    const resultsContainer = document.getElementById("resultsContainer");
    const scoreCircle = document.getElementById("scoreCircle");
    const scoreValue = document.getElementById("scoreValue");
    const matchLevelBadge = document.getElementById("matchLevelBadge");
    const matchedCount = document.getElementById("matchedCount");
    const missingCount = document.getElementById("missingCount");
    const matchedSkillsList = document.getElementById("matchedSkillsList");
    const missingSkillsList = document.getElementById("missingSkillsList");
    const suggestionsList = document.getElementById("suggestionsList");
    const extractedTextBox = document.getElementById("extractedTextBox");
    const dbSaveNotice = document.getElementById("dbSaveNotice");

    // History DOM Elements
    const dbStatusPill = document.getElementById("dbStatusPill");
    const refreshHistoryBtn = document.getElementById("refreshHistoryBtn");
    const historyTableBody = document.getElementById("historyTableBody");

    // Modal DOM Elements
    const historyModalEl = document.getElementById("historyDetailModal");
    let historyModal = null;
    if (historyModalEl && window.bootstrap) {
        historyModal = new bootstrap.Modal(historyModalEl);
    }
    const modalFileName = document.getElementById("modalFileName");
    const modalDate = document.getElementById("modalDate");
    const modalScore = document.getElementById("modalScore");
    const modalMatchedSkills = document.getElementById("modalMatchedSkills");
    const modalMissingSkills = document.getElementById("modalMissingSkills");
    const modalSuggestions = document.getElementById("modalSuggestions");
    const modalJobDescription = document.getElementById("modalJobDescription");

    // 1. File Upload Interaction
    browseBtn.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("click", (e) => {
        if (e.target !== browseBtn) {
            fileInput.click();
        }
    });

    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove("dragover");
        }, false);
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            handleSelectedFile(files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    function handleSelectedFile(file) {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            showError("Only PDF files (.pdf) are allowed. Please select a valid PDF.");
            fileInput.value = "";
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            showError("The selected file is larger than the 16 MB limit.");
            fileInput.value = "";
            return;
        }

        hideError();
        selectedFileName.textContent = file.name;
        selectedFileSize.textContent = formatBytes(file.size);

        fileSelectedCard.classList.remove("d-none");
        fileSelectedCard.classList.add("d-flex");
    }

    removeFileBtn.addEventListener("click", () => {
        fileInput.value = "";
        fileSelectedCard.classList.remove("d-flex");
        fileSelectedCard.classList.add("d-none");
    });

    function formatBytes(bytes, decimals = 1) {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ["Bytes", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
    }

    // 2. Job Description Word Count & Sample
    function updateWordCount() {
        const text = jdTextarea.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        jdWordCount.textContent = `${words} word${words === 1 ? '' : 's'}`;
    }

    jdTextarea.addEventListener("input", updateWordCount);
    updateWordCount();

    sampleJdBtn.addEventListener("click", () => {
        jdTextarea.value = `We are looking for an experienced Full-Stack Python Developer to join our core engineering team.

Key Responsibilities & Required Skills:
- Strong hands-on experience with Python and web frameworks such as Flask or Django.
- Solid front-end skills in HTML, CSS, Bootstrap, and modern JavaScript (ES6+). Experience with React is a major plus.
- Proficient in relational databases, specifically MySQL and PostgreSQL, including writing optimized SQL queries.
- Experience building and consuming scalable REST APIs.
- Familiarity with Git version control, Docker containerization, and basic CI/CD workflows.
- Understanding of Agile/Scrum development methodologies.`;
        updateWordCount();
        hideError();
    });

    // 3. Form Submission via AJAX (Fetch API)
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        if (!fileInput.files || fileInput.files.length === 0) {
            showError("Please select or upload a PDF resume before analyzing.");
            return;
        }

        if (!jdTextarea.value.trim()) {
            showError("Please enter or paste a target job description.");
            return;
        }

        hideError();
        setLoading(true);

        const formData = new FormData(form);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json"
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                showError(data.error || "An error occurred during resume analysis.");
                setLoading(false);
                return;
            }

            renderResults(data.data);
            setLoading(false);

            // Reload history to include the new saved record
            loadHistory();

            resultsContainer.scrollIntoView({ behavior: "smooth", block: "start" });

        } catch (err) {
            console.error("Analysis request failed:", err);
            showError("Network connection error. Please verify your server is running and try again.");
            setLoading(false);
        }
    });

    // 4. Render Results Function
    function renderResults(res) {
        resultsContainer.classList.remove("d-none");

        const percentage = res.match_percentage;
        scoreValue.textContent = `${percentage}%`;

        let strokeColor = "#0284c7";
        if (percentage >= 80) strokeColor = "#10b981";
        else if (percentage >= 50) strokeColor = "#f59e0b";
        else strokeColor = "#ef4444";

        scoreCircle.style.background = `conic-gradient(${strokeColor} 0% ${percentage}%, #e2e8f0 ${percentage}% 100%)`;

        matchLevelBadge.className = `badge bg-${res.match_color}-subtle text-${res.match_color} px-3 py-2 rounded-pill fw-bold fs-6`;
        matchLevelBadge.textContent = res.match_level;

        // DB Status notice
        if (res.saved_to_db) {
            dbSaveNotice.innerHTML = `<span class="text-success"><i class="bi bi-database-check me-1"></i>Saved to MySQL Database (Record #${res.record_id})</span>`;
        } else if (res.db_error) {
            dbSaveNotice.innerHTML = `<span class="text-warning"><i class="bi bi-database-exclamation me-1"></i>Analysis completed (MySQL save pending setup: ${escapeHtml(res.db_error)})</span>`;
        } else {
            dbSaveNotice.innerHTML = "";
        }

        // Matched Skills
        matchedCount.textContent = `${res.matched_skills.length} found`;
        matchedSkillsList.innerHTML = "";
        if (res.matched_skills.length > 0) {
            res.matched_skills.forEach(skill => {
                const badge = document.createElement("span");
                badge.className = "badge badge-matched px-3 py-2 rounded-pill";
                badge.innerHTML = `<i class="bi bi-check2 me-1"></i>${escapeHtml(skill)}`;
                matchedSkillsList.appendChild(badge);
            });
        } else {
            matchedSkillsList.innerHTML = `<span class="text-muted fst-italic small">No matching skills detected from the job description requirements.</span>`;
        }

        // Missing Skills
        missingCount.textContent = `${res.missing_skills.length} missing`;
        missingSkillsList.innerHTML = "";
        if (res.missing_skills.length > 0) {
            res.missing_skills.forEach(skill => {
                const badge = document.createElement("span");
                badge.className = "badge badge-missing px-3 py-2 rounded-pill";
                badge.innerHTML = `<i class="bi bi-plus-circle me-1"></i>${escapeHtml(skill)}`;
                missingSkillsList.appendChild(badge);
            });
        } else {
            missingSkillsList.innerHTML = `<span class="text-success fw-semibold small"><i class="bi bi-stars me-1"></i>Great news! No required skills are missing.</span>`;
        }

        // Suggestions
        suggestionsList.innerHTML = "";
        if (res.suggestions && res.suggestions.length > 0) {
            res.suggestions.forEach(suggestion => {
                const li = document.createElement("li");
                li.className = "suggestion-item p-3 rounded-3 bg-light border-start border-4 border-primary";
                li.innerHTML = `<i class="bi bi-arrow-right-short text-primary fs-5 me-1 align-middle"></i><span>${escapeHtml(suggestion)}</span>`;
                suggestionsList.appendChild(li);
            });
        }

        extractedTextBox.textContent = res.full_resume_text || "No text available.";
    }

    // 5. Database Status & History Functions
    async function checkDbStatus() {
        try {
            const res = await fetch("/db-status");
            const data = await res.json();
            if (data.connected) {
                dbStatusPill.className = "badge bg-success-subtle text-success border border-success-subtle px-3 py-2 rounded-pill small";
                dbStatusPill.innerHTML = `<i class="bi bi-database-check me-1"></i>MySQL Connected`;
            } else {
                dbStatusPill.className = "badge bg-warning-subtle text-warning-emphasis border border-warning-subtle px-3 py-2 rounded-pill small";
                dbStatusPill.innerHTML = `<i class="bi bi-database-exclamation me-1"></i>MySQL Disconnected`;
                dbStatusPill.title = data.message;
            }
        } catch (e) {
            dbStatusPill.className = "badge bg-danger-subtle text-danger border border-danger-subtle px-3 py-2 rounded-pill small";
            dbStatusPill.innerHTML = `<i class="bi bi-database-x me-1"></i>Offline`;
        }
    }

    async function loadHistory() {
        historyTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4 text-muted">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status"></div>
                    Loading records from MySQL...
                </td>
            </tr>
        `;

        try {
            const res = await fetch("/history");
            const data = await res.json();

            if (!res.ok || !data.success) {
                historyTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">
                            <i class="bi bi-info-circle me-1 text-warning"></i>
                            ${escapeHtml(data.error || "Unable to load database history.")}
                        </td>
                    </tr>
                `;
                return;
            }

            const records = data.analyses;
            if (!records || records.length === 0) {
                historyTableBody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-4 text-muted">
                            <i class="bi bi-inbox fs-4 d-block mb-1 text-secondary"></i>
                            No analysis records found yet. Upload and analyze a resume to save your first record!
                        </td>
                    </tr>
                `;
                return;
            }

            historyTableBody.innerHTML = "";
            records.forEach(row => {
                const tr = document.createElement("tr");

                let scoreBadgeClass = "bg-primary";
                if (row.skill_match_percentage >= 80) scoreBadgeClass = "bg-success";
                else if (row.skill_match_percentage >= 50) scoreBadgeClass = "bg-warning text-dark";
                else scoreBadgeClass = "bg-danger";

                tr.innerHTML = `
                    <td class="ps-4">
                        <div class="d-flex align-items-center gap-2">
                            <i class="bi bi-file-earmark-pdf text-danger fs-5"></i>
                            <span class="fw-semibold text-dark">${escapeHtml(row.resume_filename)}</span>
                        </div>
                    </td>
                    <td class="text-muted small">${escapeHtml(row.formatted_date || "N/A")}</td>
                    <td>
                        <span class="badge ${scoreBadgeClass} rounded-pill px-3 py-1">
                            ${row.skill_match_percentage}%
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-success-subtle text-success rounded-pill px-2 py-1 small">
                            ${row.matched_skills.length} matched
                        </span>
                    </td>
                    <td>
                        <span class="badge bg-danger-subtle text-danger rounded-pill px-2 py-1 small">
                            ${row.missing_skills.length} missing
                        </span>
                    </td>
                    <td class="text-end pe-4">
                        <button type="button" class="btn btn-sm btn-outline-primary rounded-pill px-3 view-detail-btn" data-id="${row.id}">
                            <i class="bi bi-eye me-1"></i>View
                        </button>
                    </td>
                `;

                tr.querySelector(".view-detail-btn").addEventListener("click", () => {
                    openHistoryDetail(row.id);
                });

                historyTableBody.appendChild(tr);
            });

        } catch (err) {
            console.error("Failed to load history:", err);
            historyTableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-4 text-muted">
                        <i class="bi bi-exclamation-triangle text-danger me-1"></i>
                        Could not connect to MySQL server. Please ensure database credentials are configured.
                    </td>
                </tr>
            `;
        }
    }

    async function openHistoryDetail(id) {
        try {
            const res = await fetch(`/history/${id}`);
            const data = await res.json();
            if (!data.success || !data.analysis) {
                alert("Failed to load analysis details.");
                return;
            }

            const item = data.analysis;
            modalFileName.textContent = item.resume_filename;
            modalDate.textContent = item.formatted_date;
            modalScore.textContent = `${item.skill_match_percentage}% Match`;

            // Matched skills
            modalMatchedSkills.innerHTML = "";
            if (item.matched_skills && item.matched_skills.length > 0) {
                item.matched_skills.forEach(s => {
                    const sp = document.createElement("span");
                    sp.className = "badge badge-matched px-3 py-2 rounded-pill";
                    sp.innerHTML = `<i class="bi bi-check2 me-1"></i>${escapeHtml(s)}`;
                    modalMatchedSkills.appendChild(sp);
                });
            } else {
                modalMatchedSkills.innerHTML = "<span class='text-muted small'>None</span>";
            }

            // Missing skills
            modalMissingSkills.innerHTML = "";
            if (item.missing_skills && item.missing_skills.length > 0) {
                item.missing_skills.forEach(s => {
                    const sp = document.createElement("span");
                    sp.className = "badge badge-missing px-3 py-2 rounded-pill";
                    sp.innerHTML = `<i class="bi bi-plus-circle me-1"></i>${escapeHtml(s)}`;
                    modalMissingSkills.appendChild(sp);
                });
            } else {
                modalMissingSkills.innerHTML = "<span class='text-success small'>No missing skills!</span>";
            }

            // Suggestions
            modalSuggestions.innerHTML = "";
            if (item.improvement_suggestions && item.improvement_suggestions.length > 0) {
                item.improvement_suggestions.forEach(s => {
                    const li = document.createElement("li");
                    li.className = "p-2 rounded bg-light border-start border-3 border-primary";
                    li.textContent = s;
                    modalSuggestions.appendChild(li);
                });
            }

            modalJobDescription.textContent = item.job_description || "N/A";

            if (!historyModal && window.bootstrap) {
                historyModal = new bootstrap.Modal(historyModalEl);
            }
            if (historyModal) {
                historyModal.show();
            }

        } catch (e) {
            console.error("Failed to fetch detail:", e);
        }
    }

    refreshHistoryBtn.addEventListener("click", () => {
        checkDbStatus();
        loadHistory();
    });

    // Helper functions
    function setLoading(isLoading) {
        if (isLoading) {
            analyzeBtn.disabled = true;
            analyzeBtn.classList.add("d-none");
            loadingIndicator.classList.remove("d-none");
        } else {
            analyzeBtn.disabled = false;
            analyzeBtn.classList.remove("d-none");
            loadingIndicator.classList.add("d-none");
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorAlert.classList.remove("d-none");
        errorAlert.classList.add("show");
        errorAlert.scrollIntoView({ behavior: "smooth", block: "center" });
    }

    function hideError() {
        errorAlert.classList.add("d-none");
        errorAlert.classList.remove("show");
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    }

    // Initial load
    checkDbStatus();
    loadHistory();
});
