# Macro Plan

## Current Understanding

`Zanao-LLM-Analyzer` is a Python project that collects and analyzes Zanao campus market/forum data. It has three major paths:

1. `zanao_climber`: crawls Zanao in-school posts, cross-school topic posts, and comments through captured mini-program API headers. Redis is used as a producer/worker queue. Results are stored in SQLite under `data/zanao_detailed_info/`.
2. `zanao_analyzer`: reads raw SQLite data, runs sentiment analysis, entity extraction, taxonomy matching, statistics, chart generation, and exposes FastAPI endpoints. Results are stored in `data/zanao_analyzed_info/analysis.db`.
3. `wx_login`, `group_chat_getter`, and `format_polisher`: auxiliary WeChat chat export and cleanup tools, not central to the Zanao forum monitoring goal.

Important findings:

- The repository contains sample/history SQLite data and an already-populated analysis database.
- Some configuration still uses placeholders: user tokens, school alias, API salt, request headers, platform/app info.
- `wx_login/main.py` currently contains hardcoded key/path values and should not be used as-is for a new user.
- Analyzer modules often import `config` as a top-level module, so some README commands may need a working-directory or import-path adjustment before they run reliably.
- For our intended project, the closest reusable parts are the Zanao crawler, SQLite schema, classification taxonomy, and analysis/database/API patterns.

## Candidate Product Direction

Goal: monitor Zanao campus market/forum posts for actionable demand signals such as requesting past exams, electronic textbooks, second-hand selling/buying, course resources, tutoring, rentals, rides, and similar intents, then push matched items to a chosen channel.

Scope clarification:

- Monitor only the user's own school's in-school Zanao campus market/forum.
- Do not collect cross-school topics or cross-school comments in the current product.
- The cloned `Zanao-LLM-Analyzer` data belongs to a different school and must be treated only as schema/sample data for local development, not as production content.
- The next priority is obtaining and safely configuring the user's own school's Zanao request parameters, then validating a small dry-run ingestion.

Recommended first slice:

1. Stabilize local configuration and dry-run ingestion on a small recent time window.
2. Add a demand-signal layer on top of stored posts/comments, focused on explicit categories and push eligibility.
3. Add deduplication and notification state so the same post is not pushed repeatedly.
4. Start with one push channel, then expand.
5. Keep AI optional in the first slice: use deterministic keyword/rule filters first, then add LLM/embedding reranking once data flow is stable.

Pending user decision:

- Preferred push channel: Feishu bot.
- Operating mode still needs confirmation before implementation planning.
- The user's own school Zanao request parameters still need to be obtained from a controlled capture: `X-Sc-Od`, `X-Sc-Alias`, API salt/signing inputs, version/platform/appid/User-Agent headers.

Capture findings:

- App API base: `http://api.app.zanao.com`.
- Mini-program API base: `https://api.x.zanao.com`.
- App and mini-program response schemas are highly similar for in-school list/detail/comment endpoints.
- Mini-program captured bodies are readable JSON after HTTP chunk decoding and gzip decompression.
- Recommended next implementation slice: mini-program `/thread/v2/list` dry-run client using `.env` configuration, with no database writes and no Feishu push yet.
- `ZANAO_API_SALT` has been verified locally against captured mini-program signatures and added to ignored `.env`.
