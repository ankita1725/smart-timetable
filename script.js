/* =========================================================
   1. EDITABLE TIMETABLE — primary feature
   ========================================================= */

const form = document.getElementById("entry-form");
const formHeading = document.getElementById("form-heading");
const entryIdField = document.getElementById("entry-id");
const subjectField = document.getElementById("subject");
const teacherField = document.getElementById("teacher");
const dayField = document.getElementById("day");
const startField = document.getElementById("start_time");
const endField = document.getElementById("end_time");
const notesField = document.getElementById("notes");
const submitBtn = document.getElementById("submit-btn");
const cancelEditBtn = document.getElementById("cancel-edit-btn");
const formError = document.getElementById("form-error");

const entriesBody = document.getElementById("entries-body");
const emptyNote = document.getElementById("empty-note");

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function clearError() {
  formError.hidden = true;
  formError.textContent = "";
}

function resetForm() {
  form.reset();
  entryIdField.value = "";
  formHeading.textContent = "Add a class";
  submitBtn.textContent = "Add class";
  cancelEditBtn.hidden = true;
  clearError();
}

function startEdit(entry) {
  entryIdField.value = entry.id;
  subjectField.value = entry.subject;
  teacherField.value = entry.teacher;
  dayField.value = entry.day;
  startField.value = entry.start_time;
  endField.value = entry.end_time;
  notesField.value = entry.notes;

  formHeading.textContent = "Edit class";
  submitBtn.textContent = "Save changes";
  cancelEditBtn.hidden = false;
  clearError();
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function formatTime12h(t) {
  // "14:30" -> "2:30 PM"
  const [h, m] = t.split(":").map(Number);
  const period = h >= 12 ? "PM" : "AM";
  const hour12 = h % 12 === 0 ? 12 : h % 12;
  return `${hour12}:${String(m).padStart(2, "0")} ${period}`;
}

async function loadEntries() {
  const res = await fetch("/api/entries");
  const data = await res.json();
  renderEntries(data.entries || []);
}

function renderEntries(entries) {
  entriesBody.innerHTML = "";

  if (entries.length === 0) {
    emptyNote.hidden = false;
    return;
  }
  emptyNote.hidden = true;

  entries.forEach((entry) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="slot-col">${entry.day}</td>
      <td>${formatTime12h(entry.start_time)}–${formatTime12h(entry.end_time)}</td>
      <td class="subject-col">${escapeHtml(entry.subject)}</td>
      <td>${escapeHtml(entry.teacher)}</td>
      <td>${escapeHtml(entry.notes)}</td>
      <td class="row-actions">
        <button class="edit-btn" data-id="${entry.id}">Edit</button>
        <button class="delete-btn" data-id="${entry.id}">Delete</button>
      </td>
    `;
    entriesBody.appendChild(tr);
  });

  entriesBody.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const entry = entries.find((e) => e.id === Number(btn.dataset.id));
      if (entry) startEdit(entry);
    });
  });

  entriesBody.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", () => handleDelete(Number(btn.dataset.id)));
  });
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

async function handleDelete(id) {
  if (!confirm("Delete this class from your timetable?")) return;
  await fetch(`/api/entries/${id}`, { method: "DELETE" });
  if (Number(entryIdField.value) === id) resetForm();
  loadEntries();
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  clearError();

  const payload = {
    subject: subjectField.value.trim(),
    teacher: teacherField.value.trim(),
    day: dayField.value,
    start_time: startField.value,
    end_time: endField.value,
    notes: notesField.value.trim(),
  };

  const editingId = entryIdField.value;
  const url = editingId ? `/api/entries/${editingId}` : "/api/entries";
  const method = editingId ? "PUT" : "POST";

  submitBtn.disabled = true;
  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) {
      let message = data.error || "Something went wrong.";
      if (data.conflicts && data.conflicts.length) {
        const c = data.conflicts[0];
        message += ` (clashes with ${c.subject}, ${formatTime12h(c.start_time)}–${formatTime12h(c.end_time)})`;
      }
      showError(message);
      return;
    }

    resetForm();
    loadEntries();
  } catch (err) {
    showError("Couldn't reach the server. Is app.py running?");
    console.error(err);
  } finally {
    submitBtn.disabled = false;
  }
});

cancelEditBtn.addEventListener("click", resetForm);

loadEntries();

/* =========================================================
   2. OPTIONAL SAMPLE GENERATOR — old feature, tucked away
   ========================================================= */

const toggleGeneratorBtn = document.getElementById("toggle-generator");
const generatorBody = document.getElementById("generator-body");
const generateBtn = document.getElementById("generate-btn");
const statusLine = document.getElementById("status-line");
const tabsEl = document.getElementById("tabs");
const genGridWrap = document.getElementById("gen-grid-wrap");
const genGridBody = document.getElementById("gen-grid-body");
const failureEl = document.getElementById("failure");

let currentGenData = null;
let activeSection = null;
let generatorLoadedOnce = false;

toggleGeneratorBtn.addEventListener("click", () => {
  const isHidden = generatorBody.hidden;
  generatorBody.hidden = !isHidden;
  toggleGeneratorBtn.setAttribute("aria-expanded", String(isHidden));
  toggleGeneratorBtn.textContent = toggleGeneratorBtn.textContent.replace(
    isHidden ? "▾" : "▸",
    isHidden ? "▸" : "▾"
  );
});

async function runGenerator() {
  generateBtn.disabled = true;
  generateBtn.textContent = "Generating…";
  statusLine.className = "status-line";
  statusLine.textContent = "Running the scheduler…";
  failureEl.hidden = true;
  genGridWrap.hidden = true;
  tabsEl.hidden = true;

  try {
    const res = await fetch("/api/generate");
    if (!res.ok) throw new Error(`Server responded ${res.status}`);
    const data = await res.json();
    currentGenData = data;

    if (!data.success) {
      statusLine.className = "status-line fail";
      statusLine.textContent = `No valid timetable — ${data.total_placed}/${data.total_required} classes placed before getting stuck.`;
      failureEl.hidden = false;
      return;
    }

    statusLine.className = "status-line ok";
    statusLine.textContent = `Generated in ${data.generated_in_ms} ms — all ${data.total_placed} classes placed with no conflicts.`;

    renderTabs(data.sections);
    activeSection = data.sections[0];
    renderGenGrid();
  } catch (err) {
    statusLine.className = "status-line fail";
    statusLine.textContent = "Couldn't reach the scheduler. Is app.py running?";
    console.error(err);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Run sample generator";
  }
}

function renderTabs(sections) {
  tabsEl.innerHTML = "";
  sections.forEach((section) => {
    const btn = document.createElement("button");
    btn.className = "tab" + (section === activeSection ? " active" : "");
    btn.textContent = section;
    btn.addEventListener("click", () => {
      activeSection = section;
      renderGenGrid();
      [...tabsEl.children].forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
    });
    tabsEl.appendChild(btn);
  });
  tabsEl.hidden = false;
}

function renderGenGrid() {
  if (!currentGenData) return;
  const { slots, assignments } = currentGenData;

  const rows = assignments
    .filter((a) => a.section === activeSection)
    .sort((a, b) => slots.indexOf(a.slot) - slots.indexOf(b.slot));

  genGridBody.innerHTML = "";
  rows.forEach((a) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="slot-col">${a.slot}</td>
      <td class="subject-col">${a.subject}</td>
      <td>${a.teacher}</td>
      <td>${a.room}</td>
    `;
    genGridBody.appendChild(tr);
  });

  genGridWrap.hidden = false;
}

generateBtn.addEventListener("click", () => {
  if (!generatorLoadedOnce) generatorLoadedOnce = true;
  runGenerator();
});
