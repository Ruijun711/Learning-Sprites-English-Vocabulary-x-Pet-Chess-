"""用本機的開源模型（Ollama）替每個單字產生例句與繁體中文翻譯。

流程：讀單字表 → 每個字請模型寫一批候選例句 → 程式自動檢查 → 留下通過的前 N 句 → 寫進 CSV，給組員人工檢查。
不夠 N 句時會再請模型多寫幾次；還是不夠就標記「不足」，之後用 Tatoeba 或自己寫補。

事前準備：
  1. 安裝 Ollama（https://ollama.com），下載模型，例如：ollama pull qwen2.5:7b
  2. （建議）pip install opencc-python-reimplemented，把簡體字轉成繁體

用法：
  先試 10 個字，比較不同模型：
    python tools/generate_sentences.py --model qwen2.5:7b --limit 10
    python tools/generate_sentences.py --model gemma2:9b --limit 10
  正式產生全部：
    python tools/generate_sentences.py --model qwen2.5:7b --words 字表.csv

單字表 CSV 欄位：word, pos, zh, category（可參考 tools/sample_words.csv）。
輸出預設在 tools/output/sentences_<模型名稱>.csv；中途停掉再執行會從沒做完的字接著做。
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 一次請模型多寫幾句，留一些空間給檢查淘汰
CANDIDATES_PER_CALL = 8
MAX_ATTEMPTS = 3
MIN_WORDS, MAX_WORDS = 4, 14

SCHEMA = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"en": {"type": "string"}, "zh": {"type": "string"}},
                "required": ["en", "zh"],
            },
        }
    },
    "required": ["sentences"],
}

PROMPT = """Write {n} different English example sentences for the word "{word}".

Rules:
- Use "{word}" with this meaning only: {zh} ({pos}).
- Use the exact form "{word}" exactly once in each sentence. Do not change its form (no plural, no -s, -ed, -ing).
- Use only very simple, common words that elementary school students know (CEFR A1-A2).
- Each sentence is {min_w}-{max_w} words long and ends with a period, question mark or exclamation mark.
- The sentence context must make the meaning of "{word}" clear, so a learner could guess the word if it were blank.
- Every sentence must be different in topic and structure. Content must be suitable for children.
- Give a natural Traditional Chinese (Taiwan) translation for each sentence in "zh".

Return JSON only."""


def load_opencc():
    try:
        import opencc
    except ImportError:
        print("提醒：沒有安裝 OpenCC，中文翻譯不會轉成繁體。安裝：pip install opencc-python-reimplemented", file=sys.stderr)
        return lambda s: s
    try:
        conv = opencc.OpenCC("s2twp")
    except Exception:
        conv = opencc.OpenCC("s2twp.json")
    return conv.convert


def ask_model(host, model, word, temperature):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT.format(
            n=CANDIDATES_PER_CALL, word=word["word"], zh=word["zh"], pos=word["pos"],
            min_w=MIN_WORDS, max_w=MAX_WORDS)}],
        "format": SCHEMA,
        "stream": False,
        "options": {"temperature": temperature},
    }
    req = urllib.request.Request(
        f"{host}/api/chat", data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        content = json.loads(resp.read().decode("utf-8"))["message"]["content"]
    try:
        items = json.loads(content).get("sentences", [])
    except json.JSONDecodeError:
        return []
    return [i for i in items if isinstance(i, dict)]


def check(en, zh, word, seen):
    """回傳不合格的原因；合格回傳 None。"""
    en, zh = en.strip(), zh.strip()
    if not en or not zh:
        return "空白"
    hits = re.findall(rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])", en, flags=re.IGNORECASE)
    if len(hits) == 0:
        return "目標字沒出現或不是原形"
    if len(hits) > 1:
        return "目標字出現不只一次"
    n = len(re.findall(r"[A-Za-z']+", en))
    if not MIN_WORDS <= n <= MAX_WORDS:
        return f"長度 {n} 字"
    if en[-1] not in ".?!":
        return "沒有結尾標點"
    if re.search(r"[A-Za-z]{3,}", zh):
        return "翻譯含英文"
    if en.lower() in seen:
        return "重複"
    return None


def main():
    ap = argparse.ArgumentParser(description="用 Ollama 本機模型產生例句")
    ap.add_argument("--model", required=True, help="Ollama 模型名稱，例如 qwen2.5:7b")
    ap.add_argument("--words", default=str(HERE / "sample_words.csv"), help="單字表 CSV")
    ap.add_argument("--out", help="輸出 CSV（預設 tools/output/sentences_<模型>.csv）")
    ap.add_argument("--per-word", type=int, default=5, help="每個字要幾句（預設 5）")
    ap.add_argument("--limit", type=int, help="只做前幾個字，用來試模型")
    ap.add_argument("--temperature", type=float, default=0.8, help="越高句子越多樣（預設 0.8）")
    ap.add_argument("--host", default="http://localhost:11434", help="Ollama 位址")
    args = ap.parse_args()

    with open(args.words, encoding="utf-8-sig", newline="") as f:
        words = [r for r in csv.DictReader(f) if r.get("word", "").strip()]
    if args.limit:
        words = words[: args.limit]

    out = Path(args.out) if args.out else HERE / "output" / f"sentences_{re.sub(r'[^A-Za-z0-9.-]+', '_', args.model)}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        with open(out, encoding="utf-8-sig", newline="") as f:
            done = {r["word"] for r in csv.DictReader(f)}
    fields = ["word", "pos", "zh_meaning", "category", "no", "sentence", "translation",
              "source", "model", "status", "review"]
    new_file = not out.exists()
    to_trad = load_opencc()

    todo = [w for w in words if w["word"] not in done]
    print(f"模型 {args.model}：共 {len(words)} 字，已完成 {len(words) - len(todo)}，這次要做 {len(todo)}。輸出：{out}")

    with open(out, "a", encoding="utf-8-sig" if new_file else "utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            writer.writeheader()
        for i, w in enumerate(todo, 1):
            word = w["word"].strip()
            kept, seen, rejected = [], set(), {}
            start = time.time()
            for _ in range(MAX_ATTEMPTS):
                try:
                    items = ask_model(args.host, args.model, w, args.temperature)
                except urllib.error.URLError as e:
                    sys.exit(f"連不到 Ollama（{args.host}）：{e}。請確認 Ollama 已開啟，且已下載模型 {args.model}。")
                for it in items:
                    en = str(it.get("en", "")).strip()
                    zh = to_trad(str(it.get("zh", "")).strip())
                    reason = check(en, zh, word, seen)
                    if reason:
                        rejected[reason] = rejected.get(reason, 0) + 1
                        continue
                    seen.add(en.lower())
                    kept.append((en, zh))
                if len(kept) >= args.per_word:
                    break
            kept = kept[: args.per_word]
            status = "待檢查" if len(kept) == args.per_word else f"不足（{len(kept)}/{args.per_word}）"
            for n, (en, zh) in enumerate(kept, 1):
                writer.writerow({"word": word, "pos": w.get("pos", ""), "zh_meaning": w.get("zh", ""),
                                 "category": w.get("category", ""), "no": n, "sentence": en,
                                 "translation": zh, "source": "AI", "model": args.model,
                                 "status": status, "review": ""})
            if not kept:  # 一句都沒有也記一列，避免下次重跑時被當成沒做過而漏看
                writer.writerow({"word": word, "pos": w.get("pos", ""), "zh_meaning": w.get("zh", ""),
                                 "category": w.get("category", ""), "no": 0, "sentence": "",
                                 "translation": "", "source": "AI", "model": args.model,
                                 "status": status, "review": ""})
            f.flush()
            why = "、".join(f"{k}×{v}" for k, v in rejected.items()) or "無"
            print(f"[{i}/{len(todo)}] {word}: {len(kept)} 句，{time.time() - start:.0f} 秒；淘汰：{why}")

    print("完成。請用 Excel 打開輸出檔，在 review 欄填「OK」或「刪」，不足的字用 Tatoeba 或自己寫補。")


if __name__ == "__main__":
    main()
