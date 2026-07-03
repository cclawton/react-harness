#!/bin/bash
# Run all 5 examples x 2 models = 10 runs, collect results
cd ~/Hacking/react-harness

GOALS_DIR="examples"
RESULTS_FILE="runs/comparison_results.csv"
echo "example,model,status,turns,cost,duration_s,verifier_passed,verifier_confidence" > "$RESULTS_FILE"

run_example() {
  local example=$1
  local model=$2
  local workdir=$3
  local goal=$4
  local label="${example}_${model##*/}"

  echo "============================================"
  echo "RUNNING: ${label}"
  echo "============================================"

  python main.py \
    --actor-model "$model" \
    --verifier-model "$model" \
    --goal "$goal" \
    --workdir "$workdir" \
    --max-turns 30 2>&1 | tee "/tmp/run_${label}.log"

  # Extract the result line
  local result=$(grep "RESULT:" "/tmp/run_${label}.log" 2>/dev/null | head -1)
  echo "RESULT LINE: $result"
}

# --- GLM runs ---
echo "########## GLM-5.2 RUNS ##########"

run_example "csv_normalizer" "z-ai/glm-5.2" "examples/csv_normalizer_glm" \
  "Read test_normalize.py to understand the expected behaviour, then write normalize.py that passes all tests. Run tests to verify. Do NOT modify test_normalize.py."

run_example "recursive_parser" "z-ai/glm-5.2" "examples/recursive_parser_glm" \
  "Read test_parser.py to understand the expected behaviour, then create parser.py implementing parse_json and ParseError. Run tests to verify. Do NOT modify test_parser.py."

run_example "broken_api_client" "z-ai/glm-5.2" "examples/broken_api_client_glm" \
  "Fix all bugs in client.py so that all tests in test_client.py pass. Read the code and tests first. Do NOT modify test_client.py."

run_example "markdown_converter" "z-ai/glm-5.2" "examples/markdown_converter_glm" \
  "Read test_converter.py carefully, then create tokenizer.py, parser.py, renderer.py, and converter.py to pass all tests. Run tests to verify. Do NOT modify test_converter.py."

run_example "pipeline_debug" "z-ai/glm-5.2" "examples/pipeline_debug_glm" \
  "Read test_pipeline.py carefully, then create filter.py, enrich.py, aggregate.py, report.py, and pipeline.py to pass all tests. Run tests to verify. Do NOT modify test_pipeline.py."

# --- Opus runs ---
echo "########## OPUS-4.8 RUNS ##########"

run_example "csv_normalizer" "anthropic/claude-opus-4.8" "examples/csv_normalizer_opus" \
  "Read test_normalize.py to understand the expected behaviour, then write normalize.py that passes all tests. Run tests to verify. Do NOT modify test_normalize.py."

run_example "recursive_parser" "anthropic/claude-opus-4.8" "examples/recursive_parser_opus" \
  "Read test_parser.py to understand the expected behaviour, then create parser.py implementing parse_json and ParseError. Run tests to verify. Do NOT modify test_parser.py."

run_example "broken_api_client" "anthropic/claude-opus-4.8" "examples/broken_api_client_opus" \
  "Fix all bugs in client.py so that all tests in test_client.py pass. Read the code and tests first. Do NOT modify test_client.py."

run_example "markdown_converter" "anthropic/claude-opus-4.8" "examples/markdown_converter_opus" \
  "Read test_converter.py carefully, then create tokenizer.py, parser.py, renderer.py, and converter.py to pass all tests. Run tests to verify. Do NOT modify test_converter.py."

run_example "pipeline_debug" "anthropic/claude-opus-4.8" "examples/pipeline_debug_opus" \
  "Read test_pipeline.py carefully, then create filter.py, enrich.py, aggregate.py, report.py, and pipeline.py to pass all tests. Run tests to verify. Do NOT modify test_pipeline.py."

echo ""
echo "============================================"
echo "ALL RUNS COMPLETE"
echo "============================================"
echo ""
echo "Run records in runs/*.json"
echo "Logs in /tmp/run_*.log"
