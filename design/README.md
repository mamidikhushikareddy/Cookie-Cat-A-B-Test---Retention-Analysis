# Cookie Cat design & motion brief

## Penpot (optional design workspace)
Open [Penpot](https://penpot.app/) and create a file named `Cookie Cat — Quest Arcade`. Use `design_tokens.json` as the color/type/radius reference. Create these frames:
1. Quest map with four mission nodes.
2. Mission card with prompt, three choices, XP reward, and feedback.
3. Boss-battle decision card.
4. Badge vault and investigator rank.
5. Evidence view with retention difference and confidence interval.

The current repository includes the tokens and functional in-app quest UI; it does **not** include a Penpot cloud file or claim to have created one.

## Rive (optional animation workflow)
Open [Rive](https://rive.app/) and create a small mascot state machine with states `idle`, `thinking`, `correct`, `retry`, and `badge_unlock`. Export the `.riv` asset and add it to `assets/rive/` before wiring it into the UI. The app currently uses Streamlit feedback and confetti; no Rive asset is bundled.

This makes Penpot and Rive honest optional integrations rather than fake linked services.
