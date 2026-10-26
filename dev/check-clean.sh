#!/usr/bin/env bash
# 配る物に、社内の呼び名・人の名前・社員名・社内の記号・社内のパス・鍵・他社の測った値・成人向けが残っていないかを grep する。
# 使い方: bash dev/check-clean.sh   （1件でも当たれば exit 1）
cd "$(dirname "$0")/.."
PAT='工藤|岩本|みやび|miyabi|堂本|domoto|kudo|iwamoto|hirosa|篠原|shinohara|土橋|恋トレ|koitore|amai|aiko|裏垢|urakaki|otoko|男コーチング|Ghost|Aoi\b|Reel\b|Tetsu|Nick\b|Riku|Rojin|Gaku|Nagi|Shiori|Koyomi|Kaji|tc://|---DECIDE|---WAKE|HANDOFF|DISPATCH|trans-chat|transchat|tc-seats|ai-employees|workspaces/|/home/|auth\.db|TC_GEMINI|TC_XAI|nano-banana|x-engine|AKARI|vt\.mjs|transaij-video|Replicate|UTAGE|utage|XTEP|kudo-corpus|sozai|ttp-explainer|kudo-memo|sk-ant-|sk-proj-|AIza[0-9A-Za-z_-]{20}|xai-[0-9A-Za-z]{20}|ghp_[0-9A-Za-z]{20}|BMS|道銀|ai-advisors|fwh\.co|igpi'
FILES=$(git ls-files --cached --others --exclude-standard | grep -v '^dev/check-clean.sh$')
HITS=$(echo "$FILES" | tr '\n' '\0' | xargs -0 grep -nIE "$PAT" 2>/dev/null)
echo "調べたファイル: $(echo "$FILES" | wc -l) 件"
echo "調べた言葉: $PAT"
if [ -n "$HITS" ]; then echo "× 当たり:"; echo "$HITS"; exit 1; fi
echo "○ 当たり 0 件"
# 会社名（作者・ライセンス・URL）だけは出てよい。どこに出るかを並べる
echo "--- 作者として出る会社名（出てよい物）"
echo "$FILES" | tr '\n' '\0' | xargs -0 grep -nIo "TransAIJ[^\"]\{0,20\}" 2>/dev/null
exit 0
