---
description: Show pending HA enhancement todo items
---

Query `todo.ha_enhancements` using `ha_get_todo_items` with `status="needs_action"`.

Output ONLY a bullet list of item summaries, nothing else:
- Item 1
- Item 2

If empty, output: "No pending items."

Do NOT show completed items, counts, or any other commentary.
