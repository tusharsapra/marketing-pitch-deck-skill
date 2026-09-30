# marketing-pitch-deck-skill

I am Tushar Sapra, a marketing expert who has worked on more than 20 pitches. I created this skill based on what I learned from that work.

This skill helps agency teams turn a brand website and a basic brief into a researched, story-led marketing pitch deck. It brings research, strategic choices, slide writing, media planning, practical executions and final quality checks into one workflow. Recurring review lessons are built into the process so they can be caught before handoff.

## What it produces

- A coherent narrative with headers that explain each slide's value.
- Source-backed brand, market, competitor and audience analysis relevant to the brief.
- Media roles, justified partner choices and tangible product-connected executions.
- Reconciled budget scenarios, clearly labelled forecasts and a measurement plan where needed.
- An editable presentation, requested preview and relevant supporting model/source records.

The workflow also supports revisions, including visual-only changes that preserve approved copy and slide order. It adapts to awareness, launches, acquisition, B2B/trade, portfolio and partnership pitches. It does not force the same chapter list or platforms into every deck.

## Works with Codex and Claude Code

The shared skill uses the Agent Skills format: a folder containing `SKILL.md`, relative references, scripts and templates. The same folder can be installed in both tools. `agents/openai.yaml` adds optional Codex interface metadata; Claude Code uses `SKILL.md`.

This release passed package checks and 15 utility tests. A fictional launch trial produced an eight-slide editable PPTX, an inspected PDF preview and a formula-driven model. A separate visual-only blueprint trial preserved approved content and slide order. It has not been run through both standalone Codex and Claude Code CLIs. Rendering, browsing and presentation output depend on the tools available in your agent environment.

## Install

Download the [repository](https://github.com/tusharsapra/marketing-pitch-deck-skill) or its [ZIP archive](https://github.com/tusharsapra/marketing-pitch-deck-skill/archive/refs/heads/main.zip) and extract it. Open a terminal in the repository folder.

Python 3.10 or newer is needed for the optional installer and validation utilities. On Windows, use `py -3` where `python3` is unavailable.

Install for both tools in your user account:

```bash
python3 tools/install_skill.py --agent both --scope user
```

Install for one tool:

```bash
python3 tools/install_skill.py --agent codex --scope user
python3 tools/install_skill.py --agent claude --scope user
```

Install only in a specific project:

```bash
python3 tools/install_skill.py --agent both --scope project --project-dir /path/to/project
```

| Tool | User-wide location | Project location |
| --- | --- | --- |
| Codex | `~/.agents/skills/marketing-pitch-deck-skill/` | `.agents/skills/marketing-pitch-deck-skill/` |
| Claude Code | `~/.claude/skills/marketing-pitch-deck-skill/` | `.claude/skills/marketing-pitch-deck-skill/` |

For manual installation, copy the entire `skills/marketing-pitch-deck-skill` folder to the relevant location. Keep its references, scripts and assets together. These instructions cover local Codex and Claude Code; they do not claim installation into every web or hosted product.

The installer refuses to overwrite an existing skill. To update, download/pull the latest repository and rerun with `--force`. It backs up the previous folder outside the skill discovery directory. User-wide and project copies are separate; update the copy you use and avoid maintaining conflicting versions at both scopes.

## Use

In Codex, invoke `$marketing-pitch-deck-skill`. In Claude Code, invoke `/marketing-pitch-deck-skill`.

Example request:

```text
Use marketing-pitch-deck-skill.
Brand website: https://your-brand.example
Brief: Launch this product in the priority cities among homeowners and specifiers.
Objective: Build consideration and qualified enquiries.
Budget: INR 30 lakh and INR 50 lakh, media only; identify other costs separately.
Timing: Eight weeks after launch readiness.
Output: 18 slides including cover, editable PPTX and PDF preview.
Use the supplied brand template. Label forecasts and proposed inventory.
```

Start with the website and brief. Add budget, geography, audiences, timing, existing deck, official assets and a template when available. If details are missing, the agent should ask only material questions, continue useful work and record authorized assumptions.

The creator introduction belongs in this README. It is not inserted into client decks.

## Tools and requirements

The skill does not include paid accounts, API credentials, partner access or a presentation engine. It uses your agent's available search, file, image, calculation, presentation and rendering tools. Research should use accessible sources or supplied evidence; missing data must not be invented.

Use an existing presentation tool/skill when available. An optional local route is Node.js with [PptxGenJS](https://gitbrent.github.io/PptxGenJS/), with LibreOffice/Poppler for preview rendering. Consult their current documentation and install dependencies in the working project. The bundled Python tools need only the standard library.

| Utility | Purpose |
| --- | --- |
| `init_project.py` | Copy brief, blueprint, ledger and revision templates without overwriting work |
| `check_environment.py` | Report optional local executables and slide tooling |
| `validate_plan.py` | Check blueprint references, count, disclosure presence and supported media arithmetic |
| `inspect_pptx.py` | Inspect actual slide order, native objects, text and basic canvas bounds |

Example commands after filling a project blueprint:

```bash
python3 skills/marketing-pitch-deck-skill/scripts/init_project.py ./pitch-project
python3 skills/marketing-pitch-deck-skill/scripts/check_environment.py --workdir ./pitch-project
python3 skills/marketing-pitch-deck-skill/scripts/validate_plan.py ./pitch-project/deck-plan.json
python3 skills/marketing-pitch-deck-skill/scripts/inspect_pptx.py ./pitch-project/output/deck.pptx --expected-slides 18
```

The blank blueprint intentionally fails until filled. See `examples/sample-plan.json` for syntax and the skill's `references/plan-schema.md` for field definitions. Sample figures are fictional, not market benchmarks.

A clean script result does not prove source truth, strategic quality or visual quality. The workflow requires human-readable evidence, semantic review and inspection of every rendered slide.

## Repository contents

```text
marketing-pitch-deck-skill/
  .github/workflows/validate.yml
  README.md
  LICENSE
  skills/marketing-pitch-deck-skill/
    SKILL.md
    agents/openai.yaml
    references/
    scripts/
    assets/
  examples/
  tests/
  tools/
```

The skill keeps its main workflow concise and loads detailed references as needed. The references explain research, audience strategy, narrative, media/executions, economics, production and learned review checks.

## Get the source

The public repository is [tusharsapra/marketing-pitch-deck-skill](https://github.com/tusharsapra/marketing-pitch-deck-skill). Clone it or download its ZIP archive, then use the installation steps above. Keep `skills/marketing-pitch-deck-skill/SKILL.md` and its supporting files together. No marketplace registration is required for this local folder installation.

## Check changes before sharing

```bash
python3 tools/validate_package.py
python3 -m unittest discover -s tests -v
python3 skills/marketing-pitch-deck-skill/scripts/validate_plan.py examples/sample-plan.json
```

The included GitHub Actions workflow runs these checks on Ubuntu and Windows with Python 3.10 and 3.12 after each push. It needs no added account secret.

For behavioral changes, try materially different briefs and inspect the actual output: source support, coherent headers, practical execution, reconciled economics and preserved revision constraints. Automated checks cover specific mechanics, not the entire pitch-making judgment.

## Privacy and reuse

Use only public, fictional or explicitly authorized materials in contributions. Keep confidential briefs, client decks, private rate cards, screenshots, credentials and generated project outputs out of this public repository. The included examples are fictional. Add real brand assets only inside an authorized working project.

## License

MIT. Anyone may use, adapt and share the skill under the terms in [LICENSE](LICENSE). Third-party research, brand assets and tools retain their own rights and terms; the repository license does not grant rights to those materials.

Format and installation references: [Agent Skills specification](https://agentskills.io/specification), [Codex skills documentation](https://developers.openai.com/codex/skills/), [Claude Code skills documentation](https://code.claude.com/docs/en/skills).
