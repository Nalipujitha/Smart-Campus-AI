/**
 * Dashboard & Analytics Visualizations
 * Chart.js configurations with resilient fallbacks
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle
  const mobileBtn = document.getElementById('mobileToggleBtn');
  const sidebar = document.getElementById('appSidebar');
  if (mobileBtn && sidebar) {
    mobileBtn.addEventListener('click', () => {
      sidebar.classList.toggle('show-mobile');
    });
  }

  // Initialize Dashboard Charts if data object exists
  if (typeof window.DASHBOARD_DATA !== 'undefined' && typeof Chart !== 'undefined') {
    initDashboardCharts(window.DASHBOARD_DATA);
  }
});

function initDashboardCharts(data) {
  // 1. Academic Performance (GPA Distribution)
  const gpaCtx = document.getElementById('gpaDistributionChart');
  if (gpaCtx && data.gpa_distribution) {
    const labels = Object.keys(data.gpa_distribution);
    const values = Object.values(data.gpa_distribution);
    new Chart(gpaCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Students Count',
          data: values,
          backgroundColor: '#3b82f6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 5 } }
        }
      }
    });
  }

  // 2. Attendance Distribution (Tiers)
  const attCtx = document.getElementById('attendanceDistributionChart');
  if (attCtx && data.attendance_distribution) {
    const labels = Object.keys(data.attendance_distribution);
    const values = Object.values(data.attendance_distribution);
    new Chart(attCtx, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // 3. Academic Risk Distribution
  const riskCtx = document.getElementById('riskDistributionChart');
  if (riskCtx && data.risk_distribution) {
    new Chart(riskCtx, {
      type: 'pie',
      data: {
        labels: ['Low Concern', 'Medium Concern', 'High Concern'],
        datasets: [{
          data: [
            data.risk_distribution['Low'] || 0,
            data.risk_distribution['Medium'] || 0,
            data.risk_distribution['High'] || 0
          ],
          backgroundColor: ['#10b981', '#f59e0b', '#ef4444']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // 4. Placement Readiness by Department
  const placCtx = document.getElementById('placementByDeptChart');
  if (placCtx && data.placement_by_dept && data.placement_by_dept.length > 0) {
    const labels = data.placement_by_dept.map(d => d.department.split(' ')[0]);
    const values = data.placement_by_dept.map(d => d.average_readiness);
    new Chart(placCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Avg Readiness %',
          data: values,
          backgroundColor: '#8b5cf6',
          borderRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100 }
        }
      }
    });
  }
}
