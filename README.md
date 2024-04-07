# adaptive-pipeline-orchestration

**Brief Project Context:** ...

**Purpose of this Repository:**  Contains code and resources for orchestrating the overall adaptive model training pipeline.

**Key Technologies:**
*   Python
*   GCP Cloud Workflows (or your chosen orchestration tool)

**Getting Started**
...

**Usage/Examples**
*   (Describe how to trigger the pipeline, execution workflow)

**Tests**
*  (Explain if/how integration tests for the pipeline are implemented)

**Contributions**
...

**License**
...


Flow:
1. Start
	a. MSG: ADAPTIVE_PIPELINE_START (topic adaptive-pipeline-workflow)
	b. FUNCTION adaptive-pipeline-orchestrator: reads ADAPTIVE_PIPELINE message
	c. FUNCTION adaptive-pipeline-orchestrator: Generates new unique ID for a new pipeline, saves the requested model performance KPI
	b. FUNCTION adaptive-pipeline-orchestrator: MSG: GET_CONFIGURATION (topic adaptive-pipeline-config-topic)
2. Get configuration
	a. FUNCTION adaptive-pipeline-config:	reads GET_CONFIGURATION message
	b. FUNCTION adaptive-pipeline-config:	get previous config data (by layers qty) with preformance results
	c. FUNCTION adaptive-pipeline-config:	prepare prev configuration summary for the LLM module
	d. FUNCTION adaptive-pipeline-config:	MSG: GENERATE_NEW_LLM_CONFIGURATION (topic adaptive-pipeline-config-topic)
	e. FUNCTION adaptive-pipeline-llm:		reads GENERATE_NEW_LLM_CONFIGURATION message
	f. FUNCTION adaptive-pipeline-llm:		calls LLM, requesting a new configuration
	g. FUNCTION adaptive-pipeline-llm:		saves new configuration
	h. FUNCTION adaptive-pipeline-llm:		MSG: NEW_LLM_CONFIGURATION_READY (topic adaptive-pipeline-config-topic)	
3. Build model
	a. FUNCTION adaptive-pipeline-orchestrator:	reads NEW_LLM_CONFIGURATION_READY message
	b. FUNCTION adaptive-pipeline-orchestrator:	MSG: GENERATE_MODEL (topic adaptive-pipeline-model-topic)
	c. FUNCTION adaptive-pipeline-build-model:	reads GENERATE_MODEL message
	d. FUNCTION adaptive-pipeline-build-model:	creates a model based on a new configuration and saves it to the Cloud Storage
	e. FUNCTION adaptive-pipeline-build-model:	MSG: MODEL_READY (topic adaptive-pipeline-model-topic)
4. Prepare data
	a. FUNCTION adaptive-pipeline-orchestrator:		reads MODEL_READY message
	b. FUNCTION adaptive-pipeline-orchestrator:		MSG: PREPARE_FEATURES (topic adaptive-pipeline-features-topic)
	c. FUNCTION adaptive-pipeline-prepare-features:	prepares features - training, testing sets, normalizes and saves it to the Cloud Storage
	d. FUNCTION adaptive-pipeline-prepare-features:	MSG: FEATURES_READY (topic adaptive-pipeline-features-topic)
5. Train data, predict, and evaluate
	a. FUNCTION adaptive-pipeline-orchestrator:					reads FEATURES_READY message
	b. FUNCTION adaptive-pipeline-orchestrator:					MSG: RUN_MODEL (topic adaptive-pipeline-predict-topic)
	c. Cloud Run or Cloud FUNCTION: adaptive-pipeline-predict:	load model and features
	d. Cloud Run or Cloud FUNCTION: adaptive-pipeline-predict:	trains and predicts model
	e. Cloud Run or Cloud FUNCTION: adaptive-pipeline-predict:	evaluates model
	f. Cloud Run or Cloud FUNCTION: adaptive-pipeline-predict:	saves results
	d. Cloud Run or Cloud FUNCTION: adaptive-pipeline-predict:	MSG: PREDICTION_READY (adaptive-pipeline-predict-topic)
6. Results review step
	a. FUNCTION adaptive-pipeline-orchestrator:	reads PREDICTION_READY message
	b. FUNCTION adaptive-pipeline-orchestrator:	decides if the model performance satisfies the requested performance KPI
		ba. FUNCTION adaptive-pipeline-orchestrator:	if performance is poor - MSG: GET_CONFIGURATION (topic adaptive-pipeline-config-topic)
		OR
		bb. FUNCTION adaptive-pipeline-orchestrator:	if performance is OK - Generates notification that the prediction pipeline is fininshed