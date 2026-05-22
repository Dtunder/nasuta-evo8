const variables = [
    "Sanitation", "Production", "Education", "Quality of Life",
    "Population Growth", "Environment", "Population", "Politics",
    "Round", "AP Points"
];

let chart;

function init() {
    initIndicators();
    initChart();
    
    document.getElementById('run-btn').addEventListener('click', runSimulation);
    
    // Slider labels update
    document.getElementById('stability-slider').addEventListener('input', (e) => {
        e.target.nextElementSibling.textContent = e.target.value + '%';
    });
    document.getElementById('humanity-slider').addEventListener('input', (e) => {
        e.target.nextElementSibling.textContent = e.target.value > 0 ? 'ON' : 'OFF';
    });
}

function initIndicators() {
    const container = document.getElementById('indicators');
    container.innerHTML = '';
    
    variables.forEach((name, i) => {
        const div = document.createElement('div');
        div.className = 'indicator';
        div.innerHTML = `
            <div class="ind-container">
                <svg class="circ-svg">
                    <circle class="circ-bg" cx="30" cy="30" r="26"></circle>
                    <circle class="circ-val" id="circ-${i}" cx="30" cy="30" r="26" stroke-dasharray="0 163.36"></circle>
                </svg>
                <div class="ind-value" id="val-${i}">0</div>
            </div>
            <div class="ind-label">${name.toUpperCase()}</div>
        `;
        container.appendChild(div);
    });
}

function updateIndicators(values) {
    // values is array of 10 numbers
    const maxes = [29, 29, 29, 29, 29, 29, 48, 37, 30, 36];
    values.forEach((v, i) => {
        const percent = Math.min(100, (v / maxes[i]) * 100);
        const circle = document.getElementById(`circ-${i}`);
        const valText = document.getElementById(`val-${i}`);
        
        const circumference = 2 * Math.PI * 26;
        const offset = (percent / 100) * circumference;
        circle.style.strokeDasharray = `${offset} ${circumference}`;
        valText.textContent = Math.round(v);
        
        // Color coding
        if (i < 8) {
            if (v < 5 || v > 25) circle.style.stroke = "var(--danger)";
            else if (v < 10 || v > 20) circle.style.stroke = "#f6ad55";
            else circle.style.stroke = "var(--accent-blue)";
        }
    });
}

function initChart() {
    const ctx = document.getElementById('main-chart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({length: 31}, (_, i) => i),
            datasets: [
                {
                    label: 'Sovereign MCTS (Stability)',
                    data: [],
                    borderColor: '#00d2ff',
                    backgroundColor: 'rgba(0, 210, 255, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Paper MCTS (Stability)',
                    data: [],
                    borderColor: '#94a3b8',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

async function runSimulation() {
    const btn = document.getElementById('run-btn');
    const prompt = document.getElementById('prompt-input').value;
    const stability = document.getElementById('stability-slider').value;
    const humanity = document.getElementById('humanity-slider').value > 0;
    
    btn.disabled = true;
    btn.textContent = "THINKING...";
    document.getElementById('system-status').textContent = "SOVEREIGN_COMPUTING";
    
    addLogLine("INITIATING JULES SOVEREIGN ENGINE...", "sys");
    addLogLine(`PROMPT_PARSED: "${prompt || 'NONE'}"`, "sys");
    
    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                stability_bias: stability / 100,
                sovereign_mode: humanity
            })
        });
        
        const data = await response.json();
        
        // Playback trajectory
        playTrajectory(data.trajectory, data.paper_trajectory, data.logs);
        
    } catch (err) {
        addLogLine("CRITICAL_ERROR: " + err.message, "err");
    } finally {
        btn.disabled = false;
        btn.textContent = "INITIALIZE SIMULATION";
    }
}

function addLogLine(text, type = "") {
    const log = document.getElementById('log-terminal');
    const div = document.createElement('div');
    div.className = 'line ' + type;
    div.textContent = `> ${text}`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
}

function playTrajectory(traj, paperTraj, logs) {
    let step = 0;
    const interval = setInterval(() => {
        if (step >= traj.length) {
            clearInterval(interval);
            document.getElementById('system-status').textContent = "SOVEREIGN_STABLE";
            addLogLine("SIMULATION_COMPLETE. EQUILIBRIUM REACHED.", "sys");
            return;
        }
        
        const state = traj[step];
        updateIndicators(state);
        
        // Update Chart
        chart.data.datasets[0].data = traj.slice(0, step + 1).map(s => calculateStability(s));
        if (paperTraj) {
            chart.data.datasets[1].data = paperTraj.slice(0, step + 1).map(s => calculateStability(s));
        }
        chart.update('none');
        
        // Add log if exists for this step
        if (logs && logs[step]) {
            logs[step].forEach(l => addLogLine(l));
        }
        
        step++;
    }, 200);
}

function calculateStability(V) {
    // Simple stability metric: 30 - range of variables
    const core = V.slice(0, 8);
    const range = Math.max(...core) - Math.min(...core);
    return Math.max(0, 30 - range);
}

document.addEventListener('DOMContentLoaded', init);
