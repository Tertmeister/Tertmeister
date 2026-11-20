# YouTube Shorts series set in Azul

Two series share one world (the continent of Azul):

- **What the Songs Don't Tell You** — dark-fantasy lore: a narrator explains the conspiracies and hidden
  history behind the official story. Episodes live in `shorts/epNN-<slug>/`; pipeline in `shorts/README.md`.
- **A Bestiary of Azul** — a mage-naturalist's field notes on the creatures and ecology of Azul, one engraved
  plate per episode. Plates live in `bestiary/plateNN-<slug>/`; pipeline in `bestiary/README.md`.

## Rules (both series)

1. **Script approval is required before any production.** When I write or rework a script, post it
   and stop. Do not generate narration, render video, or spend any credits until the user
   explicitly approves that script (e.g. "approved", "go", "looks good, make it"). Any change
   to the script after approval needs approval again. If the user supplies their own finished
   audio, confirm the transcript or script with them first.
2. List any lore details invented beyond what the user gave, so they can veto them.
3. Never spend Higgsfield (or other paid) credits without quoting the cost and getting a yes.

## What the Songs Don't Tell You — conventions
- Format: 1080x1920 vertical, under 3 minutes (aim for 45-65 s).
- Series title card "WHAT THE SONGS DON'T TELL YOU" plus "Ep. N · <Title>".
- Narration style: short, punchy lines; dry, knowing tone; ends on a hook.
- Default voice: Kokoro `am_michael`, speed 1.0 (until the user picks another).

## A Bestiary of Azul — conventions
- Lemo-Opuscar **Copperplate Engraving** style, portrait plate 1080x1920 at 24 fps, under 3 minutes
  (Plate I ran 2:21 against the user's 2:05–2:20 target).
- Each episode is a numbered plate: "A BESTIARY OF AZUL · PLATE N", title in roman capitals, the Latin
  name in italics; the mage narrator is unnamed until the user names them.
- Narration: clinical, academic nature-documentary tone; Kokoro `bm_george`.
- Colour only as transparent wash on the part being taught; the finished plate is the last shot.

## Toolchain (both series)
Free, offline tools in `tools/` (see `tools/README.md`): `tools/az narrate | say | align | place | fx | deliver | lint | doctor | selftest`.
`sh tools/setup_env.sh` installs anything missing (`--check` reports). Local narration costs no credits, but rule 1
still applies: narrate only an approved script (`az narrate … --check` shows pronunciations without making audio).

## Spellings (both series)
Azul, Ambershire, Nightingale's palace, Aquarion, the Great Oak, the Royal Archives, Lady Jane, the Black
Witch, the Witch of Hope, the Paladins of Parabellum, the Adventurers' Guild, the Bifrost, Cicada, Agent Kat,
the Wildlands, the Gold Wyvern (*Dracunculus fulgur*), Dynamo Sacs, Sylvan iron, Static-Ticks.
