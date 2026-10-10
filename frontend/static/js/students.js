/**
 * Student Management Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('studentSearchInput');
  const deptSelect = document.getElementById('studentDeptFilter');
  const statusSelect = document.getElementById('studentStatusFilter');

  // Debounced live filter
  let debounceTimeout;
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(() => {
        applyStudentFilters();
      }, 400);
    });
  }

  if (deptSelect) deptSelect.addEventListener('change', applyStudentFilters);
  if (statusSelect) statusSelect.addEventListener('change', applyStudentFilters);
});

function applyStudentFilters() {
  const form = document.getElementById('studentFilterForm');
  if (form) {
    form.submit();
  }
}

function confirmStudentDelete(studentId, studentName) {
  return confirm(`Are you sure you want to permanently delete student record for ${studentName} (${studentId})? This action cannot be undone.`);
}
