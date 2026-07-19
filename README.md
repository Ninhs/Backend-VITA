# OPC AI Agent — Frontend/Backend Integration

## Files

- `Decision & Partner Agent 1_FRONTEND_ALIGNED.yml`
- `Decision & Partner Agent 2_BACKEND_ALIGNED.yml`
- `main_FRONTEND_ALIGNED.py`
- `frontend_FRONTEND_ALIGNED.js`
- `validate_integration.py`
- `validation_report.txt`

## What changed

### Agent 1

- Start inputs now match FastAPI: `contract_id`, optional `case_data`.
- Normal and missing-data branches converge into one End node.
- End outputs use the exact generic names consumed by the dashboard:
  `status`, `message`, `decision`, `finance_result`, financial metrics,
  risk fields, confidence fields, missing fields and Decision package identifiers.
- The full Decision package is stored in `agent_decisions.output_ref` so Agent 2
  can recover the latest draft using only `contract_id`.
- Decision Card contains three reasons, one protective condition, partner option,
  finance/risk summaries, masking and API/task usage.

### Agent 2

- Start inputs match the current backend: `contract_id`, `founder_decision`,
  optional `external_send_confirmation`.
- `decision_id` and `decision_package` remain optional for direct/manual calls.
- When they are absent, Agent 2 loads the latest Agent 1 draft audit from
  `agent_decisions` by `contract_id` and parses `output_ref`.
- Final outputs include generic aliases (`status`, `message`, `decision`,
  `approval_status`, `agent_decision`) in addition to the `final_*` audit fields.

### Optional backend/frontend patches

The supplied backend patch forwards `decision_id` and `decision_package` when the
browser has them. Agent 2 still works without them by loading the latest audit.

The supplied frontend patch:

- renders the three Agent-generated Decision Card reasons;
- renders partner/product and protective condition;
- sends all three Founder actions through Agent 2;
- forwards the Agent 1 package to Agent 2;
- updates approval/session status after Agent 2 finishes.

## Import order

1. Publish Data & Finance Agent and Risk & Compliance Agent.
2. Import and publish `Decision & Partner Agent 1_FRONTEND_ALIGNED.yml`.
3. Confirm the two internal Dify API keys in Agent 1 point to the published
   Finance and Risk workflows.
4. Import and publish `Decision & Partner Agent 2_BACKEND_ALIGNED.yml`.
5. Replace backend `main.py` with `main_FRONTEND_ALIGNED.py`.
6. Replace frontend `frontend.js` with `frontend_FRONTEND_ALIGNED.js`.
7. Set the new Agent 1 and Agent 2 app keys in backend environment variables.

## Required smoke test

1. Run `CON-004` from the dashboard.
2. Confirm these outputs are non-empty:
   - `decision`
   - `finance_result`
   - `computed_margin`
   - `maximum_funding_need`
   - `risk_level`
   - `decision_id`
   - `decision_package`
3. Confirm the dashboard shows three reasons and one protective condition.
4. Test Founder `approve`, `request_more_info`, and `reject`.
5. Confirm Agent 2 writes the final row to `decisions` and a row to
   `human_approvals`.

## Expected CON-004 values

- Computed margin: approximately `0.24`
- Target margin: `0.28`
- Maximum funding need: approximately `710000000`
- Overall risk: `HIGH` or `CRITICAL` depending on the current Risk package
- Founder approval required: `true`
