# API Endpoint Inventory

**Generated:** 2026-03-05T12:52:03.984296

**Total Endpoints:** 184

## Summary

- **Tested:** 0
- **Accessible:** 0
- **Not Tested:** 184

## By Method

- **GET:** 98
- **PATCH:** 6
- **POST:** 80

## By Framework

- **express:** 73
- **fastapi:** 111

## By Project

### B-A-P

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `B-A-P/src/main.py:100`
   - Framework: fastapi

⚪ 🔓 **GET** `/ready`
   - Function: `ready`
   - File: `B-A-P/src/main.py:105`
   - Framework: fastapi

⚪ 🔓 **GET** `/metrics`
   - Function: `metrics`
   - File: `B-A-P/src/main.py:121`
   - Framework: fastapi

⚪ 🔓 **GET** `/`
   - Function: `root`
   - File: `B-A-P/src/main.py:126`
   - Framework: fastapi

⚪ 🔓 **POST** `/upload-data`
   - Function: `upload_data`
   - File: `B-A-P/src/api/routes/data.py:21`
   - Framework: fastapi
   - Parameters: file, name, description

⚪ 🔓 **GET** `/datasets`
   - Function: `list_datasets`
   - File: `B-A-P/src/api/routes/data.py:97`
   - Framework: fastapi
   - Parameters: skip, limit

⚪ 🔓 **GET** `/datasets/{dataset_id}`
   - Function: `get_dataset`
   - File: `B-A-P/src/api/routes/data.py:117`
   - Framework: fastapi
   - Parameters: dataset_id

⚪ 🔓 **POST** `/run`
   - Function: `run_pipeline`
   - File: `B-A-P/src/api/routes/pipeline.py:21`
   - Framework: fastapi
   - Parameters: background_tasks, user

⚪ 🔓 **GET** `/status/{job_id}`
   - Function: `get_pipeline_status`
   - File: `B-A-P/src/api/routes/pipeline.py:86`
   - Framework: fastapi
   - Parameters: job_id

⚪ 🔓 **GET** `/summary`
   - Function: `analytics_summary`
   - File: `B-A-P/src/api/routes/analytics.py:17`
   - Framework: fastapi
   - Parameters: dataset_id

⚪ 🔓 **POST** `/forecast`
   - Function: `analytics_forecast`
   - File: `B-A-P/src/api/routes/analytics.py:68`
   - Framework: fastapi

### Citadel

⚪ 🔓 **GET** `/api/health`
   - Function: `health_check`
   - File: `Citadel/backend/app.py:6`
   - Framework: fastapi

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/local_agent/main.py:194`
   - Framework: fastapi

⚪ 🔓 **GET** `/`
   - Function: `get_index`
   - File: `Citadel/local_agent/main.py:198`
   - Framework: fastapi

⚪ 🔓 **POST** `/v1/chat/completions`
   - Function: `chat_completions`
   - File: `Citadel/local_agent/main.py:202`
   - Framework: fastapi

⚪ 🔓 **GET** `/health`
   - Function: `health_check`
   - File: `Citadel/notebooks/gateway/main.py:109`
   - Framework: fastapi

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/nl_agent/main.py:277`
   - Framework: fastapi

⚪ 🔓 **POST** `/v1/chat/completions`
   - Function: `chat_completions`
   - File: `Citadel/services/nl_agent/main.py:282`
   - Framework: fastapi

⚪ 🔓 **POST** `/effect`
   - Function: `estimate_effect`
   - File: `Citadel/services/causal_inference/main.py:75`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/causal_inference/main.py:115`
   - Framework: fastapi

⚪ 🔓 **POST** `/execute`
   - Function: `execute_shell_command`
   - File: `Citadel/services/shell_command/main.py:61`
   - Framework: fastapi
   - Parameters: cmd, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/shell_command/main.py:83`
   - Framework: fastapi

⚪ 🔓 **POST** `/embed/text`
   - Function: `embed_text`
   - File: `Citadel/services/multi_modal/main.py:97`
   - Framework: fastapi
   - Parameters: payload, api_key

⚪ 🔓 **POST** `/embed/image`
   - Function: `embed_image`
   - File: `Citadel/services/multi_modal/main.py:102`
   - Framework: fastapi
   - Parameters: file, api_key

⚪ 🔓 **POST** `/search`
   - Function: `search`
   - File: `Citadel/services/multi_modal/main.py:112`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/multi_modal/main.py:139`
   - Framework: fastapi

⚪ 🔓 **POST** `/search`
   - Function: `web_search`
   - File: `Citadel/services/web_service/main.py:72`
   - Framework: fastapi
   - Parameters: api_key

⚪ 🔓 **POST** `/fetch`
   - Function: `fetch_url`
   - File: `Citadel/services/web_service/main.py:85`
   - Framework: fastapi
   - Parameters: api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/web_service/main.py:109`
   - Framework: fastapi

⚪ 🔓 **POST** `/index`
   - Function: `index_documents`
   - File: `Citadel/services/vector_search/main.py:146`
   - Framework: fastapi
   - Parameters: documents, api_key

⚪ 🔓 **POST** `/search`
   - Function: `search`
   - File: `Citadel/services/vector_search/main.py:167`
   - Framework: fastapi
   - Parameters: query, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health_check`
   - File: `Citadel/services/vector_search/main.py:185`
   - Framework: fastapi

⚪ 🔓 **GET** `/health`
   - Function: `health_check_stub`
   - File: `Citadel/services/vector_search/main.py:194`
   - Framework: fastapi

⚪ 🔓 **POST** `/publish`
   - Function: `publish_event`
   - File: `Citadel/services/orchestrator/main.py:195`
   - Framework: fastapi
   - Parameters: event, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/orchestrator/main.py:204`
   - Framework: fastapi

⚪ 🔓 **POST** `/evaluate`
   - Function: `evaluate`
   - File: `Citadel/services/rule_engine/main.py:84`
   - Framework: fastapi
   - Parameters: event, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/rule_engine/main.py:108`
   - Framework: fastapi

⚪ 🔓 **POST** `/forecast`
   - Function: `forecast`
   - File: `Citadel/services/time_series/main.py:87`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **POST** `/anomaly`
   - Function: `anomaly_detection`
   - File: `Citadel/services/time_series/main.py:105`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/time_series/main.py:125`
   - Framework: fastapi

⚪ 🔓 **GET** `/health`
   - Function: `health_check_stub`
   - File: `Citadel/services/knowledge_graph/main.py:74`
   - Framework: fastapi

⚪ 🔓 **POST** `/query`
   - Function: `execute_query`
   - File: `Citadel/services/knowledge_graph/main.py:127`
   - Framework: fastapi
   - Parameters: api_key

⚪ 🔓 **GET** `/health`
   - Function: `health_check`
   - File: `Citadel/services/knowledge_graph/main.py:156`
   - Framework: fastapi

⚪ 🔓 **POST** `/train`
   - Function: `train_model`
   - File: `Citadel/services/hierarchical_classification/main.py:91`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **POST** `/predict`
   - Function: `predict`
   - File: `Citadel/services/hierarchical_classification/main.py:122`
   - Framework: fastapi
   - Parameters: req, api_key

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Citadel/services/hierarchical_classification/main.py:140`
   - Framework: fastapi

### DocuMancer

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `DocuMancer/backend/server.py:133`
   - Framework: fastapi

⚪ 🔓 **POST** `/convert`
   - Function: `convert`
   - File: `DocuMancer/backend/server.py:148`
   - Framework: fastapi
   - Parameters: http_request

### Gen-H

⚪ 🔓 **GET** `/health`
   - Function: `app_get_374`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:374`
   - Framework: express

⚪ 🔓 **GET** `/api/system/config`
   - Function: `app_get_377`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:377`
   - Framework: express

⚪ 🔓 **POST** `/api/system/readiness`
   - Function: `app_post_391`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:391`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history`
   - Function: `app_get_408`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:408`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history/:file`
   - Function: `app_get_416`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:416`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history/:file/download`
   - Function: `app_get_426`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:426`
   - Framework: express

⚪ 🔓 **POST** `/api/system/profile`
   - Function: `app_post_435`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:435`
   - Framework: express

⚪ 🔓 **POST** `/api/system/dry-run`
   - Function: `app_post_447`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:447`
   - Framework: express

⚪ 🔓 **POST** `/api/system/run`
   - Function: `app_post_459`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:459`
   - Framework: express

⚪ 🔓 **POST** `/api/system/promote`
   - Function: `app_post_471`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:471`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns`
   - Function: `app_post_577`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:577`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns`
   - Function: `app_get_590`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:590`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns/:id/start`
   - Function: `app_post_607`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:607`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:campaign_id/leads`
   - Function: `app_get_620`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:620`
   - Framework: express

⚪ 🔓 **PATCH** `/api/leads/:id`
   - Function: `app_patch_638`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:638`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:id/stats`
   - Function: `app_get_652`
   - File: `Gen-H/hvac-lead-generator/api/dist/server.js:652`
   - Framework: express

⚪ 🔓 **GET** `/health`
   - Function: `app_get_22`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:22`
   - Framework: express

⚪ 🔓 **GET** `/api/templates`
   - Function: `app_get_25`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:25`
   - Framework: express

⚪ 🔓 **GET** `/api/templates/:id`
   - Function: `app_get_46`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:46`
   - Framework: express

⚪ 🔓 **POST** `/api/templates`
   - Function: `app_post_59`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:59`
   - Framework: express

⚪ 🔓 **GET** `/api/companies`
   - Function: `app_get_92`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:92`
   - Framework: express

⚪ 🔓 **POST** `/api/companies`
   - Function: `app_post_101`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:101`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments`
   - Function: `app_get_113`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:113`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments`
   - Function: `app_post_138`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:138`
   - Framework: express

⚪ 🔓 **PATCH** `/api/deployments/:id/customize`
   - Function: `app_patch_151`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:151`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments/:id/deploy`
   - Function: `app_post_165`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:165`
   - Framework: express

⚪ 🔓 **POST** `/api/analytics/:deployment_id`
   - Function: `app_post_178`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:178`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments/:id/analytics`
   - Function: `app_get_190`
   - File: `Gen-H/hvac-template-library/api-gateway/dist/server.js:190`
   - Framework: express

⚪ 🔓 **GET** `/api/templates`
   - Function: `app_get_22`
   - File: `Gen-H/.extracted/api_server.ts:22`
   - Framework: express

⚪ 🔓 **GET** `/api/templates/:id`
   - Function: `app_get_46`
   - File: `Gen-H/.extracted/api_server.ts:46`
   - Framework: express

⚪ 🔓 **POST** `/api/templates`
   - Function: `app_post_65`
   - File: `Gen-H/.extracted/api_server.ts:65`
   - Framework: express

⚪ 🔓 **GET** `/api/companies`
   - Function: `app_get_112`
   - File: `Gen-H/.extracted/api_server.ts:112`
   - Framework: express

⚪ 🔓 **POST** `/api/companies`
   - Function: `app_post_121`
   - File: `Gen-H/.extracted/api_server.ts:121`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments`
   - Function: `app_get_142`
   - File: `Gen-H/.extracted/api_server.ts:142`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments`
   - Function: `app_post_170`
   - File: `Gen-H/.extracted/api_server.ts:170`
   - Framework: express

⚪ 🔓 **PATCH** `/api/deployments/:id/customize`
   - Function: `app_patch_189`
   - File: `Gen-H/.extracted/api_server.ts:189`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments/:id/deploy`
   - Function: `app_post_209`
   - File: `Gen-H/.extracted/api_server.ts:209`
   - Framework: express

⚪ 🔓 **POST** `/api/analytics/:deployment_id`
   - Function: `app_post_233`
   - File: `Gen-H/.extracted/api_server.ts:233`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments/:id/analytics`
   - Function: `app_get_250`
   - File: `Gen-H/.extracted/api_server.ts:250`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns`
   - Function: `app_post_70`
   - File: `Gen-H/.extracted/lead_gen_api.ts:70`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns`
   - Function: `app_get_96`
   - File: `Gen-H/.extracted/lead_gen_api.ts:96`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns/:id/start`
   - Function: `app_post_117`
   - File: `Gen-H/.extracted/lead_gen_api.ts:117`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:campaign_id/leads`
   - Function: `app_get_141`
   - File: `Gen-H/.extracted/lead_gen_api.ts:141`
   - Framework: express

⚪ 🔓 **PATCH** `/api/leads/:id`
   - Function: `app_patch_164`
   - File: `Gen-H/.extracted/lead_gen_api.ts:164`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:id/stats`
   - Function: `app_get_184`
   - File: `Gen-H/.extracted/lead_gen_api.ts:184`
   - Framework: express

⚪ 🔓 **GET** `/health`
   - Function: `app_get_492`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:492`
   - Framework: express

⚪ 🔓 **GET** `/api/system/config`
   - Function: `app_get_496`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:496`
   - Framework: express

⚪ 🔓 **POST** `/api/system/readiness`
   - Function: `app_post_510`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:510`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history`
   - Function: `app_get_527`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:527`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history/:file`
   - Function: `app_get_535`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:535`
   - Framework: express

⚪ 🔓 **GET** `/api/system/history/:file/download`
   - Function: `app_get_548`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:548`
   - Framework: express

⚪ 🔓 **POST** `/api/system/profile`
   - Function: `app_post_560`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:560`
   - Framework: express

⚪ 🔓 **POST** `/api/system/dry-run`
   - Function: `app_post_572`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:572`
   - Framework: express

⚪ 🔓 **POST** `/api/system/run`
   - Function: `app_post_584`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:584`
   - Framework: express

⚪ 🔓 **POST** `/api/system/promote`
   - Function: `app_post_596`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:596`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns`
   - Function: `app_post_719`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:719`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns`
   - Function: `app_get_744`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:744`
   - Framework: express

⚪ 🔓 **POST** `/api/campaigns/:id/start`
   - Function: `app_post_764`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:764`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:campaign_id/leads`
   - Function: `app_get_782`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:782`
   - Framework: express

⚪ 🔓 **PATCH** `/api/leads/:id`
   - Function: `app_patch_804`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:804`
   - Framework: express

⚪ 🔓 **GET** `/api/campaigns/:id/stats`
   - Function: `app_get_823`
   - File: `Gen-H/hvac-lead-generator/api/server.ts:823`
   - Framework: express

⚪ 🔓 **GET** `/health`
   - Function: `app_get_22`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:22`
   - Framework: express

⚪ 🔓 **GET** `/api/templates`
   - Function: `app_get_26`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:26`
   - Framework: express

⚪ 🔓 **GET** `/api/templates/:id`
   - Function: `app_get_49`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:49`
   - Framework: express

⚪ 🔓 **POST** `/api/templates`
   - Function: `app_post_64`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:64`
   - Framework: express

⚪ 🔓 **GET** `/api/companies`
   - Function: `app_get_119`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:119`
   - Framework: express

⚪ 🔓 **POST** `/api/companies`
   - Function: `app_post_128`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:128`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments`
   - Function: `app_get_145`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:145`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments`
   - Function: `app_post_172`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:172`
   - Framework: express

⚪ 🔓 **PATCH** `/api/deployments/:id/customize`
   - Function: `app_patch_190`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:190`
   - Framework: express

⚪ 🔓 **POST** `/api/deployments/:id/deploy`
   - Function: `app_post_209`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:209`
   - Framework: express

⚪ 🔓 **POST** `/api/analytics/:deployment_id`
   - Function: `app_post_227`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:227`
   - Framework: express

⚪ 🔓 **GET** `/api/deployments/:id/analytics`
   - Function: `app_get_244`
   - File: `Gen-H/hvac-template-library/api-gateway/server.ts:244`
   - Framework: express

### Money

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `Money/main.py:292`
   - Framework: fastapi

⚪ 🔓 **POST** `/dispatch`
   - Function: `dispatch`
   - File: `Money/main.py:309`
   - Framework: fastapi
   - Parameters: payload, background_tasks, x_api_key

⚪ 🔓 **GET** `/run/{run_id}`
   - Function: `get_run`
   - File: `Money/main.py:347`
   - Framework: fastapi
   - Parameters: run_id, x_api_key

⚪ 🔓 **GET** `/dispatches`
   - Function: `list_dispatches`
   - File: `Money/main.py:370`
   - Framework: fastapi
   - Parameters: limit, x_api_key

⚪ 🔓 **GET** `/api/dispatch/{dispatch_id}/timeline`
   - Function: `get_dispatch_timeline`
   - File: `Money/main.py:378`
   - Framework: fastapi
   - Parameters: dispatch_id, x_api_key

⚪ 🔓 **GET** `/api/dispatch/funnel`
   - Function: `get_dispatch_funnel`
   - File: `Money/main.py:404`
   - Framework: fastapi
   - Parameters: x_api_key

⚪ 🔓 **POST** `/sms`
   - Function: `sms_webhook`
   - File: `Money/main.py:436`
   - Framework: fastapi
   - Parameters: background_tasks, From, Body, MessageSid, To

⚪ 🔓 **POST** `/whatsapp`
   - Function: `whatsapp_webhook`
   - File: `Money/main.py:498`
   - Framework: fastapi
   - Parameters: background_tasks, From, Body, MessageSid, To

⚪ 🔓 **GET** `/login`
   - Function: `login_page`
   - File: `Money/main.py:562`
   - Framework: fastapi

⚪ 🔓 **POST** `/login`
   - Function: `login_submit`
   - File: `Money/main.py:569`
   - Framework: fastapi
   - Parameters: username, password

⚪ 🔓 **GET** `/logout`
   - Function: `logout`
   - File: `Money/main.py:585`
   - Framework: fastapi

⚪ 🔓 **GET** `/legacy-admin`
   - Function: `admin_dashboard`
   - File: `Money/main.py:592`
   - Framework: fastapi

⚪ 🔓 **GET** `/integrations/status`
   - Function: `integrations_status`
   - File: `Money/main.py:628`
   - Framework: fastapi
   - Parameters: x_api_key

⚪ 🔓 **POST** `/webhooks/make/sales-lead`
   - Function: `make_webhook_sales_lead`
   - File: `Money/main.py:648`
   - Framework: fastapi
   - Parameters: background_tasks, x_webhook_timestamp, x_webhook_signature

⚪ 🔓 **POST** `/webhooks/hubspot/contact-updated`
   - Function: `hubspot_webhook_contact_updated`
   - File: `Money/main.py:716`
   - Framework: fastapi
   - Parameters: x_hubspot_signature

⚪ 🔓 **GET** `/`
   - Function: `serve_index`
   - File: `Money/main.py:741`
   - Framework: fastapi

⚪ 🔓 **POST** `/sales-intelligence/lead`
   - Function: `receive_sales_lead`
   - File: `Money/integrations/sales_intelligence.py:403`
   - Framework: fastapi
   - Parameters: lead_data, x_api_key

⚪ 🔓 **GET** `/sales-intelligence/status`
   - Function: `sales_intel_status`
   - File: `Money/integrations/sales_intelligence.py:431`
   - Framework: fastapi

### citadel_ultimate_a_plus

⚪ 🔓 **GET** `/health`
   - Function: `health`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:100`
   - Framework: fastapi

⚪ 🔓 **GET** `/`
   - Function: `index`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:109`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/funnel`
   - Function: `api_funnel`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:235`
   - Framework: fastapi
   - Parameters: _

⚪ 🔓 **GET** `/api/verticals`
   - Function: `api_verticals`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:241`
   - Framework: fastapi
   - Parameters: _

⚪ 🔓 **GET** `/api/leads`
   - Function: `api_leads`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:247`
   - Framework: fastapi
   - Parameters: limit, _

⚪ 🔓 **GET** `/api/economics`
   - Function: `api_economics`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:253`
   - Framework: fastapi
   - Parameters: _

⚪ 🔓 **GET** `/api/beat-compliance`
   - Function: `api_beat_compliance`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:259`
   - Framework: fastapi
   - Parameters: _

⚪ 🔓 **GET** `/api/lead/{lead_slug}/timeline`
   - Function: `api_timeline`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:265`
   - Framework: fastapi
   - Parameters: lead_slug, _

⚪ 🔓 **POST** `/api/webhooks/openclaw`
   - Function: `webhook_openclaw`
   - File: `citadel_ultimate_a_plus/dashboard_app.py:274`
   - Framework: fastapi
   - Parameters: x_citadel_timestamp, x_citadel_signature

### intelligent-storage

⚪ 🔓 **GET** `/`
   - Function: `root`
   - File: `intelligent-storage/web_ui.py:43`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/stats`
   - Function: `get_stats`
   - File: `intelligent-storage/web_ui.py:225`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/files`
   - Function: `get_files`
   - File: `intelligent-storage/web_ui.py:258`
   - Framework: fastapi
   - Parameters: q, category, page, limit

⚪ 🔓 **GET** `/`
   - Function: `root`
   - File: `intelligent-storage/api_server.py:156`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/search/advanced`
   - Function: `advanced_search`
   - File: `intelligent-storage/api_server.py:892`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/search/v2`
   - Function: `rrf_search`
   - File: `intelligent-storage/api_server.py:1108`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/chat`
   - Function: `chat_endpoint`
   - File: `intelligent-storage/api_server.py:1352`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/search/semantic`
   - Function: `semantic_search`
   - File: `intelligent-storage/api_server.py:1368`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/search/faceted`
   - Function: `faceted_search`
   - File: `intelligent-storage/api_server.py:1424`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/files/{file_id}`
   - Function: `get_file_details`
   - File: `intelligent-storage/api_server.py:1478`
   - Framework: fastapi
   - Parameters: file_id

⚪ 🔓 **POST** `/api/tot/reason`
   - Function: `tree_of_thoughts_reasoning`
   - File: `intelligent-storage/api_server.py:1564`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/graph/query`
   - Function: `query_knowledge_graph`
   - File: `intelligent-storage/api_server.py:1630`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/graph/status`
   - Function: `get_graph_status`
   - File: `intelligent-storage/api_server.py:1687`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/graph/pagerank`
   - Function: `get_pagerank`
   - File: `intelligent-storage/api_server.py:1701`
   - Framework: fastapi
   - Parameters: limit

⚪ 🔓 **GET** `/api/graph/communities`
   - Function: `get_communities`
   - File: `intelligent-storage/api_server.py:1721`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/graph/path`
   - Function: `get_shortest_path`
   - File: `intelligent-storage/api_server.py:1741`
   - Framework: fastapi
   - Parameters: from_id, to_id

⚪ 🔓 **POST** `/api/insights`
   - Function: `get_insights`
   - File: `intelligent-storage/api_server.py:1779`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/recommendations`
   - Function: `get_recommendations`
   - File: `intelligent-storage/api_server.py:1823`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/dashboard`
   - Function: `get_dashboard_stats`
   - File: `intelligent-storage/api_server.py:1862`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/files`
   - Function: `list_files`
   - File: `intelligent-storage/api_server.py:1937`
   - Framework: fastapi
   - Parameters: page, limit, extension, q, category, sort_by

⚪ 🔓 **GET** `/api/files/{file_id}/content`
   - Function: `get_file_content`
   - File: `intelligent-storage/api_server.py:2007`
   - Framework: fastapi
   - Parameters: file_id

⚪ 🔓 **POST** `/api/files/{file_id}/tags`
   - Function: `update_file_tags`
   - File: `intelligent-storage/api_server.py:2029`
   - Framework: fastapi
   - Parameters: file_id

⚪ 🔓 **GET** `/export/{export_type}`
   - Function: `export_data`
   - File: `intelligent-storage/api_server.py:2066`
   - Framework: fastapi
   - Parameters: export_type, query, format

⚪ 🔓 **GET** `/api/optimization/status`
   - Function: `get_optimization_status`
   - File: `intelligent-storage/api_server.py:2184`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/optimization/index`
   - Function: `index_embeddings_for_optimization`
   - File: `intelligent-storage/api_server.py:2228`
   - Framework: fastapi
   - Parameters: file_ids

⚪ 🔓 **POST** `/api/optimization/benchmark`
   - Function: `run_optimization_benchmark`
   - File: `intelligent-storage/api_server.py:2289`
   - Framework: fastapi
   - Parameters: n_files

⚪ 🔓 **GET** `/api/health`
   - Function: `health_check`
   - File: `intelligent-storage/api_server.py:2335`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/duplicates`
   - Function: `get_duplicates`
   - File: `intelligent-storage/api_server.py:2422`
   - Framework: fastapi
   - Parameters: type, threshold, limit

⚪ 🔓 **POST** `/api/search/natural`
   - Function: `natural_language_search`
   - File: `intelligent-storage/api_server.py:2524`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/control/index`
   - Function: `trigger_indexing`
   - File: `intelligent-storage/api_server.py:2939`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/control/clear-db`
   - Function: `clear_database`
   - File: `intelligent-storage/api_server.py:2974`
   - Framework: fastapi

⚪ 🔓 **GET** `/api/control/stats`
   - Function: `get_system_stats`
   - File: `intelligent-storage/api_server.py:2985`
   - Framework: fastapi

⚪ 🔓 **POST** `/api/control/progress/{operation_id}`
   - Function: `report_progress`
   - File: `intelligent-storage/api_server.py:3025`
   - Framework: fastapi
   - Parameters: operation_id, report

⚪ 🔓 **POST** `/api/control/stop/{operation_id}`
   - Function: `stop_operation`
   - File: `intelligent-storage/api_server.py:3048`
   - Framework: fastapi
   - Parameters: operation_id

⚪ 🔓 **POST** `/api/control/pause/{operation_id}`
   - Function: `pause_operation_endpoint`
   - File: `intelligent-storage/api_server.py:3077`
   - Framework: fastapi
   - Parameters: operation_id

⚪ 🔓 **POST** `/api/control/resume/{operation_id}`
   - Function: `resume_operation_endpoint`
   - File: `intelligent-storage/api_server.py:3091`
   - Framework: fastapi
   - Parameters: operation_id

