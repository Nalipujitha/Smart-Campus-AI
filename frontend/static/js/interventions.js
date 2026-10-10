/**
 * Faculty Mentoring & Intervention Case Interactions
 */

function openEditInterventionModal(id, title, status, priority, followUp, outcome, actionItems) {
  const form = document.getElementById('updateInterventionForm');
  if (!form) return;

  form.action = `/interventions/${id}/update`;
  document.getElementById('editInterventionTitle').innerText = title;
  document.getElementById('editStatusSelect').value = status;
  document.getElementById('editPrioritySelect').value = priority;
  document.getElementById('editFollowUpDate').value = followUp || '';
  document.getElementById('editActionItems').value = actionItems || '';
  document.getElementById('editOutcomeNotes').value = outcome || '';

  const modal = document.getElementById('interventionModal');
  if (modal) {
    modal.style.display = 'block';
  }
}

function closeInterventionModal() {
  const modal = document.getElementById('interventionModal');
  if (modal) {
    modal.style.display = 'none';
  }
}
