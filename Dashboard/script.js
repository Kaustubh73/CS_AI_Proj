let currentAnomalyScoreThreshold = 0.90;
let currentRequestRateThreshold = 100;

function loadThresholdsFromStorage() {
    const storedAnomalyScoreThreshold = localStorage.getItem('anomalyScoreThreshold');
    const storedRequestRateThreshold = localStorage.getItem('requestRateThreshold');

    if (storedAnomalyScoreThreshold) {
        currentAnomalyScoreThreshold = parseFloat(storedAnomalyScoreThreshold);
    }

    if (storedRequestRateThreshold) {
        currentRequestRateThreshold = parseInt(storedRequestRateThreshold);
    }
}

function saveThresholdsToStorage() {
    localStorage.setItem('anomalyScoreThreshold', currentAnomalyScoreThreshold);
    localStorage.setItem('requestRateThreshold', currentRequestRateThreshold);
}

let currentTab = 'dashboard';
let requestRateChart, anomalyScoreChart;
let sampleData = [];

async function fetchAndUpdateData() {
    try {
        const file = 'results.csv';
        sampleData = await readCSV(file);
        updateRequestRateChart(currentRequestRateThreshold);
        updateAnomalyScoreChart();
        updateModelPerformanceTable();
        updateRecentAlertsTable(currentAnomalyScoreThreshold);
    } catch (error) {
        console.error('Error fetching and updating data:', error);
    }
}

async function readCSV(file) {
    const response = await fetch(file);
    const csvText = await response.text();
    return parseCSV(csvText);
}

function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    
    return lines.slice(1).map(line => {
        const [
            Method, URL, Cookie, ContentLen, Payload, ReqLen, ArgLen, NumArgs, NumDigitsArgs, 
            PathLen, NumLettersArgs, NumLettersPath, NumSpecialCharsPath, MaxByteValReq, 
            Content_present, IP, timestamp, predicted_class, target_class, predicted_prob
        ] = line.split(',');

        const features = {
            Method: parseInt(Method.trim(), 10),
            URL: URL.trim(),
            Cookie: Cookie.trim(),
            ContentLen: parseInt(ContentLen.trim(), 10),
            Payload: Payload.trim(),
            ReqLen: parseInt(ReqLen.trim(), 10),
            ArgLen: parseInt(ArgLen.trim(), 10),
            NumArgs: parseInt(NumArgs.trim(), 10),
            NumDigitsArgs: parseInt(NumDigitsArgs.trim(), 10),
            PathLen: parseInt(PathLen.trim(), 10),
            NumLettersArgs: parseInt(NumLettersArgs.trim(), 10),
            NumLettersPath: parseInt(NumLettersPath.trim(), 10),
            NumSpecialCharsPath: parseInt(NumSpecialCharsPath.trim(), 10),
            MaxByteValReq: parseInt(MaxByteValReq.trim(), 10),
            Content_present: parseInt(Content_present.trim(), 10),
            IP: IP.trim(),
        };

        return {
            timestamp: timestamp.trim(),
            features: features,
            predictedClass: parseInt(predicted_class.trim(), 10),
            actualClass: parseInt(target_class.trim(), 10),
            predictedProb: parseFloat(predicted_prob.trim())
        };
    });
}

function displayTab(tab) {
    document.querySelectorAll('main > div').forEach(content => content.classList.add('hidden'));
    document.getElementById(tab).classList.remove('hidden');
    currentTab = tab;
}

document.getElementById('dashboardTab').addEventListener('click', () => displayTab('dashboard'));
document.getElementById('configurationTab').addEventListener('click', () => displayTab('configuration'));
document.getElementById('usersTab').addEventListener('click', () => displayTab('users'));
document.getElementById('auditLogTab').addEventListener('click', () => displayTab('auditLog'));

function updateRequestRateChart(requestRateThreshold) {
    const ctx = document.getElementById('requestRateChart').getContext('2d');
    
    sampleData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    const firstTimestamp = new Date(sampleData[0].timestamp);
    const lastTimestamp = new Date(sampleData[sampleData.length - 1].timestamp);

    const startTime = new Date(firstTimestamp.getTime() - 3 * 60000);
    const endTime = new Date(lastTimestamp.getTime() + 3 * 60000);
    const timeIntervals = [];
    for (let time = startTime; time <= endTime; time.setMinutes(time.getMinutes() + 1)) {
        timeIntervals.push(new Date(time));
    }
    const attackCounts = timeIntervals.map(interval => {
        const endInterval = new Date(interval.getTime() + 60000);
        return sampleData.filter(item => {
            const timestamp = new Date(item.timestamp);
            return timestamp >= interval && timestamp < endInterval;
        }).length;
    });

    if (requestRateChart) {
        requestRateChart.data.labels = timeIntervals.map(interval => formatTime(interval));
        requestRateChart.data.datasets[0].data = attackCounts;

        requestRateChart.options.plugins.beforeDraw = function (chart) {
            const ctx = chart.ctx;
            const yScale = chart.scales['y'];
            const yPos = yScale.getPixelForValue(requestRateThreshold);

            ctx.save();
            ctx.strokeStyle = 'red';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(chart.chartArea.left, yPos);
            ctx.lineTo(chart.chartArea.right, yPos);
            ctx.stroke();
            ctx.restore();
        };

        requestRateChart.update();
    } else {
        requestRateChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: timeIntervals.map(interval => formatTime(interval)),
                datasets: [
                    {
                        label: 'Request Rate (GET or POST Requests per Minute)',
                        data: attackCounts,
                        borderColor: '#007bff',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    beforeDraw: function (chart) {
                        const ctx = chart.ctx;
                        const yScale = chart.scales['y'];
                        const yPos = yScale.getPixelForValue(requestRateThreshold);

                        ctx.save();
                        ctx.strokeStyle = 'red';
                        ctx.lineWidth = 2;
                        ctx.setLineDash([5, 5]);
                        ctx.beginPath();
                        ctx.moveTo(chart.chartArea.left, yPos);
                        ctx.lineTo(chart.chartArea.right, yPos);
                        ctx.stroke();
                        ctx.restore();
                    }
                }
            }
        });
    }
}

function formatTime(date) {
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
}

function getISTTimestamp() {
    const now = new Date();

    const utcTime = now.getTime();
    const istOffset = 5.5 * 60 * 60 * 1000;
    const istTime = new Date(utcTime + istOffset);
    return istTime.toISOString().slice(0, 19).replace('T', ' ');
}

function updateAnomalyScoreChart() {
    const ctx = document.getElementById('anomalyScoreChart').getContext('2d');

    const normalData = sampleData.filter(item => item.predictedClass === 0);
    const anomalousData = sampleData.filter(item => item.predictedClass === 1);

    const correctNormal = normalData.filter(item => item.actualClass === 0).length;
    const incorrectNormal = normalData.filter(item => item.actualClass === 1).length;

    const correctAnomalous = anomalousData.filter(item => item.actualClass === 1).length;
    const incorrectAnomalous = anomalousData.filter(item => item.actualClass === 0).length;

    if (anomalyScoreChart) {
        anomalyScoreChart.data.datasets[0].data = [correctNormal, correctAnomalous];
        anomalyScoreChart.data.datasets[1].data = [incorrectNormal, incorrectAnomalous];
        anomalyScoreChart.update();
    } else {
        anomalyScoreChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Normal', 'Anomalous'],
                datasets: [
                    {
                        label: 'Correct Predictions',
                        data: [correctNormal, correctAnomalous],
                        backgroundColor: ['#28a745', '#28a745'],
                        borderColor: ['#28a745', '#28a745'],
                        borderWidth: 1
                    },
                    {
                        label: 'Incorrect Predictions',
                        data: [incorrectNormal, incorrectAnomalous],
                        backgroundColor: ['#dc3545', '#dc3545'],
                        borderColor: ['#dc3545', '#dc3545'],
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: false,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

function updateRecentAlertsTable(anomalyScoreThreshold) {
    const tableBody = document.getElementById('recentAlertsTable').getElementsByTagName('tbody')[0];
    tableBody.innerHTML = '';

    const filteredData = sampleData.filter(item => item.predictedClass === 1 && item.predictedProb >= anomalyScoreThreshold).slice(-5).reverse();

    filteredData.forEach(item => {
        const timestamp = item.timestamp;
        const actualClass = item.actualClass;
        const predictedClass = item.predictedClass;
        const predictedProb = item.predictedProb;
        const { Method, Payload } = item.features;
        const method = Method === 1 ? 'POST' : 'GET';
        const status = actualClass === 1 ? 'Detected' : 'False Positive';
        const statusClass = actualClass === 1 ? 'positive' : 'false-positive';

        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${method}</td>
            <td class="payload" data-full-payload="${Payload}">${Payload.slice(0, 20)}...</td>
            <td>${(predictedProb * 100).toFixed(2)}%</td>
            <td class="${statusClass}">${status}</td>
        `;
        tableBody.appendChild(row);
    });
}

function addAuditLogEntry(event, details) {
    const timestamp = getISTTimestamp();
    const table = document.getElementById('auditLogTable');
    let tableBody = table.querySelector('tbody');
    if (!tableBody) {
        tableBody = document.createElement('tbody');
        table.appendChild(tableBody);
    }

    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${timestamp}</td>
      <td>${event}</td>
      <td>${details}</td>
    `;
    tableBody.appendChild(row);
}

function updateAlertThresholdForm() {
    const form = document.getElementById('alertThresholdForm');
    form.innerHTML = '';

    const anomalyScoreThresholdInput = document.createElement('div');
    anomalyScoreThresholdInput.innerHTML = `
      <label for="anomalyScoreThreshold">Anomaly Score Threshold</label>
      <input type="number" id="anomalyScoreThreshold" name="anomalyScoreThreshold" step="0.01" value="0.90" required>
    `;

    const requestRateThresholdInput = document.createElement('div');
    requestRateThresholdInput.innerHTML = `
      <label for="requestRateThreshold">Request Rate Threshold</label>
      <input type="number" id="requestRateThreshold" name="requestRateThreshold" step="10" value="100" required>
    `;

    const submitButton = document.createElement('button');
    submitButton.type = 'submit';
    submitButton.textContent = 'Save Thresholds';

    form.appendChild(anomalyScoreThresholdInput);
    form.appendChild(requestRateThresholdInput);
    form.appendChild(submitButton);

    form.addEventListener('submit', handleAlertThresholdSave);
}

function handleAlertThresholdSave(event) {
    event.preventDefault();
    const form = event.target;
    currentAnomalyScoreThreshold = parseFloat(form.querySelector('#anomalyScoreThreshold').value);
    currentRequestRateThreshold = parseInt(form.querySelector('#requestRateThreshold').value);

    saveThresholdsToStorage();
    updateRecentAlertsTable(currentAnomalyScoreThreshold);
    updateRequestRateChart(currentRequestRateThreshold);
    addAuditLogEntry('Configuration', `Admin Changed Alert Thresholds`);
}

function updateUsersTable() {
    const table = document.getElementById('usersTable');
    table.innerHTML = '';
    const users = [
        { id: 1, username: 'admin', role: 'Admin' },
        { id: 2, username: 'user1', role: 'User' }
    ];
    users.forEach(user => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.role}</td>
        `;
        table.appendChild(tr);
    });
}

function updateModelPerformanceTable() {
    const table = document.getElementById('modelPerformanceTable');
    table.innerHTML = '';

    const truePositives = sampleData.filter(item => item.predictedClass === 1 && item.actualClass === 1).length;
    const falsePositives = sampleData.filter(item => item.predictedClass === 1 && item.actualClass === 0).length;
    const trueNegatives = sampleData.filter(item => item.predictedClass === 0 && item.actualClass === 0).length;
    const falseNegatives = sampleData.filter(item => item.predictedClass === 0 && item.actualClass === 1).length;

    const accuracy = (truePositives + trueNegatives) / sampleData.length;
    const precision = truePositives / (truePositives + falsePositives);
    const recall = truePositives / (truePositives + falseNegatives);
    const f1Score = 2 * ((precision * recall) / (precision + recall));

    const rows = [
        { name: 'Accuracy', value: accuracy * 100 },
        { name: 'Precision', value: precision * 100 },
        { name: 'Recall', value: recall * 100 },
        { name: 'F1-Score', value: f1Score * 100 }
    ];

    rows.forEach(row => {
        const tr = document.createElement('tr');
        const tdMetric = document.createElement('td');
        tdMetric.textContent = row.name;
        const tdValue = document.createElement('td');

        const barContainer = document.createElement('div');
        barContainer.className = 'bar-container';
        const bar = document.createElement('div');
        bar.className = 'bar';
        bar.style.width = `${row.value}%`;
        bar.style.backgroundColor = getBarColor(row.value);
        bar.textContent = `${row.value.toFixed(2)}%`;
        barContainer.appendChild(bar);
        tdValue.appendChild(barContainer);

        tr.appendChild(tdMetric);
        tr.appendChild(tdValue);
        table.appendChild(tr);
    });
}

function getBarColor(value) {
    if (value < 25) return '#FF0000';
    if (value < 50) return '#FFA500';
    if (value < 75) return '#0000FF';
    return '#00FF00';
}

async function initializeDashboard() {
    loadThresholdsFromStorage();
    updateAlertThresholdForm();
    updateUsersTable();

    await fetchAndUpdateData();
    setInterval(async () => {
        try {
            if (currentTab === 'dashboard') {
                await fetchAndUpdateData();
            }
        } catch (error) {
            console.error('Error in periodic update:', error);
        }
    }, 3000);
}

document.addEventListener("DOMContentLoaded", function () {
    const loginOverlay = document.getElementById('login-overlay');
    const mainContent = document.getElementById('main-content');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const logoutButton = document.getElementById('logoutButton');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');

    const validCredentials = [
        { id: 1, username: 'admin', password: 'admin', role: 'Admin' },
        { id: 2, username: 'user1', password: 'user1', role: 'User1' }
    ];

    function centerLoginOverlay() {
        loginOverlay.style.position = 'fixed';
        loginOverlay.style.top = '50%';
        loginOverlay.style.left = '50%';
        loginOverlay.style.transform = 'translate(-50%, -50%)';
    }

    function clearLoginError() {
        loginError.textContent = '';
    }

    function isUserLoggedIn() {
        return localStorage.getItem('isLoggedIn') === 'true';
    }

    function showLogin() {
        centerLoginOverlay();
        loginOverlay.style.display = 'flex';
        mainContent.classList.add('blurred');
        clearLoginError();
    }

    function hideLogin() {
        loginOverlay.style.display = 'none';
        mainContent.classList.remove('blurred');
    }

    async function initializeAfterLogin() {
        if (!isUserLoggedIn()) return;
        hideLogin();
        initializeDashboard();
    }

    loginForm.addEventListener('submit', function (e) {
        e.preventDefault();
        const username = usernameInput.value;
        const password = passwordInput.value;

        clearLoginError();

        const validUser = validCredentials.find(
            cred => cred.username === username && cred.password === password
        );

        if (validUser) {
            localStorage.setItem('isLoggedIn', 'true');
            addAuditLogEntry('Login', `${validUser.role} Logged In`);
            initializeAfterLogin();
        } else {
            loginError.textContent = 'Invalid credentials. Please try again.';
        }

        usernameInput.value = '';
        passwordInput.value = '';
    });

    logoutButton.addEventListener('click', () => {
        localStorage.setItem('isLoggedIn', 'false');
        showLogin();
    });

    if (isUserLoggedIn()) {
        initializeAfterLogin();
    } else {
        showLogin();
    }
});
