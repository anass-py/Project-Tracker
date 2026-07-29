import streamlit as st
from supabase import create_client

# The two people using this board. Change these to your real names.
PEOPLE = ["Husband", "Wifey"]

st.set_page_config(page_title="Tracker", page_icon="▪", layout="centered")


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600;12..96,800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
  --ink: #16202E;
  --paper: #F7F8FA;
  --card: #FFFFFF;
  --line: #E3E7ED;
  --muted: #7C889B;
  --done: #2E7D5B;
  --done-soft: #DCEAE2;
}

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

header[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer { visibility: hidden; }

.masthead {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-weight: 800;
  font-size: 2.1rem;
  letter-spacing: -0.03em;
  color: var(--ink);
  margin: 0 0 1.4rem 0;
}

.proj-name {
  font-family: 'Bricolage Grotesque', sans-serif;
  font-weight: 600;
  font-size: 1.55rem;
  letter-spacing: -0.02em;
  color: var(--ink);
  margin: 0.2rem 0 0.15rem 0;
}
.proj-desc {
  color: var(--muted);
  font-size: 0.92rem;
  margin: 0 0 1.1rem 0;
}

/* the signature: one block per task */
.strip { display: flex; flex-wrap: wrap; gap: 5px; margin: 0.2rem 0 1.1rem 0; }
.blk {
  width: 26px; height: 26px;
  border-radius: 5px;
  background: var(--card);
  border: 1.5px solid var(--line);
  transition: background 140ms ease, border-color 140ms ease;
}
.blk.on { background: var(--done); border-color: var(--done); }
.strip.empty-note { color: var(--muted); font-size: 0.88rem; }

.stats { display: flex; gap: 10px; margin: 0 0 1.4rem 0; }
.stat {
  flex: 1;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.65rem 0.8rem;
}
.stat .who {
  font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.09em;
  color: var(--muted); font-weight: 600;
}
.stat .num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem; font-weight: 700; color: var(--ink);
  margin-top: 0.15rem;
}
.stat.total { background: var(--done-soft); border-color: var(--done-soft); }
.stat.total .num, .stat.total .who { color: var(--done); }

.chip {
  display: inline-block;
  font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--muted);
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 2px 9px;
  margin-top: 0.45rem;
  white-space: nowrap;
}

.stButton button {
  border-radius: 8px;
  transition: transform 90ms ease, border-color 120ms ease;
}
.stButton button:hover { transform: translateY(-1px); }
.stButton button:active { transform: translateY(0); }

.blk:hover { border-color: var(--muted); }
.blk.on { animation: pop 180ms ease-out; }
@keyframes pop {
  0%   { transform: scale(0.72); }
  60%  { transform: scale(1.06); }
  100% { transform: scale(1); }
}

.stat { transition: border-color 140ms ease; }
.stat:hover { border-color: var(--muted); }

div[data-testid="stHorizontalBlock"] {
  border-radius: 9px;
  transition: background 120ms ease;
}
div[data-testid="stHorizontalBlock"]:hover { background: rgba(22,32,46,0.025); }

@media (prefers-reduced-motion: reduce) {
  .blk.on { animation: none; }
  .stButton button:hover { transform: none; }
}

.danger { color: var(--muted); font-size: 0.82rem; margin-bottom: 0.4rem; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def get_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


sb = get_client()


def get_projects():
    return sb.table("projects").select("*").order("created_at").execute().data


def get_tasks(project_id):
    return (
        sb.table("tasks")
        .select("*")
        .eq("project_id", project_id)
        .order("created_at")
        .execute()
        .data
    )


def strip_html(tasks):
    if not tasks:
        return '<div class="strip empty-note">No tasks yet.</div>'
    cells = "".join(
        '<span class="blk on"></span>' if t["done"] else '<span class="blk"></span>'
        for t in tasks
    )
    return f'<div class="strip">{cells}</div>'


def stats_html(tasks):
    cards = []
    for person in PEOPLE:
        mine = [t for t in tasks if t.get("assignee") == person]
        cards.append(
            f'<div class="stat"><div class="who">{person}</div>'
            f'<div class="num">{sum(t["done"] for t in mine)} / {len(mine)}</div></div>'
        )
    cards.append(
        f'<div class="stat total"><div class="who">Together</div>'
        f'<div class="num">{sum(t["done"] for t in tasks)} / {len(tasks)}</div></div>'
    )
    return f'<div class="stats">{"".join(cards)}</div>'


def toggle_task(tid):
    sb.table("tasks").update({"done": st.session_state[f"chk_{tid}"]}).eq(
        "id", tid
    ).execute()


def delete_project(project_id, name):
    sb.table("projects").delete().eq("id", project_id).execute()
    st.session_state.board_msg = f"Deleted '{name}'."


def stage_task():
    text = st.session_state.task_input.strip()
    if text:
        st.session_state.new_tasks.append(
            {"text": text, "assignee": st.session_state.task_who}
        )


def save_new_project():
    name = st.session_state.new_name.strip()
    if not name:
        st.session_state.new_msg = ("error", "Give the project a name to save it.")
        return

    try:
        result = (
            sb.table("projects")
            .insert({"name": name, "description": st.session_state.new_desc})
            .execute()
        )
    except Exception:
        st.session_state.new_msg = ("error", f"'{name}' already exists. Pick another name.")
        return

    project_id = result.data[0]["id"]

    if st.session_state.new_tasks:
        sb.table("tasks").insert(
            [
                {"project_id": project_id, "text": t["text"], "assignee": t["assignee"]}
                for t in st.session_state.new_tasks
            ]
        ).execute()

    st.session_state.new_tasks = []
    st.session_state.new_name = ""
    st.session_state.new_desc = ""
    st.session_state.new_msg = ("success", f"Created '{name}'.")


if "new_tasks" not in st.session_state:
    st.session_state.new_tasks = []
if "editing" not in st.session_state:
    st.session_state.editing = None

st.markdown('<div class="masthead">Tracker</div>', unsafe_allow_html=True)

tab_view, tab_new = st.tabs(["Board", "New project"])


# --- Board ------------------------------------------------------------

with tab_view:
    projects = get_projects()

    if "board_msg" in st.session_state:
        st.success(st.session_state.pop("board_msg"))

    if not projects:
        st.info("Nothing here yet. Create your first project in the next tab.")
    else:
        by_name = {p["name"]: p for p in projects}
        selected = st.selectbox("Project", list(by_name.keys()), label_visibility="collapsed")
        project = by_name[selected]

        st.markdown(f'<div class="proj-name">{selected}</div>', unsafe_allow_html=True)
        if project["description"]:
            st.markdown(
                f'<div class="proj-desc">{project["description"]}</div>',
                unsafe_allow_html=True,
            )

        tasks = get_tasks(project["id"])

        st.markdown(strip_html(tasks), unsafe_allow_html=True)
        st.markdown(stats_html(tasks), unsafe_allow_html=True)

        who = st.radio(
            "Show", ["Everyone"] + PEOPLE, horizontal=True, label_visibility="collapsed"
        )
        shown = tasks if who == "Everyone" else [
            t for t in tasks if t.get("assignee") == who
        ]

        for task in shown:
            tid = task["id"]

            if st.session_state.editing == tid:
                c_text, c_who, c_ok, c_no = st.columns([5, 2.2, 0.8, 0.8])
                text = c_text.text_input(
                    "edit", value=task["text"], key=f"edit_{tid}",
                    label_visibility="collapsed",
                )
                assignee = c_who.selectbox(
                    "who", PEOPLE, key=f"who_{tid}",
                    index=PEOPLE.index(task["assignee"]) if task.get("assignee") in PEOPLE else 0,
                    label_visibility="collapsed",
                )
                if c_ok.button("Save", key=f"ok_{tid}"):
                    if text.strip():
                        sb.table("tasks").update(
                            {"text": text.strip(), "assignee": assignee}
                        ).eq("id", tid).execute()
                    st.session_state.editing = None
                    st.rerun()
                if c_no.button("Cancel", key=f"cancel_{tid}"):
                    st.session_state.editing = None
                    st.rerun()
            else:
                c_box, c_chip, c_edit, c_del = st.columns([6, 1.6, 0.7, 0.7])
                c_box.checkbox(
                    task["text"],
                    value=task["done"],
                    key=f"chk_{tid}",
                    on_change=toggle_task,
                    args=(tid,),
                )
                c_chip.markdown(
                    f'<span class="chip">{task.get("assignee") or "unassigned"}</span>',
                    unsafe_allow_html=True,
                )
                if c_edit.button("✏️", key=f"edit_btn_{tid}", help="Edit"):
                    st.session_state.editing = tid
                    st.rerun()
                if c_del.button("🗑️", key=f"del_{tid}", help="Delete"):
                    sb.table("tasks").delete().eq("id", tid).execute()
                    st.rerun()

        st.write("")
        with st.form("add_existing_task", clear_on_submit=True):
            c1, c2, c3 = st.columns([5, 2.2, 1])
            text = c1.text_input(
                "task", label_visibility="collapsed", placeholder="Add a task…"
            )
            assignee = c2.selectbox("who", PEOPLE, label_visibility="collapsed")
            added = c3.form_submit_button("Add")

        if added and text.strip():
            sb.table("tasks").insert(
                {"project_id": project["id"], "text": text.strip(), "assignee": assignee}
            ).execute()
            st.rerun()

        with st.expander("Delete this project"):
            st.markdown(
                f'<div class="danger">Removes "{selected}" and all {len(tasks)} '
                f'of its tasks. This cannot be undone.</div>',
                unsafe_allow_html=True,
            )
            sure = st.checkbox("Yes, delete it", key=f"sure_{project['id']}")
            st.button(
                "Delete project",
                disabled=not sure,
                on_click=delete_project,
                args=(project["id"], selected),
            )


# --- New project ------------------------------------------------------

with tab_new:
    st.text_input("Project name", key="new_name")
    st.text_area("Description", key="new_desc")

    with st.form("task_entry", clear_on_submit=True):
        c1, c2, c3 = st.columns([5, 2.2, 1])
        c1.text_input("task", key="task_input", label_visibility="collapsed",
                      placeholder="Task, then press Enter")
        c2.selectbox("who", PEOPLE, key="task_who", label_visibility="collapsed")
        c3.form_submit_button("Add", on_click=stage_task)

    for i, task in enumerate(st.session_state.new_tasks, 1):
        st.markdown(
            f'{i}. {task["text"]} &nbsp;<span class="chip">{task["assignee"]}</span>',
            unsafe_allow_html=True,
        )

    st.write("")
    st.button("Create project", on_click=save_new_project)

    if "new_msg" in st.session_state:
        kind, text = st.session_state.pop("new_msg")
        if kind == "error":
            st.error(text)
        else:
            st.success(text)