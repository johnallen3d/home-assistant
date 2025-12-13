---
description: Show pending HA enhancement todo items
---

Query `todo.ha_enhancements` using `ha_get_todo_items` with `status="needs_action"`.

Output ONLY a numbered list of item summaries, nothing else:
1. Item 1
2. Item 2

If empty, output: "No pending items."

Do NOT show completed items, counts, or any other commentary.
