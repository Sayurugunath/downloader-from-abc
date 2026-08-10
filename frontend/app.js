// ==========================================
// DOWNLOADER FROM ABC
// ==========================================

let refreshTimer = null;
let lastDownloadStates = new Map();

const SETTINGS_KEY = "downly.settings";
const DEFAULT_SETTINGS = {
    defaultQuality: "auto",
    defaultAudio: "M4A",
    rememberQuality: true,
    notifications: true,
    showSpeedEta: true,
    theme: "system",
};

let settings = loadSettings();


function loadSettings() {
    try {
        return {
            ...DEFAULT_SETTINGS,
            ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}"),
        };
    } catch {
        return { ...DEFAULT_SETTINGS };
    }
}


function saveSettings() {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}


function applyTheme() {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.dataset.theme =
        settings.theme === "system"
            ? (prefersDark ? "dark" : "light")
            : settings.theme;
}


function preferredQuality() {
    if (settings.rememberQuality) {
        const lastQuality = localStorage.getItem("downly.lastQuality");
        if (lastQuality) return lastQuality;
    }
    return settings.defaultQuality;
}


function showToast(message) {
    if (!settings.notifications) return;
    const toast = document.getElementById("notificationToast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.add("is-visible");
    clearTimeout(showToast.timeout);
    showToast.timeout = setTimeout(() => toast.classList.remove("is-visible"), 3600);
}


async function loadServerSettings() {
    try {
        const response = await fetch("/api/settings", { cache: "no-store" });
        const serverSettings = await response.json();
        const toggle = document.getElementById("autoCleanupSetting");
        if (toggle) toggle.checked = serverSettings.auto_cleanup;
    } catch (error) {
        console.error("Unable to load server settings:", error);
    }
}


async function saveAutoCleanup(enabled) {
    try {
        const response = await fetch("/api/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ auto_cleanup: enabled }),
        });
        if (!response.ok) throw new Error("Unable to save cleanup setting.");
    } catch (error) {
        console.error(error);
        showToast("Could not save automatic cleanup preference.");
        await loadServerSettings();
    }
}


function openSettings() {
    const panel = document.getElementById("settingsPanel");
    if (!panel) return;
    panel.hidden = false;
    document.body.classList.add("settings-open");
    document.getElementById("closeSettingsButton").focus();
}


function closeSettings() {
    const panel = document.getElementById("settingsPanel");
    if (!panel) return;
    panel.hidden = true;
    document.body.classList.remove("settings-open");
    document.getElementById("settingsButton").focus();
}


function initializeSettings() {
    const fieldMap = {
        defaultQualitySetting: "defaultQuality",
        defaultAudioSetting: "defaultAudio",
        rememberQualitySetting: "rememberQuality",
        notificationsSetting: "notifications",
        speedEtaSetting: "showSpeedEta",
        themeSetting: "theme",
    };

    for (const [elementId, settingKey] of Object.entries(fieldMap)) {
        const element = document.getElementById(elementId);
        if (!element) continue;
        element.type === "checkbox"
            ? (element.checked = settings[settingKey])
            : (element.value = settings[settingKey]);
        element.addEventListener("change", () => {
            settings[settingKey] = element.type === "checkbox" ? element.checked : element.value;
            saveSettings();
            if (settingKey === "theme") applyTheme();
            if (window.currentVideo) {
                renderQualities(window.currentVideo.qualities || []);
                renderAudio(window.currentVideo.audio || []);
            }
            if (settingKey === "showSpeedEta") refreshDownloads();
        });
    }

    document.getElementById("settingsButton").addEventListener("click", openSettings);
    document.getElementById("closeSettingsButton").addEventListener("click", closeSettings);
    document.getElementById("settingsPanel").addEventListener("click", event => {
        if (event.target.id === "settingsPanel") closeSettings();
    });
    document.getElementById("autoCleanupSetting").addEventListener("change", event => {
        saveAutoCleanup(event.target.checked);
    });
    document.addEventListener("keydown", event => {
        if (event.key === "Escape" && !document.getElementById("settingsPanel").hidden) closeSettings();
    });

    applyTheme();
    loadServerSettings();
}


// ==========================================
// SERVER STATUS
// ==========================================

function setServerStatus(isOnline) {

    const indicator =
        document.getElementById(
            "serverStatus"
        );

    const text =
        document.getElementById(
            "serverStatusText"
        );


    if (!indicator || !text) {
        return;
    }


    indicator.classList.toggle(
        "is-online",
        isOnline
    );

    indicator.classList.toggle(
        "is-offline",
        !isOnline
    );

    indicator.classList.remove(
        "is-checking"
    );

    text.textContent = isOnline
        ? "Server: Online"
        : "Server: Offline";
}


// ==========================================
// ANALYZE
// ==========================================

async function analyze() {

    const url =
        document.getElementById("url")
            .value.trim();

    const button =
        document.getElementById(
            "analyzeButton"
        );

    const status =
        document.getElementById(
            "status"
        );

    const result =
        document.getElementById(
            "result"
        );


    if (!url) {

        status.textContent =
            "Paste a video URL first.";

        return;
    }


    button.disabled = true;

    status.textContent =
        "Analyzing...";

    result.style.display =
        "none";


    try {

        const response =
            await fetch(
                "/api/analyze",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        url: url
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to analyze this URL."
            );
        }


        const video =
            data.data;


        document.getElementById(
            "thumbnail"
        ).src =
            video.thumbnail || "";


        document.getElementById(
            "title"
        ).textContent =
            video.title ||
            "Unknown title";


        document.getElementById(
            "uploader"
        ).textContent =
            video.uploader ||
            "Unknown";


        document.getElementById(
            "duration"
        ).textContent =
            formatDuration(
                video.duration
            );


        // Store current video data
        window.currentVideo = {
            url: url,
            title: video.title,
            thumbnail: video.thumbnail,
            qualities: video.qualities || [],
            audio: video.audio || [],
        };


        renderQualities(
            video.qualities || []
        );


        renderAudio(
            video.audio || []
        );


        result.style.display =
            "block";


        status.textContent =
            "";


    } catch (error) {

        console.error(error);

        status.textContent =
            "Error: " +
            error.message;


    } finally {

        button.disabled =
            false;

    }
}


// ==========================================
// VIDEO FORMATS
// ==========================================

function renderQualities(
    qualities
) {

    const container =
        document.getElementById(
            "qualities"
        );


    container.innerHTML =
        "";


    for (
        const item of qualities
    ) {

        const card =
            document.createElement(
                "div"
            );


        card.className =
            "format-card";

        const isPreferred =
            preferredQuality() !== "auto" &&
            item.quality === preferredQuality();

        if (isPreferred) card.classList.add("is-preferred");


        card.innerHTML = `

            <div class="format-top">

                <div class="quality">
                    ${escapeHtml(
                        item.quality
                    )}
                </div>

                <div class="format-badge">
                    ${escapeHtml(
                        item.format
                    )}
                </div>

            </div>

            <div class="format-size">
                ${escapeHtml(
                    item.size ||
                    "Size unknown"
                )}
            </div>

            ${isPreferred ? '<div class="format-preference">Preferred</div>' : ""}

            <button
                class="download-button"
                type="button"
            >
                DOWNLOAD
            </button>

        `;


        const button =
            card.querySelector(
                ".download-button"
            );


        button.addEventListener(
            "click",
            () => {

                startDownload(
                    item.selector,
                    button,
                    item.quality
                );

            }
        );


        container.appendChild(
            card
        );
    }
}


// ==========================================
// AUDIO
// ==========================================

function renderAudio(
    audio
) {

    const container =
        document.getElementById(
            "audio"
        );


    container.innerHTML =
        "";


    for (
        const item of audio
    ) {

        const card =
            document.createElement(
                "div"
            );


        card.className =
            "format-card";

        const isPreferred = item.format === settings.defaultAudio;

        if (isPreferred) card.classList.add("is-preferred");


        card.innerHTML = `

            <div class="format-top">

                <div class="quality">
                    Audio
                </div>

                <div class="format-badge">
                    ${escapeHtml(
                        item.format
                    )}
                </div>

            </div>

            <div class="format-size">
                ${escapeHtml(
                    item.size ||
                    "Size unknown"
                )}
            </div>

            ${isPreferred ? '<div class="format-preference">Preferred</div>' : ""}

            <button
                class="download-button"
                type="button"
            >
                DOWNLOAD
            </button>

        `;


        const button =
            card.querySelector(
                ".download-button"
            );


        button.addEventListener(
            "click",
            () => {

                startDownload(
                    item.format_id,
                    button,
                    null
                );

            }
        );


        container.appendChild(
            card
        );
    }
}


// ==========================================
// START DOWNLOAD
// ==========================================

async function startDownload(
    formatId,
    sourceButton,
    quality = null
) {

    const video =
        window.currentVideo;


    if (!video) {

        alert(
            "Analyze a video first."
        );

        return;
    }


    sourceButton.disabled =
        true;

    sourceButton.textContent =
        "STARTING...";

    if (quality && settings.rememberQuality) {
        localStorage.setItem("downly.lastQuality", quality);
    }


    try {

        const response =
            await fetch(
                "/api/download",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        url:
                            video.url,

                        format_id:
                            formatId,

                        title:
                            video.title,

                        thumbnail:
                            video.thumbnail

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Unable to start download."
            );
        }


        sourceButton.textContent =
            "ADDED";


        await refreshDownloads();


        setTimeout(() => {

            sourceButton.disabled =
                false;

            sourceButton.textContent =
                "DOWNLOAD";

        }, 800);


    } catch (error) {

        console.error(error);

        sourceButton.disabled =
            false;

        sourceButton.textContent =
            "RETRY";

        alert(
            error.message
        );
    }
}


// ==========================================
// DOWNLOAD MANAGER
// ==========================================

async function refreshDownloads() {

    try {

        const response =
            await fetch(
                "/api/downloads",
                {
                    cache: "no-store"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {
            setServerStatus(false);
            return;
        }


        setServerStatus(true);

        for (const job of data.downloads || []) {
            const previousStatus = lastDownloadStates.get(job.job_id);
            if (previousStatus && previousStatus !== job.status) {
                if (job.status === "completed") showToast(`Download complete: ${job.title || "Your file"}`);
                if (job.status === "error") showToast(`Download failed: ${job.title || "Your file"}`);
            }
            lastDownloadStates.set(job.job_id, job.status);
        }


        renderDownloads(
            data.downloads || []
        );


    } catch (error) {

        setServerStatus(false);

        console.error(
            "Download manager:",
            error
        );
    }
}


// ==========================================
// RENDER DOWNLOADS
// ==========================================

function renderDownloads(
    downloads
) {

    const container =
        document.getElementById(
            "downloads"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        "";


    if (!downloads.length) {

        container.innerHTML = `

            <div class="empty-downloads">

                <div class="empty-icon">
                    ↓
                </div>

                <div>
                    No downloads yet
                </div>

                <span>
                    Your downloads will appear here.
                </span>

            </div>

        `;

        return;
    }


    for (
        const job of downloads
    ) {

        container.appendChild(
            createDownloadCard(job)
        );
    }
}


// ==========================================
// DOWNLOAD CARD
// ==========================================

function createDownloadCard(
    job
) {

    const card =
        document.createElement(
            "div"
        );


    card.className =
        "download-manager-card";


    const progress =
        Number(
            job.progress || 0
        );


    let statusText =
        "Queued";


    if (
        job.status ===
        "downloading"
    ) {

        statusText =
            "Downloading";
    }

    else if (
        job.status ===
        "paused"
    ) {

        statusText =
            "Paused";
    }

    else if (
        job.status ===
        "processing"
    ) {

        statusText =
            "Processing";
    }

    else if (
        job.status ===
        "completed"
    ) {

        statusText =
            "Complete";
    }

    else if (
        job.status ===
        "cancelled"
    ) {

        statusText =
            "Cancelled";
    }

    else if (
        job.status ===
        "error"
    ) {

        statusText =
            "Failed";
    }


    const downloaded =
        formatBytes(
            job.downloaded
        );


    const total =
        formatBytes(
            job.total
        );


    const speed =
        formatSpeed(
            job.speed
        );


    const eta =
        formatETA(
            job.eta
        );


    card.innerHTML = `

        <div class="manager-top">

            ${
                job.thumbnail
                ? `
                    <img
                        class="manager-thumbnail"
                        src="${escapeHtml(
                            job.thumbnail
                        )}"
                        alt=""
                    >
                `
                : `
                    <div
                        class="
                            manager-thumbnail
                            thumbnail-placeholder
                        "
                    >
                        U
                    </div>
                `
            }


            <div class="manager-info">

                <div class="manager-title">
                    ${escapeHtml(
                        job.title ||
                        "Download"
                    )}
                </div>

                <div class="manager-meta">

                    ${statusText}

                    ${
                        job.format_id
                        ? " • " +
                          escapeHtml(
                              job.format_id
                          )
                        : ""
                    }

                </div>

            </div>


            <div class="
                manager-status
                status-${escapeHtml(
                    job.status
                )}
            ">

                ${statusText}

            </div>

        </div>


        <div class="manager-progress">

            <div
                class="manager-progress-fill"
                style="
                    width:${progress}%;
                "
            ></div>

        </div>


        <div class="manager-bottom">

            <div class="manager-stats">

                <span>
                    ${progress.toFixed(1)}%
                </span>


                ${
                    job.total
                    ? `
                        <span>
                            ${downloaded}
                            /
                            ${total}
                        </span>
                    `
                    : ""
                }


                ${
                    settings.showSpeedEta &&
                    job.status ===
                    "downloading"
                    ? `
                        <span>
                            ${speed}
                        </span>

                        <span>
                            ETA ${eta}
                        </span>
                    `
                    : ""
                }

            </div>


            <div class="manager-actions">

                ${getManagerAction(job)}

            </div>

        </div>

    `;


    return card;
}


// ==========================================
// ACTIONS
// ==========================================

function getManagerAction(
    job
) {

    if (
        job.status ===
        "downloading"
    ) {

        return `

            <button
                class="
                    manager-button
                    pause
                "
                onclick="
                    pauseDownload(
                        '${job.job_id}'
                    )
                "
            >
                PAUSE
            </button>

            <button
                class="
                    manager-button
                    cancel
                "
                onclick="
                    cancelDownload(
                        '${job.job_id}'
                    )
                "
            >
                CANCEL
            </button>

        `;
    }


    if (
        job.status ===
        "paused"
    ) {

        return `

            <button
                class="
                    manager-button
                    primary
                "
                onclick="
                    resumeDownload(
                        '${job.job_id}'
                    )
                "
            >
                RESUME
            </button>

            <button
                class="
                    manager-button
                    cancel
                "
                onclick="
                    cancelDownload(
                        '${job.job_id}'
                    )
                "
            >
                DELETE
            </button>

        `;
    }


    if (
        job.status ===
        "queued"
    ) {

        return `

            <button
                class="
                    manager-button
                    cancel
                "
                onclick="
                    cancelDownload(
                        '${job.job_id}'
                    )
                "
            >
                CANCEL
            </button>

        `;
    }


    if (
        job.status ===
        "processing"
    ) {

        return `
            <span class="processing-label">
                Processing...
            </span>
        `;
    }


    if (
        job.status ===
        "completed"
    ) {

        return `

            <button
                class="
                    manager-button
                    primary
                "
                onclick="
                    downloadCompleted(
                        '${job.job_id}'
                    )
                "
            >
                DOWNLOAD FILE
            </button>

        `;
    }


    if (
        job.status ===
        "error" ||
        job.status ===
        "cancelled"
    ) {

        return `

            <button
                class="
                    manager-button
                    primary
                "
                onclick="
                    retryDownload(
                        '${job.job_id}'
                    )
                "
            >
                RETRY
            </button>

        `;
    }


    return "";
}


// ==========================================
// PAUSE
// ==========================================

async function pauseDownload(
    jobId
) {

    try {

        await fetch(
            `/api/pause/${jobId}`,
            {
                method: "POST"
            }
        );


        await refreshDownloads();


    } catch (error) {

        console.error(error);

    }
}


// ==========================================
// RESUME
// ==========================================

async function resumeDownload(
    jobId
) {

    try {

        await fetch(
            `/api/resume/${jobId}`,
            {
                method: "POST"
            }
        );


        await refreshDownloads();


    } catch (error) {

        console.error(error);

    }
}


// ==========================================
// CANCEL
// ==========================================

async function cancelDownload(
    jobId
) {

    try {

        await fetch(
            `/api/cancel/${jobId}`,
            {
                method: "POST"
            }
        );


        await refreshDownloads();


    } catch (error) {

        console.error(error);

    }
}


// ==========================================
// RETRY
// ==========================================

async function retryDownload(
    jobId
) {

    try {

        const response =
            await fetch(
                `/api/retry/${jobId}`,
                {
                    method: "POST"
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Retry failed."
            );
        }


        await refreshDownloads();


    } catch (error) {

        alert(
            error.message
        );
    }
}


// ==========================================
// COMPLETED FILE
// ==========================================

function downloadCompleted(
    jobId
) {

    const link =
        document.createElement(
            "a"
        );


    link.href =
        `/api/file/${jobId}`;


    link.download =
        "";


    document.body.appendChild(
        link
    );


    link.click();

    link.remove();
}


// ==========================================
// CLEAR HISTORY
// ==========================================

async function clearHistory() {

    if (
        !confirm(
            "Clear completed, cancelled and failed downloads?"
        )
    ) {

        return;
    }


    try {

        await fetch(
            "/api/downloads",
            {
                method: "DELETE"
            }
        );


        await refreshDownloads();


    } catch (error) {

        console.error(error);

    }
}


// ==========================================
// FILE SIZE
// ==========================================

function formatBytes(
    bytes
) {

    if (
        bytes === null ||
        bytes === undefined ||
        bytes <= 0
    ) {

        return "—";
    }


    const units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ];


    let value =
        Number(bytes);


    let index = 0;


    while (
        value >= 1024 &&
        index <
        units.length - 1
    ) {

        value /=
            1024;

        index++;
    }


    return (
        value.toFixed(
            value >= 100
                ? 0
                : 1
        ) +
        " " +
        units[index]
    );
}


// ==========================================
// SPEED
// ==========================================

function formatSpeed(
    speed
) {

    if (
        !speed ||
        speed <= 0
    ) {

        return "—";
    }


    return (
        formatBytes(speed) +
        "/s"
    );
}


// ==========================================
// ETA
// ==========================================

function formatETA(
    seconds
) {

    if (
        seconds === null ||
        seconds === undefined
    ) {

        return "—";
    }


    seconds =
        Number(seconds);


    if (
        !Number.isFinite(
            seconds
        )
    ) {

        return "—";
    }


    const minutes =
        Math.floor(
            seconds / 60
        );


    const remaining =
        Math.floor(
            seconds % 60
        );


    if (
        minutes > 59
    ) {

        const hours =
            Math.floor(
                minutes / 60
            );


        const mins =
            minutes % 60;


        return (
            `${hours}h ${mins}m`
        );
    }


    return (
        `${minutes}:` +
        `${String(
            remaining
        ).padStart(
            2,
            "0"
        )}`
    );
}


// ==========================================
// DURATION
// ==========================================

function formatDuration(
    seconds
) {

    if (!seconds) {
        return "";
    }


    seconds =
        Math.floor(
            Number(seconds)
        );


    const hours =
        Math.floor(
            seconds / 3600
        );


    const minutes =
        Math.floor(
            (seconds % 3600) / 60
        );


    const remaining =
        seconds % 60;


    if (
        hours > 0
    ) {

        return (
            `${hours}:` +
            `${String(
                minutes
            ).padStart(
                2,
                "0"
            )}:` +
            `${String(
                remaining
            ).padStart(
                2,
                "0"
            )}`
        );
    }


    return (
        `${minutes}:` +
        `${String(
            remaining
        ).padStart(
            2,
            "0"
        )}`
    );
}


// ==========================================
// ESCAPE HTML
// ==========================================

function escapeHtml(
    value
) {

    const element =
        document.createElement(
            "div"
        );


    element.textContent =
        String(
            value ?? ""
        );


    return element.innerHTML;
}


// ==========================================
// INITIALIZE
// ==========================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        initializeSettings();

        const input =
            document.getElementById(
                "url"
            );


        if (input) {

            input.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key ===
                        "Enter"
                    ) {

                        event.preventDefault();

                        analyze();

                    }

                }
            );
        }


        refreshDownloads();


        refreshTimer =
            setInterval(
                refreshDownloads,
                1000
            );

    }
);
