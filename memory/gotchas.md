# Gotchas

- User wants project replies mainly in Simplified Chinese.
- Do not make architectural, business logic, or core product decisions silently.
- When the user asks to plan, review, assess, or explain first, do not edit project code until execution is approved.
- Never use `any`.
- The scheduler scripts originally ran one pass and exited; when the user asks for "monitoring" they may expect a long-running watch process. Be explicit about one-shot scheduler mode vs watch mode.
