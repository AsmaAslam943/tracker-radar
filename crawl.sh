node "$COLLECTOR_DIR/cli.js" \
  --input "$CRAWL_LIST" \
  --output "$OUTPUT_DIR" \
  --collectors requests,cookies,targets,apis \
  --reporters cli \
  --maxCollectionTimeMs 30000 \
  --workers 4 \
  2>&1 | tee -a "$LOG_FILE"
 
echo ""
echo "Finished: $(date)" | tee -a "$LOG_FILE"
COLLECTED=$(ls "$OUTPUT_DIR"/*.json 2>/dev/null | wc -l | tr -d ' ')
echo "✓ Collected $COLLECTED JSON result files"
echo ""
echo "Next step: run  python3 analysis/03_analyze.py"
 
# ── Cleanup temp file ─────────────────────────────────────────────────────────
[ -n "$TEST_N" ] && rm -f "$CRAWL_LIST"