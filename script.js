// 1. Grab the elements from the page that we need to work with
const form = document.getElementById("todo-form");
const input = document.getElementById("todo-input");
const list = document.getElementById("todo-list");
const counter = document.getElementById("counter");
const clearDoneButton = document.getElementById("clear-done");
const filterButtons = document.querySelectorAll(".filter");

// 2. Our data: a list of tasks like { id: 123, text: "Buy milk", done: false }
//    We load it from the browser's storage so tasks survive a page refresh.
let todos = loadTodos();
let currentFilter = "all";

function loadTodos() {
  try {
    return JSON.parse(localStorage.getItem("todos")) || [];
  } catch {
    return [];
  }
}

function saveTodos() {
  try {
    localStorage.setItem("todos", JSON.stringify(todos));
  } catch {
    // Storage can be blocked (e.g. private mode). The app still works, it just won't remember.
  }
}

// 3. Draw the list on the screen based on the current data
function render() {
  list.innerHTML = "";

  const visible = todos.filter((todo) => {
    if (currentFilter === "active") return !todo.done;
    if (currentFilter === "done") return todo.done;
    return true;
  });

  if (visible.length === 0) {
    list.innerHTML = '<li class="empty">Nothing here yet 🎉</li>';
  }

  for (const todo of visible) {
    const li = document.createElement("li");
    li.className = "todo-item" + (todo.done ? " done" : "");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.addEventListener("change", () => toggleTodo(todo.id));

    const text = document.createElement("span");
    text.textContent = todo.text; // textContent is safe: it never runs typed HTML

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete";
    deleteButton.textContent = "×";
    deleteButton.title = "Delete";
    deleteButton.addEventListener("click", () => deleteTodo(todo.id));

    li.append(checkbox, text, deleteButton);
    list.append(li);
  }

  const left = todos.filter((todo) => !todo.done).length;
  counter.textContent = `${left} task${left === 1 ? "" : "s"} left`;
}

// 4. Actions that change the data. Each one saves and re-draws.
function addTodo(text) {
  todos.push({ id: Date.now(), text, done: false });
  saveTodos();
  render();
}

function toggleTodo(id) {
  const todo = todos.find((t) => t.id === id);
  todo.done = !todo.done;
  saveTodos();
  render();
}

function deleteTodo(id) {
  todos = todos.filter((t) => t.id !== id);
  saveTodos();
  render();
}

function clearDone() {
  todos = todos.filter((t) => !t.done);
  saveTodos();
  render();
}

// 5. Connect the page's buttons and form to those actions
form.addEventListener("submit", (event) => {
  event.preventDefault(); // stop the page from reloading
  const text = input.value.trim();
  if (text) {
    addTodo(text);
    input.value = "";
    input.focus();
  }
});

clearDoneButton.addEventListener("click", clearDone);

filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    currentFilter = button.dataset.filter;
    render();
  });
});

// 6. Draw the list once when the page first opens
render();
