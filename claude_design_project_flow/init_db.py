"""Database initialization — clean slate, no mock data."""

import sqlite3
import json
from datetime import datetime, timedelta

DB_PATH = 'onboarding.db'


# ── Schema ──────────────────────────────────────────────────────────────────

def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('PRAGMA foreign_keys = ON')

    # ── Core project tables ─────────────────────────────────────────────
    c.executescript('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            domain TEXT NOT NULL,
            environment TEXT NOT NULL,
            team_name TEXT, team_email TEXT, jira_project TEXT,
            aws_account_id TEXT, aws_region TEXT, eks_cluster_name TEXT,
            status TEXT DEFAULT 'in_progress',
            start_date TEXT, target_completion TEXT,
            template_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            phase_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            target_start TEXT, target_end TEXT,
            started_at TEXT, completed_at TEXT, completed_by TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase_id INTEGER NOT NULL,
            task_order INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            ownership TEXT DEFAULT 'Platform Team',
            instructions TEXT,
            jira_reference TEXT,
            sample_reference TEXT,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            started_at TEXT, completed_at TEXT, completed_by TEXT,
            is_blocked INTEGER DEFAULT 0,
            automation_type TEXT DEFAULT 'manual',
            automation_config TEXT DEFAULT '{}',
            FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS task_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_label TEXT NOT NULL,
            action_url TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            comment_text TEXT NOT NULL,
            author TEXT NOT NULL,
            author_type TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS phase_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            phase_id INTEGER NOT NULL,
            depends_on_phase_id INTEGER NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE,
            FOREIGN KEY (depends_on_phase_id) REFERENCES phases(id) ON DELETE CASCADE,
            UNIQUE(project_id, phase_id, depends_on_phase_id)
        );
        CREATE TABLE IF NOT EXISTS category_swimlane_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL UNIQUE,
            swimlane_id TEXT NOT NULL
        );

        -- Template system tables
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT UNIQUE NOT NULL,
            description TEXT,
            version TEXT DEFAULT '1.0',
            is_default INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS template_phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            phase_name TEXT NOT NULL,
            duration_days INTEGER DEFAULT 14,
            FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
            UNIQUE(template_id, phase_number)
        );
        CREATE TABLE IF NOT EXISTS template_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_phase_id INTEGER NOT NULL,
            task_order INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            ownership TEXT DEFAULT 'Platform Team',
            instructions TEXT,
            jira_reference TEXT,
            sample_reference TEXT,
            notes TEXT,
            automation_type TEXT DEFAULT 'manual',
            automation_config TEXT DEFAULT '{}',
            FOREIGN KEY (template_phase_id) REFERENCES template_phases(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS template_task_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_task_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            action_label TEXT NOT NULL,
            action_url TEXT NOT NULL,
            FOREIGN KEY (template_task_id) REFERENCES template_tasks(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS template_phase_dependencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_id INTEGER NOT NULL,
            phase_number INTEGER NOT NULL,
            depends_on_phase_number INTEGER NOT NULL,
            FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
            UNIQUE(template_id, phase_number, depends_on_phase_number)
        );
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL DEFAULT 1,
            code TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS environments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0
        );

        -- Deadline tracking tables
        CREATE TABLE IF NOT EXISTS phase_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phase_id INTEGER NOT NULL,
            ownership TEXT NOT NULL,
            planned_date TEXT,
            agreed_date TEXT,
            actual_date TEXT,
            variance_days INTEGER,
            notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (phase_id) REFERENCES phases(id) ON DELETE CASCADE,
            UNIQUE(phase_id, ownership)
        );
        CREATE TABLE IF NOT EXISTS task_deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            planned_date TEXT,
            agreed_date TEXT,
            actual_date TEXT,
            variance_days INTEGER,
            notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            UNIQUE(task_id)
        );
    ''')

    # ── Seed only the default program (required for domains) ─────────────
    c.execute("""INSERT OR IGNORE INTO programs (id, code, display_name, description)
                 VALUES (1, 'Application_EKS', 'Application on EKS', 'Application Infrastructure on EKS platform')""")

    # ── Seed default environments ────────────────────────────────────────
    envs = [('dev', 'Development', 1), ('uat', 'UAT', 2), ('vpt', 'VPT', 3), ('prod', 'Production', 4)]
    for code, name, order in envs:
        c.execute("INSERT OR IGNORE INTO environments (code, display_name, sort_order) VALUES (?,?,?)",
                  (code, name, order))

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH} (clean slate)")
    print("No mock data created — create your own domains, templates, and projects")
    print("Run: python app.py")


# ── Project creation from template ─────────────────────────────────────────

def create_project_from_template(c, project_id, template_id, project_start):
    """Stamp a template into a project: create phases, tasks, dependencies, actions."""
    t_phases = c.execute(
        "SELECT id, phase_number, phase_name, duration_days FROM template_phases WHERE template_id=? ORDER BY phase_number",
        (template_id,)
    ).fetchall()

    phase_lookup = {}
    running_date = datetime.strptime(project_start, '%Y-%m-%d').date() if isinstance(project_start, str) else project_start

    for tp_id, pnum, pname, dur in t_phases:
        target_start = running_date.strftime('%Y-%m-%d')
        target_end = (running_date + timedelta(days=dur)).strftime('%Y-%m-%d')

        c.execute("""INSERT INTO phases (project_id, phase_number, phase_name, status,
                     target_start, target_end) VALUES (?,?,?,?,?,?)""",
                  (project_id, pnum, pname, 'pending', target_start, target_end))
        phase_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]
        phase_lookup[pnum] = phase_id

        # Copy tasks from template
        t_tasks = c.execute(
            """SELECT id, task_order, task_name, category, description, ownership,
                      instructions, jira_reference, sample_reference, notes,
                      automation_type, automation_config
               FROM template_tasks WHERE template_phase_id=? ORDER BY task_order""",
            (tp_id,)
        ).fetchall()

        for tt_id, t_order, t_name, t_cat, t_desc, t_own, t_instr, t_jira, t_sample, t_notes, t_auto, t_acfg in t_tasks:
            c.execute("""INSERT INTO tasks (phase_id, task_order, task_name, category, description,
                         ownership, instructions, jira_reference, sample_reference, notes, status,
                         automation_type, automation_config)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                      (phase_id, t_order, t_name, t_cat, t_desc, t_own, t_instr, t_jira, t_sample, t_notes,
                       'pending', t_auto, t_acfg))
            task_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Copy task actions
            for _, _, a_type, a_label, a_url in c.execute(
                "SELECT * FROM template_task_actions WHERE template_task_id=?", (tt_id,)
            ).fetchall():
                c.execute("INSERT INTO task_actions VALUES (NULL,?,?,?,?)",
                          (task_id, a_type, a_label, a_url))

        # Advance date only for main sequential path
        if pnum in [1, 2, 3]:
            running_date += timedelta(days=dur)

    # Copy dependencies
    t_deps = c.execute(
        "SELECT phase_number, depends_on_phase_number FROM template_phase_dependencies WHERE template_id=?",
        (template_id,)
    ).fetchall()
    for dep_num, prereq_num in t_deps:
        if dep_num in phase_lookup and prereq_num in phase_lookup:
            c.execute("INSERT INTO phase_dependencies (project_id, phase_id, depends_on_phase_id) VALUES (?,?,?)",
                      (project_id, phase_lookup[dep_num], phase_lookup[prereq_num]))


if __name__ == '__main__':
    init_database()
