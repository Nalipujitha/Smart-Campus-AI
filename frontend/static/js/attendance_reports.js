/**
 * Attendance Reports & Department Chart Visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
  if (typeof window.ATTENDANCE_SUMMARY !== 'undefined' && typeof Chart !== 'undefined') {
    initAttendanceReports(window.ATTENDANCE_SUMMARY);
  }
});

function initAttendanceReports(summary) {
  const deptCtx = document.getElementById('deptAttendanceChart');
  if (deptCtx && summary.department_breakdown) {
    const labels = summary.department_breakdown.map(d => d.department.split(' ')[0]);
    const values = summary.department_breakdown.map(d => d.percentage);

    new Chart(deptCtx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Average Attendance %',
          data: values,
          backgroundColor: '#0d9488',
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
