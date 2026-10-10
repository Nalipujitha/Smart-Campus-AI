/**
 * Learning Assistant & Task Completion Toggle
 */

async function toggleLearningTask(taskId, isChecked) {
  try {
    const res = await fetch(`/learning/task/${taskId}/toggle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `is_completed=${isChecked ? '1' : '0'}`
    });
    const data = await res.json();
    if (data.success) {
      const progEl = document.getElementById(`plan-progress-${data.task.plan_id}`);
      const progBar = document.getElementById(`plan-bar-${data.task.plan_id}`);
      if (progEl) progEl.innerText = `${data.plan_progress}%`;
      if (progBar) progBar.style.width = `${data.plan_progress}%`;
    }
  } catch (err) {
    console.error('Error toggling task:', err);
  }
}
