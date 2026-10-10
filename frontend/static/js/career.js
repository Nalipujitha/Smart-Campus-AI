/**
 * Career Guidance & Skill Tag Selection
 */

function addSkillTag(skillName) {
  const input = document.getElementById('careerSkillsInput');
  if (!input) return;

  const current = input.value.split(',').map(s => s.trim()).filter(Boolean);
  if (!current.includes(skillName)) {
    current.push(skillName);
    input.value = current.join(', ');
  }
}
