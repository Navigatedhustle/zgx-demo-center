# Architecture

HTML catalog → shared Python installation plans and launcher utilities → independent demo apps/containers. The repository stays a suite because loader plans and common path utilities couple the included examples. Individual applications retain their original source subdirectories.

## Implemented endpoints inspected from source

| Method | Route | Source |
| --- | --- | --- |
| GET | `/status/{demo_id}` | `demo_install_server.py` |
| GET | `/install/{demo_id}` | `demo_install_server.py` |
| GET | `/launch/{demo_id}` | `demo_install_server.py` |
| GET | `/port_check/{port}` | `demo_install_server.py` |
| GET | `/health_check/{demo_id}` | `demo_install_server.py` |
| GET | `/robot_check` | `demo_install_server.py` |
| GET | `/bench_status` | `demo_install_server.py` |
| POST | `/ollama_release` | `demo_install_server.py` |
| POST | `/exit_kiosk` | `demo_install_server.py` |
| POST | `/bench_stop` | `demo_install_server.py` |
| GET | `/running` | `demo_install_server.py` |
| POST | `/stop/{demo_id}` | `demo_install_server.py` |
| GET | `/start/{demo_id}` | `demo_install_server.py` |
| GET | `/load_time/{demo_id}` | `demo_install_server.py` |
| GET | `/load_times` | `demo_install_server.py` |
| GET | `/health` | `demo_install_server.py` |
| GET | `/` | `pipeline-pulse/pipeline_pulse_v6.py` |
| GET | `/api/status` | `pipeline-pulse/pipeline_pulse_v6.py` |
| GET | `/api/reset` | `pipeline-pulse/pipeline_pulse_v6.py` |
| POST | `/api/inference` | `pipeline-pulse/pipeline_pulse_v6.py` |
| WEBSOCKET | `/ws/telemetry` | `pipeline-pulse/pipeline_pulse_v6.py` |
| GET | `/` | `ai-vision/vision_demo.py` |
| GET | `/api/scenarios` | `ai-vision/vision_demo.py` |
| POST | `/api/scenario/{scenario_id}` | `ai-vision/vision_demo.py` |
| GET | `/api/status` | `ai-vision/vision_demo.py` |
| WEBSOCKET | `/ws/frames` | `ai-vision/vision_demo.py` |
| WEBSOCKET | `/ws` | `ai-vision/vision_demo.py` |
| POST | `/api/alert` | `ai-vision/vision_demo.py` |
| GET | `/api/alerts/history` | `ai-vision/vision_demo.py` |
| GET | `/` | `document-translation/backend/main.py` |
| POST | `/load_models` | `document-translation/backend/main.py` |
| POST | `/translate` | `document-translation/backend/main.py` |
| GET | `/language_pairs` | `document-translation/backend/main.py` |
| GET | `/` | `Fed-Navy-containerized-docker/backend/main.py` |
| GET | `/api/health` | `Fed-Navy-containerized-docker/backend/main.py` |
| GET | `/api/regions` | `Fed-Navy-containerized-docker/backend/main.py` |
| POST | `/api/analyze` | `Fed-Navy-containerized-docker/backend/main.py` |
| GET | `/` | `pii-demo-containerized-docker/backend/main.py` |
| GET | `/load_models` | `pii-demo-containerized-docker/backend/main.py` |
| POST | `/mask_pii` | `pii-demo-containerized-docker/backend/main.py` |
| POST | `/test_offline` | `pii-demo-containerized-docker/backend/main.py` |
| GET | `/` | `pii-demo-containerized-docker/backend/main_ollama.py` |
| GET | `/load_models` | `pii-demo-containerized-docker/backend/main_ollama.py` |
| POST | `/mask_pii` | `pii-demo-containerized-docker/backend/main_ollama.py` |
| POST | `/test_offline` | `pii-demo-containerized-docker/backend/main_ollama.py` |
| GET | `/` | `AEC-construction-safety/backend/main.py` |
| POST | `/ask` | `AEC-construction-safety/backend/main.py` |
| GET | `/` | `healthcare-pharmacy-containerized-docker/backend/main.py` |
| POST | `/api/simple_interaction` | `healthcare-pharmacy-containerized-docker/backend/main.py` |
| POST | `/api/complex_interaction` | `healthcare-pharmacy-containerized-docker/backend/main.py` |
| GET | `/api/health` | `healthcare-pharmacy-containerized-docker/backend/main.py` |
| GET | `/api/sample_queries` | `healthcare-pharmacy-containerized-docker/backend/main.py` |
| GET | `/health` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| POST | `/transcribe` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| POST | `/generate` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| POST | `/speak` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| POST | `/process` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| GET | `/conversations` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |
| POST | `/reset` | `Robotic-medical-AI-assistant/docker/zgx_ai_api.py` |

These routes establish implementation shape. They do not establish successful provider integration or model quality. Generated state and data stores are excluded from the repository.
