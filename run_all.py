"""One-command project runner: download, validate, analyze, save outputs."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.download_data import download
from src.cookie_cat import load_and_validate, analyze, save_outputs

def main():
    data_path = ROOT / "data" / "raw" / "cookie_cats.csv"
    if not data_path.exists():
        data_path = download()
    df = load_and_validate(data_path)
    result = analyze(df)
    save_outputs(result, ROOT / "outputs")
    print(f"Analyzed {result['n_total']:,} players.")
    print(f"Day-7 retention: gate_30={result['retention_7']['gate_30']:.2%}; gate_40={result['retention_7']['gate_40']:.2%}")
    print(f"Difference gate_40 - gate_30: {result['retention_7']['difference_pp']:+.2f} pp")
    print(f"Two-sided z-test p-value: {result['retention_7']['p_value']:.6g}")
    print(f"Decision: {result['decision']['recommendation']}")
    print(f"Outputs: {ROOT / 'outputs'}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"RUN FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
