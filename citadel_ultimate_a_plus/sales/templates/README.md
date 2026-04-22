# Reusable Template Pack

This pack parameterizes all six configured target verticals from `market/target_verticals.json`.

## Files

- `sales/templates/vertical_parameters.yaml`: vertical parameter map for:
  - `plumbing`
  - `hvac`
  - `roofing`
  - `landscaping`
  - `electrical`
  - `painting`
- `sales/templates/one_pager_template.md`: one-pager template with placeholders.
- `sales/templates/outbound_template.md`: outbound sequence template with placeholders.

## How to Use

1. Select the vertical block in `vertical_parameters.yaml`.
2. Fill placeholders in both templates using that block.
3. Save outputs to:
   - `sales/one_pagers/<vertical>.md`
   - `sales/outbound/<vertical>.md`
4. Review and add account-level personalization before sending.

## Placeholder Conventions

- Core:
  - `{{display_name}}`
  - `{{vertical_slug}}`
  - `{{audience}}`
  - `{{headline_phrase}}`
  - `{{proof_angle}}`
- Pain points:
  - `{{pain_point_1}}`
  - `{{pain_point_2}}`
  - `{{pain_point_3}}`
- Observation prompts:
  - `{{observation_prompt_1}}`
  - `{{observation_prompt_2}}`
  - `{{observation_prompt_3}}`

Use `{{geo_label}}` for territory text (example: `Harris County, TX`).
