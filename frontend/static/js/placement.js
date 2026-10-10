/**
 * Placement Prep Practice Interactions
 */

function selectOption(optionValue, btnElement, groupName) {
  const hiddenInput = document.getElementById(`selected_answer_${groupName}`);
  if (hiddenInput) {
    hiddenInput.value = optionValue;
  }
  const allBtns = document.querySelectorAll(`.opt-btn-${groupName}`);
  allBtns.forEach(b => {
    b.classList.remove('btn-primary');
    b.classList.add('btn-secondary');
  });
  btnElement.classList.remove('btn-secondary');
  btnElement.classList.add('btn-primary');
}
