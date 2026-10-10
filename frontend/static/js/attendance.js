/**
 * Attendance Session Recording & Roster Dynamic Fetching
 */

document.addEventListener('DOMContentLoaded', () => {
  const deptSelect = document.getElementById('sessionDeptSelect');
  const semSelect = document.getElementById('sessionSemSelect');
  const fetchRosterBtn = document.getElementById('fetchRosterBtn');
  const markAllPresentBtn = document.getElementById('markAllPresentBtn');
  const markAllAbsentBtn = document.getElementById('markAllAbsentBtn');

  if (fetchRosterBtn) {
    fetchRosterBtn.addEventListener('click', loadClassRoster);
  }

  if (markAllPresentBtn) {
    markAllPresentBtn.addEventListener('click', () => setAllAttendance('Present'));
  }

  if (markAllAbsentBtn) {
    markAllAbsentBtn.addEventListener('click', () => setAllAttendance('Absent'));
  }
});

async function loadClassRoster() {
  const dept = document.getElementById('sessionDeptSelect').value;
  const sem = document.getElementById('sessionSemSelect').value;
  const rosterBody = document.getElementById('rosterTableBody');
  const rosterContainer = document.getElementById('rosterContainer');

  if (!dept || !sem) {
    alert('Please select both Department and Semester to fetch the roster.');
    return;
  }

  rosterBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">Loading class roster...</td></tr>';
  rosterContainer.style.display = 'block';

  try {
    const res = await fetch(`/attendance/roster?department=${encodeURIComponent(dept)}&semester=${encodeURIComponent(sem)}`);
    const students = await res.json();

    if (!students || students.length === 0) {
      rosterBody.innerHTML = '<tr><td colspan="4" class="text-center py-4 text-muted">No active students found in this department and semester.</td></tr>';
      return;
    }

    let html = '';
    students.forEach((stu, idx) => {
      html += `
        <tr>
          <td><strong>${stu.student_id}</strong></td>
          <td>${stu.first_name} ${stu.last_name}</td>
          <td>
            <div style="display: flex; gap: 1rem;">
              <label style="display: flex; align-items: center; gap: 0.3rem; cursor: pointer;">
                <input type="radio" name="status_${stu.student_id}" value="Present" checked>
                <span class="badge badge-success">Present</span>
              </label>
              <label style="display: flex; align-items: center; gap: 0.3rem; cursor: pointer;">
                <input type="radio" name="status_${stu.student_id}" value="Absent">
                <span class="badge badge-danger">Absent</span>
              </label>
              <label style="display: flex; align-items: center; gap: 0.3rem; cursor: pointer;">
                <input type="radio" name="status_${stu.student_id}" value="On Leave">
                <span class="badge badge-warning">On Leave</span>
              </label>
            </div>
          </td>
          <td>
            <input type="text" name="remarks_${stu.student_id}" class="form-control form-control-sm" placeholder="Optional notes" style="min-width: 140px;">
          </td>
        </tr>
      `;
    });

    rosterBody.innerHTML = html;
  } catch (err) {
    rosterBody.innerHTML = `<tr><td colspan="4" class="text-center text-danger py-4">Failed to load roster: ${err.message}</td></tr>`;
  }
}

function setAllAttendance(status) {
  const radios = document.querySelectorAll(`input[type="radio"][value="${status}"]`);
  radios.forEach(r => { r.checked = true; });
}
