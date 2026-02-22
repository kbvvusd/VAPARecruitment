
// Recruitment Dashboard Application Logic

let dashboardData = {};
let currentSchool = null;
let currentProgram = null;
let activeClassificationFilter = null; // Track active classification filter

// DOM Elements
const schoolDropdown = document.getElementById('school-dropdown');
const contentAreaEl = document.getElementById('content-area');
const refreshBtn = document.getElementById('refresh-btn');
const exportBtn = document.getElementById('export-btn');

// --- Initialization ---

async function init() {
    console.log("Initializing Dashboard...");
    try {
        const response = await fetch('dashboard_data.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Handle new structure (with metadata) or fallback
        if (data.metadata && data.schools) {
            dashboardData = data.schools;
        } else {
            dashboardData = data;
        }

        populateDropdown();

        // Auto-select first school if available
        const schools = Object.keys(dashboardData).sort();
        if (schools.length > 0) {
            schoolDropdown.value = schools[0];
            selectSchool(schools[0]);
        }

    } catch (error) {
        console.error("Error loading data:", error);
        contentAreaEl.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-triangle-exclamation" style="color: var(--status-bad-text)"></i>
                <p>Failed to load dashboard data.</p>
                <p class="text-sm text-muted">${error.message}</p>
                <button onclick="location.reload()" class="btn btn-secondary mt-4">Retry</button>
            </div>
        `;
    }
}

// --- Dropdown Population ---

function populateDropdown() {
    const schools = Object.keys(dashboardData).sort();

    schools.forEach(school => {
        const option = document.createElement('option');
        option.value = school;
        option.textContent = school;
        schoolDropdown.appendChild(option);
    });
}

function selectSchool(schoolName) {
    if (!schoolName || !dashboardData[schoolName]) return;

    currentSchool = schoolName;

    // Determine default program (usually Band, or first available)
    const programs = Object.keys(dashboardData[schoolName]).sort();
    currentProgram = programs.includes('Band') ? 'Band' : programs[0];

    renderMainContent();
}

// --- Main Content Rendering ---

function renderMainContent() {
    if (!currentSchool) return;

    const schoolData = dashboardData[currentSchool];
    const programs = Object.keys(schoolData).sort();

    // Generate HTML
    let html = `
        <div class="dashboard-grid">
            
            <!-- Program Tabs -->
            <div class="card">
                <div class="card-header">
                    <div class="tabs">
                        ${programs.map(prog => `
                            <button 
                                class="tab-btn ${prog === currentProgram ? 'active' : ''}" 
                                onclick="switchProgram('${prog}')"
                            >
                                <i class="fa-solid ${prog === 'Band' ? 'fa-drum' : (prog === 'Choir' ? 'fa-microphone' : (prog === 'Dance' ? 'fa-shoe-prints' : 'fa-masks-theater'))}"></i> ${prog}
                            </button>
                        `).join('')}
                    </div>
                    
                    <div class="search-container">
                        <i class="fa-solid fa-search search-icon"></i>
                        <input type="text" id="student-search" class="search-input" placeholder="Search students..." onkeyup="filterTable()">
                    </div>
                </div>

                <div class="card-body">
                    <div class="filter-bar" style="margin-bottom: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                        <span style="font-weight: 500; color: var(--text-primary);">Filter by:</span>
                        <button class="filter-chip ${!activeClassificationFilter ? 'active' : ''}" onclick="setClassificationFilter(null)">
                            <i class="fa-solid fa-users"></i> All Students
                        </button>
                        <button class="filter-chip tag-status-green ${activeClassificationFilter === 'nerd' ? 'active' : ''}" onclick="setClassificationFilter('nerd')">
                            <i class="fa-solid fa-star"></i> Hardcore Nerds
                        </button>
                        <button class="filter-chip tag-status-yellow ${activeClassificationFilter === 'late' ? 'active' : ''}" onclick="setClassificationFilter('late')">
                            <i class="fa-solid fa-clock"></i> Late Starters
                        </button>
                        <button class="filter-chip tag-status-red ${activeClassificationFilter === 'withdrew' ? 'active' : ''}" onclick="setClassificationFilter('withdrew')">
                            <i class="fa-solid fa-door-open"></i> Withdrew
                        </button>
                    </div>
                    ${renderStudentTable(schoolData[currentProgram])}
                </div>
            </div>
        </div>
    `;

    contentAreaEl.innerHTML = html;
}

function switchProgram(programName) {
    currentProgram = programName;
    renderMainContent();
}

function renderStudentTable(programData) {
    if (!programData || !programData.students || programData.students.length === 0) {
        return `<div class="p-8 text-center text-muted">No student data available for this program.</div>`;
    }

    const students = programData.students;
    const years = programData.years; // List of year strings

    // Table Header
    let tableHtml = `
        <div class="data-table-wrapper">
        <table class="data-table" id="students-table">
            <thead>
                <tr>
                    <th>Student Name</th>
                    <th>ID</th>
                    <th style="width: 80px; text-align: center;">Yrs</th>
                    <th>Classification</th>
                    ${years.map(year => `<th class="cell-year ${year === '2025-2026' ? 'cell-current' : ''}">${year}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    // Table Rows
    students.forEach(student => {
        tableHtml += `<tr>`;


        tableHtml += `
            <td><div class="font-medium">${student.name}</div></td>
            <td class="text-muted font-mono text-xs">${student.id}</td>
            <td style="text-align: center; font-weight: 600;">${student.years_enrolled || 0}</td>
            <td>${renderClassification(student)}</td>
        `;

        // Years Data
        years.forEach(year => {
            const yearData = student.history[year];
            const currentClass = year === '2025-2026' ? 'cell-current' : '';

            if (!yearData || yearData.grade === 'N/A' || yearData.course === 'No Enrollment') {
                tableHtml += `<td class="cell-no-enrollment ${currentClass}">No Enrollment</td>`;
            } else {
                // Determine Grade Class
                let gradeClass = 'tag tag-grade';
                const g = String(yearData.grade);
                if (g.includes('6')) gradeClass = 'tag tag-grade-6';
                else if (g.includes('7')) gradeClass = 'tag tag-grade-7';
                else if (g.includes('8')) gradeClass = 'tag tag-grade-8';

                tableHtml += `
                    <td class="${currentClass}">
                        <span class="${gradeClass}">${yearData.grade}</span>
                        <span class="course-text">${yearData.course}</span>
                    </td>
                `;
            }
        });

        tableHtml += `</tr>`;
    });

    tableHtml += `
            </tbody>
        </table>
        </div>
    `;

    return tableHtml;
}

function renderClassification(student) {
    const classification = getClassification(student);
    if (!classification) return '';

    return `<span class="tag tag-status-${classification.color}">${classification.label}</span>`;
}

function getClassification(student) {
    // Determine projected current grade for 2025-2026
    let projectedGrade = null;
    const h25 = student.history['2025-2026'];
    const h24 = student.history['2024-2025'];
    const h23 = student.history['2023-2024'];

    if (h25 && h25.grade && h25.grade !== 'N/A') {
        projectedGrade = parseInt(h25.grade);
    } else if (h24 && h24.grade && h24.grade !== 'N/A') {
        projectedGrade = parseInt(h24.grade) + 1;
    } else if (h23 && h23.grade && h23.grade !== 'N/A') {
        projectedGrade = parseInt(h23.grade) + 2;
    }

    // Exclude if they "would" no longer be in middle school (6-8)
    if (!projectedGrade || projectedGrade < 6 || projectedGrade > 8) return null;

    // Get all enrolled grades
    const enrolledGrades = new Set();
    Object.values(student.history).forEach(h => {
        if (h.grade && h.grade !== 'N/A' && h.course !== 'No Enrollment') {
            const gradeNum = parseInt(h.grade);
            if (!isNaN(gradeNum)) enrolledGrades.add(gradeNum);
        }
    });

    const has6 = enrolledGrades.has(6);
    const has7 = enrolledGrades.has(7);
    const has8 = enrolledGrades.has(8);

    // Rule: If currently in 6th or 7th grade in 2025-2026, they haven't withdrawn yet
    const hist25 = student.history['2025-2026'];
    const isCurrently6or7 = hist25 && (String(hist25.grade) === '6' || String(hist25.grade) === '7') && hist25.course !== 'No Enrollment';

    const nerdLabel = currentProgram === 'Choir' ? 'hardcore choir nerd' : (currentProgram === 'Dance' ? 'hardcore dance nerd' : (currentProgram === 'Theatre' ? 'hardcore theatre nerd' : 'hardcore band nerd'));

    if (currentSchool === "Lakeside Middle School") {
        if (has7 && has8) return { label: nerdLabel, color: 'green' };
        if (has8 && !has7 && !has6) return { label: 'late starter', color: 'yellow' };
        if (!isCurrently6or7 && (has6 || has7) && !has8) return { label: 'withdrew', color: 'red' };
    } else {
        if (has6 && has7 && has8) return { label: nerdLabel, color: 'green' };
        if (has8) return { label: 'late starter', color: 'yellow' };
        if (!isCurrently6or7 && (has6 || has7) && !has8) return { label: 'withdrew', color: 'red' };
    }

    return null;
}

// --- Interaction ---

function setClassificationFilter(filterType) {
    activeClassificationFilter = filterType;
    renderMainContent();
    // Apply filter after DOM updates
    setTimeout(() => filterTable(), 0);
}

function filterTable() {
    const input = document.getElementById('student-search');
    const filter = input.value.toUpperCase();
    const table = document.getElementById('students-table');
    if (!table) return;

    const tr = table.getElementsByTagName('tr');

    // Loop through all table rows, and hide those who don't match the search query
    // Start from 1 to skip header
    for (let i = 1; i < tr.length; i++) {
        // Search Name (col 0) and ID (col 1)
        const nameTd = tr[i].getElementsByTagName('td')[0];
        const idTd = tr[i].getElementsByTagName('td')[1];
        const classificationTd = tr[i].getElementsByTagName('td')[3]; // Classification column

        if (nameTd || idTd) {
            const nameTxt = nameTd.textContent || nameTd.innerText;
            const idTxt = idTd.textContent || idTd.innerText;

            // Check search filter
            const matchesSearch = !filter ||
                nameTxt.toUpperCase().indexOf(filter) > -1 ||
                idTxt.toUpperCase().indexOf(filter) > -1;

            // Check classification filter
            let matchesClassification = true;
            if (activeClassificationFilter) {
                const classificationTxt = classificationTd ? (classificationTd.textContent || classificationTd.innerText).toLowerCase() : '';

                if (activeClassificationFilter === 'nerd') {
                    matchesClassification = classificationTxt.includes('hardcore') || classificationTxt.includes('nerd');
                } else if (activeClassificationFilter === 'late') {
                    matchesClassification = classificationTxt.includes('late starter');
                } else if (activeClassificationFilter === 'withdrew') {
                    matchesClassification = classificationTxt.includes('withdrew');
                }
            }

            // Show row only if it matches both filters
            if (matchesSearch && matchesClassification) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}

// --- Utils ---

refreshBtn.addEventListener('click', () => {
    location.reload();
});

// Start
document.addEventListener('DOMContentLoaded', init);
