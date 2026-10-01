// A native select emits change only when its value changes. Chromium also emits
// a zero-detail click when the user confirms an option in its picker, including
// the already-selected option. Ignore that click when change handled a new item.
export function onSelectIncludingRepeat(select, onSelect) {
  let changed = false;
  let resetTimer;
  select.addEventListener('change', () => {
    changed = true;
    clearTimeout(resetTimer);
    resetTimer = setTimeout(() => { changed = false; }, 0);
    onSelect(select.value);
  });
  select.addEventListener('click', (event) => {
    if (event.detail !== 0) return;
    if (!changed) onSelect(select.value);
    changed = false;
  });
}
