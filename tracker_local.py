import json
import os
import uuid

import streamlit as st

DATA_FILE = "projects.json"


def new_task(text):
    return {"id": uuid.uuid4().hex[:8], "text": text, "done": False}


def load_projects():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        projects = json.load(f)
    # older files have tasks without an id
    for project in projects.values():
        for task in project["tasks"]:
            task.setdefault("id", uuid.uuid4().hex[:8])
    return projects


def save_projects(projects):
    with open(DATA_FILE, "w") as f:
        json.dump(projects, f, indent=2)


def add_new_task():
    text = st.session_state.task_input.strip()
    if text:
        st.session_state.new_tasks.append(text)


def save_new_project():
    name = st.session_state.new_name.strip()
    saved = load_projects()

    if not name:
        st.session_state.new_msg = ("error", "The project needs a name.")
        return
    if name in saved:
        st.session_state.new_msg = ("error", "A project with that name already exists.")
        return

    saved[name] = {
        "description": st.session_state.new_desc,
        "tasks": [new_task(t) for t in st.session_state.new_tasks],
    }
    save_projects(saved)

    st.session_state.new_tasks = []
    st.session_state.new_name = ""
    st.session_state.new_desc = ""
    st.session_state.new_msg = ("success", f"Saved '{name}'.")


if "new_tasks" not in st.session_state:
    st.session_state.new_tasks = []
if "editing" not in st.session_state:
    st.session_state.editing = None

projects = load_projects()

st.title("Project Tracker")

tab_new, tab_view = st.tabs(["New project", "My projects"])


# --- Create a project -------------------------------------------------

with tab_new:
    st.text_input("Project name", key="new_name")
    st.text_area("Description", key="new_desc")

    with st.form("task_entry", clear_on_submit=True):
        st.text_input("Task (press Enter to add)", key="task_input")
        st.form_submit_button("Add", on_click=add_new_task)

    for i, task in enumerate(st.session_state.new_tasks, 1):
        st.write(f"{i}. {task}")

    st.button("Save project", on_click=save_new_project)

    if "new_msg" in st.session_state:
        kind, text = st.session_state.pop("new_msg")
        if kind == "error":
            st.error(text)
        else:
            st.success(text)


# --- View and work on a project ---------------------------------------

with tab_view:
    if not projects:
        st.info("No projects yet. Create one in the other tab.")
    else:
        selected = st.selectbox("Project", list(projects.keys()))
        project = projects[selected]

        st.write(project["description"])

        total = len(project["tasks"])
        done = sum(t["done"] for t in project["tasks"])

        st.progress(done / total if total else 0.0)
        st.write(f"**{done}/{total}** done")

        changed = False
        delete_id = None

        for task in project["tasks"]:
            tid = task["id"]
            left, mid, right = st.columns([8, 1, 1])

            if st.session_state.editing == tid:
                text = left.text_input(
                    "edit",
                    value=task["text"],
                    key=f"edit_{tid}",
                    label_visibility="collapsed",
                )
                if mid.button("✅", key=f"ok_{tid}", help="Save"):
                    if text.strip():
                        task["text"] = text.strip()
                        save_projects(projects)
                    st.session_state.editing = None
                    st.rerun()
                if right.button("↩️", key=f"cancel_{tid}", help="Cancel"):
                    st.session_state.editing = None
                    st.rerun()
            else:
                checked = left.checkbox(task["text"], value=task["done"], key=f"chk_{tid}")
                if checked != task["done"]:
                    task["done"] = checked
                    changed = True
                if mid.button("✏️", key=f"edit_btn_{tid}", help="Edit"):
                    st.session_state.editing = tid
                    st.rerun()
                if right.button("🗑️", key=f"del_{tid}", help="Delete"):
                    delete_id = tid

        if delete_id is not None:
            project["tasks"] = [t for t in project["tasks"] if t["id"] != delete_id]
            save_projects(projects)
            st.rerun()

        if changed:
            save_projects(projects)
            st.rerun()

        with st.form("add_existing_task", clear_on_submit=True):
            text = st.text_input("Add a task", label_visibility="collapsed",
                                 placeholder="New task…")
            added = st.form_submit_button("➕")

        if added and text.strip():
            project["tasks"].append(new_task(text.strip()))
            save_projects(projects)
            st.rerun()