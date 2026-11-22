"""Execute each chapter in a fresh in-process IPython kernel and save its outputs."""

import argparse
import json
from math import isclose
from pathlib import Path
from statistics import median
import subprocess
import sys
from time import perf_counter

import nbformat
from IPython.utils.capture import capture_output
from ipykernel.inprocess.manager import InProcessKernelManager


def run_notebook(path):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    manager = InProcessKernelManager()
    manager.start_kernel()
    try:
        shell = manager.kernel.shell
        shell.run_line_magic("matplotlib", "inline")
        for index, cell in enumerate(
            (cell for cell in notebook.cells if cell.cell_type == "code"), start=1
        ):
            with capture_output() as captured:
                result = shell.run_cell(cell.source, store_history=True)
            if not result.success:
                print(captured.stdout, file=sys.stderr)
                result.raise_error()
            cell.execution_count = index
            cell.outputs = []
            for name in ("stdout", "stderr"):
                content = getattr(captured, name)
                if content:
                    cell.outputs.append(nbformat.v4.new_output("stream", name=name, text=content))
            for display in captured.outputs:
                cell.outputs.append(
                    nbformat.v4.new_output("display_data", data=display.data, metadata=display.metadata)
                )
        nbformat.validate(notebook)
        nbformat.write(notebook, path)
    finally:
        manager.shutdown_kernel()


def write_foundation_numbers(quality):
    """Regenerate the first three chapters' tables and verify their connection to Chapter 4."""
    bo, probability, kernel, posterior = (
        json.loads((quality / f"ch{index:02d}_metrics.json").read_text(encoding="utf-8"))
        for index in (1, 2, 3, 4)
    )
    first = (
        f"この実行で最初に選んだのは **{bo['first_temperature_c']:.0f} °C** です。"
        f"この温度での実行結果は **{bo['first_observed_mpa']:.2f} MPa** でした。\n"
    )
    (quality / "ch01-first.qmd").write_text(first, encoding="utf-8")
    comparison = [
        "| 方法 | 累計評価回数 | 最良観測値 [MPa] | 温度 [°C] | 最大値との差 [MPa] |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, row in bo["results"].items():
        comparison.append(
            f"| {name} | {row['evaluation_count']} | {row['best_mpa']:.2f} "
            f"| {row['best_temperature_c']:.0f} | {bo['best_possible_mpa'] - row['best_mpa']:.2f} |"
        )
    best = max(row["best_mpa"] for row in bo["results"].values())
    leaders = "・".join(name for name, row in bo["results"].items()
                       if isclose(row["best_mpa"], best, rel_tol=0.0, abs_tol=1e-10))
    comparison.extend([
        "",
        f"全41候補の最大は **{bo['best_possible_mpa']:.2f} MPa** です。"
        f"この実行で最良観測値が最も高かった方法は **{leaders}** です。",
    ])
    (quality / "ch01-results.qmd").write_text("\n".join(comparison) + "\n", encoding="utf-8")

    updates = [
        "| 使用した観測数 | 未知の平均強度の分布の平均 [MPa] | 同じ分布の標準偏差 [MPa] |",
        "|---:|---:|---:|",
    ]
    for row in probability["posterior_updates"]:
        updates.append(
            f"| {row['observations']} | {row['mean_mpa']:.3f} | {row['sd_mpa']:.3f} |"
        )
    (quality / "ch02-updating.qmd").write_text("\n".join(updates) + "\n", encoding="utf-8")
    posterior_sd = probability["posterior_updates"][-1]["sd_mpa"]
    prediction = (
        f"未知の平均の事後標準偏差は **{posterior_sd:.3f} MPa**、"
        f"新しい測定値の予測標準偏差は **{probability['new_measurement_sd_mpa']:.3f} MPa** です。"
        "次の測定の誤差を加えるため、予測分布の方が広くなります。\n"
    )
    (quality / "ch02-prediction.qmd").write_text(prediction, encoding="utf-8")

    conditional = (
        f"右図では、$V$ の平均が75から **{probability['conditional_mean_mpa']:.2f} MPa**、"
        f"標準偏差が5から **{probability['conditional_sd_mpa']:.2f} MPa** に変わりました。"
        "条件付き密度の式を、同時密度を周辺密度で割る計算と照合しています。\n"
    )
    (quality / "ch02-conditional.qmd").write_text(conditional, encoding="utf-8")

    if kernel["fixed_input_order"] != posterior["fixed_input_order"]:
        raise ValueError("Chapters 3 and 4 must use the same input order for the worked example.")
    left = kernel["fixed_prior_covariance"]
    right = posterior["fixed_prior_covariance"]
    difference = max(abs(a - b) for row_l, row_r in zip(left, right) for a, b in zip(row_l, row_r))
    if difference > 1e-10:
        raise ValueError("The Chapter 3 prior does not match the prior used for Chapter 4 conditioning.")

    bridge = (
        "Notebookで作った4行4列の行列を、第4章の二点の検算に使う事前共分散と照合しました。"
        f"この実行での最大絶対差は {difference:.2g} です。\n"
    )
    (quality / "ch03-connection.qmd").write_text(bridge, encoding="utf-8")


def write_book_numbers(quality):
    """Keep the displayed book numbers in sync with the executed notebooks."""
    gp = json.loads((quality / "ch04_metrics.json").read_text(encoding="utf-8"))
    mean = gp["fixed_mean"]
    cov = gp["fixed_covariance"]
    gp_text = (
        f"事後平均は $({mean[0]:.4f}, {mean[1]:.4f})^{{\\mathsf T}}$、"
        f"事後共分散の対角成分はともに {cov[0][0]:.4f}、"
        f"非対角成分はともに {cov[0][1]:.4f} でした。"
        "非対角成分には二つの未知点の依存関係が残ります。"
        f"倍精度で手計算の式と公開APIを比較した最大絶対差は、"
        f"この実行で平均 {gp['fixed_mean_max_abs_error']:.2g}、"
        f"共分散 {gp['fixed_covariance_max_abs_error']:.2g} でした。\n"
    )
    (quality / "ch04-numbers.qmd").write_text(gp_text, encoding="utf-8")

    acq = json.loads((quality / "ch05_metrics.json").read_text(encoding="utf-8"))

    shared_keys = (
        "prediction_grid_midpoint_mean_mpa",
        "prediction_grid_midpoint_latent_sd_mpa",
    )
    if gp["observations_mpa"] != acq["observations_mpa"]:
        raise ValueError("The chapters must use identical material observations.")
    if not all(isclose(gp[key], acq[key], abs_tol=1e-10, rel_tol=0.0) for key in shared_keys):
        raise ValueError("The posterior at x = 0.50 differs between the two chapters.")

    mean_mid, latent_sd = (gp[key] for key in shared_keys)
    measurement_sd = gp["prediction_grid_midpoint_measurement_sd_mpa"]
    midpoint_lines = [
        f"この温度での事後平均は、どちらも **{mean_mid:.2f} MPa** です。",
        "",
        "| 予測する量 | 標準偏差 [MPa] | 点ごとの約95%区間 [MPa] |",
        "|---|---:|---:|",
    ]
    for name, sd in (("潜在強度", latent_sd), ("新しい1回の測定値", measurement_sd)):
        lower = mean_mid - 1.96 * sd
        upper = mean_mid + 1.96 * sd
        midpoint_lines.append(f"| {name} | {sd:.2f} | {lower:.2f} ～ {upper:.2f} |")
    (quality / "ch04-midpoint.qmd").write_text("\n".join(midpoint_lines) + "\n", encoding="utf-8")

    shared = (
        f"正規化温度 $x=0.50$（160 °C）の潜在強度は、事後平均 **{mean_mid:.2f} MPa**、"
        f"標準偏差 **{latent_sd:.2f} MPa** です。"
        "この二つの値を出発点にすると、同じ温度について予測した強度を次の測定候補の評価に使えます。\n"
    )
    (quality / "ch05-shared-posterior.qmd").write_text(shared, encoding="utf-8")


    pi_mid = acq["prediction_grid_midpoint_pi"]
    z_mid = acq["prediction_grid_midpoint_z"]
    shared_pi = (
        f"第4章から引き継いだ $x=0.50$ の値と、"
        f"この実験の基準値 $b={acq['threshold_mpa']:.3f}$ MPa を使います。"
        f"丸め前の数値で $z\\approx {z_mid:.3f}$、"
        f"$\\mathrm{{PI}}={pi_mid:.6f}$（約 {100*pi_mid:.3f}%）です。"
        "標準正規分布の累積確率とBoTorchの計算を同じ入力で照合しています。\n"
    )
    (quality / "ch05-midpoint-pi.qmd").write_text(shared_pi, encoding="utf-8")

    example_lines = [
        "| 候補 | 平均 [MPa] | 標準偏差 [MPa] | PI | EI [MPa] | 改善した場合の平均改善量 [MPa] |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in acq["worked_example"].items():
        example_lines.append(
            f"| {name} | {row['mean_mpa']:.1f} | {row['sd_mpa']:.1f} | {row['pi']:.3f} "
            f"| {row['ei_mpa']:.3f} | {row['conditional_improvement_mpa']:.3f} |"
        )
    (quality / "ch05-worked-example.qmd").write_text(
        "\n".join(example_lines) + "\n", encoding="utf-8"
    )
    acq_text = [
        f"閾値はこの実行で約 **{acq['threshold_mpa']:.3f} MPa** です。",
        "",
        "| 獲得関数 | グリッド最大 $x$ | 連続最適化の $x$ | 温度 [°C] |",
        "|---|---:|---:|---:|",
    ]
    for name, row in acq["candidates"].items():
        acq_text.append(
            f"| {name} | {row['grid_max_x']:.4f} | {row['optimized_x']:.4f} "
            f"| {row['optimized_temperature_c']:.2f} |"
        )
    (quality / "ch05-numbers.qmd").write_text("\n".join(acq_text) + "\n", encoding="utf-8")


def write_practice_numbers(quality):
    """Write Chapters 6 and 7's displayed results from the executed notebooks."""
    loop = json.loads((quality / "ch06_metrics.json").read_text(encoding="utf-8"))
    practice = json.loads((quality / "ch07_metrics.json").read_text(encoding="utf-8"))
    initial = "、".join(f"{x:.2f}" for x in loop["initial_temperatures_c"])
    first = (
        f"この実行の初期温度は **{initial} °C** でした。"
        f"最初の追加候補は **{loop['first_temperature_c']:.2f} °C** で、"
        f"その1回の測定で **{loop['first_mpa']:.2f} MPa** を得ました。\n"
    )
    (quality / "ch06-first.qmd").write_text(first, encoding="utf-8")

    count = loop["initial_count"] + loop["additional_count"]
    results = [
        "| 量 | 温度 [°C] | 値 [MPa] |",
        "|---|---:|---:|",
        f"| 手動ループの最良観測 | {loop['manual_best_temperature_c']:.2f} | {loop['manual_best_mpa']:.2f} |",
        f"| 手動ループの終了時に作った推薦 | {loop['recommended_temperature_c']:.2f} | {loop['recommended_mean_mpa']:.2f}（事後平均） |",
        "",
        f"初期と追加を含め、手動もStudyも実測は **{count}回** です。"
        f"Studyの最良観測値は **{loop['study_best_mpa']:.2f} MPa** でした。"
        "下段の推薦は最後のGPから計算した温度です。",
    ]
    (quality / "ch06-results.qmd").write_text("\n".join(results) + "\n", encoding="utf-8")

    rows = practice["scaling"]
    med_raw = median(row["physical"] for row in rows)
    med_norm = median(row["normalized"] for row in rows)
    lower_count = sum(row["normalized"] < row["physical"] for row in rows)
    scaling = (
        f"RMSEの中央値は、物理座標のモデルで **{med_raw:.2f} MPa**、"
        f"入力を正規化したモデルで **{med_norm:.2f} MPa** でした。"
        f"この合成試験では{len(rows)}回の比較中{lower_count}回で正規化後の誤差が小さくなりました。\n"
    )
    (quality / "ch07-scaling.qmd").write_text(scaling, encoding="utf-8")

    cases = (
        ("clean_logei", "ノイズなし・LogEI"),
        ("noisy_logei", "ノイズあり・LogEI"),
        ("noisy_lognei", "ノイズあり・qLogNEI"),
    )
    table = [
        "| 条件 | 最良観測値の中央値 [MPa] | 推薦点と最大値の差の中央値 [MPa] |",
        "|---|---:|---:|",
    ]
    for key, label in cases:
        entries = [row for row in practice["noise"] if row["case"] == key]
        obs = median(row["best_observed_mpa"] for row in entries)
        gap = median(row["recommendation_gap_mpa"] for row in entries)
        table.append(f"| {label} | {obs:.2f} | {gap:.2f} |")
    table.extend([
        "",
        "ノイズありでは最良観測値が高く出ても、推薦点と真の最大との間に差が残りました。"
        "右列で0は最大値の温度を推薦できたことを示します。",
    ])
    (quality / "ch07-noise.qmd").write_text("\n".join(table) + "\n", encoding="utf-8")

    rows = practice["solver_starts"]
    target = practice["diagnostic_grid_max_x"]
    solver = (
        f"初期点1個では $x={rows[0]['x']:.3f}$（LogEI {rows[0]['score']:.2f}）、"
        f"5個では $x={rows[1]['x']:.3f}$（LogEI {rows[1]['score']:.2f}）を得ました。"
        f"501点の診断グリッドでは $x={target:.3f}$ 付近の値が最も高くなりました。\n"
    )
    (quality / "ch07-solver.qmd").write_text(solver, encoding="utf-8")

    table = [
        "| 方式 | 候補の正規化温度 | 2点を同じqLogEIで再評価 |",
        "|---|---|---:|",
    ]
    for row in practice["batch"]:
        pair = "、".join(f"{x:.3f}" for x in row["x"])
        table.append(f"| {row['label']} | {pair} | {row['score']:.3f} |")
    (quality / "ch07-batch.qmd").write_text("\n".join(table) + "\n", encoding="utf-8")


def write_active_learning_numbers(quality):
    """Regenerate the classification and active-learning tables in the text."""
    active, classifier = (
        json.loads((quality / f"ch{index:02d}_metrics.json").read_text(encoding="utf-8"))
        for index in (8, 9)
    )

    def write(name, text):
        (quality / f"{name}.qmd").write_text(text + "\n", encoding="utf-8")

    initial = "、".join(f"{x:.0f}" for x in active["initial_temperatures_c"])
    labels = "、".join(map(str, active["initial_labels"]))
    write("ch08-first", (
        f"初期温度は **{initial} °C**、順に {labels} が返りました。"
        f"予測エントロピーは **{active['first_entropy_temperature_c']:.1f} °C**、"
        f"BALDは **{active['first_bald_temperature_c']:.1f} °C** を選びました。"
        f"この回ではBALDの候補だけを測り、ラベル **{active['first_bald_label']}** を得ました。"
    ))
    a, b = active["worked_bald"]
    write("ch08-disagreement", "\n".join([
        "| 候補 | $P_x$ の分布 | 予測エントロピー [nat] | BALD [nat] |",
        "|---|---|---:|---:|",
        f"| A | 常に0.5 | 0.693 | {a:.3f} |",
        f"| B | 0.1と0.9が等確率 | 0.693 | {b:.3f} |",
    ]))
    write("ch08-regression", (
        f"潜在分散が最大の候補は **{active['regression_variance_temperature_c']:.1f} °C**、"
        f"事後平均が最大の候補は **{active['regression_mean_temperature_c']:.1f} °C** でした。"
    ))
    curves = [
        "| 方策 | 初期4件の中央値 | 最終10件の中央値 |",
        "|---|---:|---:|",
    ]
    for strategy, name in (("random", "ランダム"), ("entropy", "予測エントロピー"), ("bald", "BALD")):
        runs = active["trials"][strategy]
        start = median(row["brier"][0] for row in runs)
        end = median(row["brier"][-1] for row in runs)
        curves.append(f"| {name} | {start:.4f} | {end:.4f} |")
    write("ch08-curve", "\n".join(curves))

    write("ch09-first", (
        f"最初の評価点 **{classifier['first_test_temperature_c']:.2f} °C** での予測合格確率は "
        f"**{classifier['first_test_p']:.3f}** でした。"
    ))
    write("ch09-checks", (
        f"241点で ◇predict_proba◇ とProbitの解析式を照合した最大絶対差は "
        f"**{classifier['probit_max_abs_error']:.2e}** でした。"
        f"48点Gauss–Hermite求積と公開APIの差は最大 **{classifier['quadrature_max_abs_error']:.2e}** でした。"
    ).replace("◇", chr(96)))
    write("ch09-query", (
        f"予測エントロピーが選んだのは **{classifier['entropy_temperature_c']:.1f} °C**、"
        f"BALDが選んだのは **{classifier['bald_temperature_c']:.1f} °C** でした。"
        f"BALDの候補でラベル **{classifier['new_label']}** を記録し、9件で学習し直しました。"
    ))
    scores = [
        "| 訓練データ | Brier損失 | 対数損失 [nat/件] | 誤分類率（閾値0.5） |",
        "|---|---:|---:|---:|",
    ]
    for stage, label in (("before", "初期8件"), ("after", "BALDで1件追加")):
        row = classifier[stage]
        scores.append(
            f"| {label} | {row['brier']:.4f} | {row['log_loss']:.4f} | {row['error_rate']:.1%} |"
        )
    write("ch09-scores", "\n".join(scores))


def write_application_numbers(quality):
    """Update the text's worked results for Chapters 10 through 12."""
    materials, advanced, guidance = (
        json.loads((quality / f"ch{index:02d}_metrics.json").read_text(encoding="utf-8"))
        for index in (10, 11, 12)
    )

    def write(name, body):
        (quality / f"{name}.qmd").write_text(body + "\n", encoding="utf-8")

    rows = [
        "| 追加試験 | 温度 [°C] | 保持時間 [分] | 強度 [MPa] |",
        "|---|---:|---:|---:|",
    ]
    for number, row in enumerate(materials["new_trials"], 1):
        rows.append(
            f"| B{number:02d} | {row['temperature']:.2f} | {row['hold']:.2f} | {row['strength']:.2f} |"
        )
    write("ch10-trials", "\n".join(rows))
    best = materials["best_setting"]
    t, hold = materials["recommendation"]
    write("ch10-recommendation", (
        f"全完了試験での最良観測値は **{materials['best_observed']:.2f} MPa**"
        f"（{best['temperature_c']:.2f} °C、{best['hold_min']:.2f}分）でした。"
        f"終了時の推薦は **{t:.2f} °C、{hold:.3f}分** で、"
        f"その事後平均は **{materials['posterior_mean_at_recommendation']:.2f} MPa** です。"
    ))
    baseline, recommended = materials["confirmation_means"]
    write("ch10-confirmation", (
        f"確認試験の平均は、現行条件で **{baseline:.2f} MPa**、"
        f"推薦条件で **{recommended:.2f} MPa** でした。"
        f"4件ずつの測定を丸める前に比較した平均の差は **{recommended - baseline:.2f} MPa** です。"
    ))
    front = "、".join(advanced["pareto"])
    write("ch11-pareto", (
        f"非支配点は **{front}** です。参照点は（75 MPa、14 kWh）で、"
        f"面積は **{advanced['hypervolume']:.0f} MPa·kWh** です。"
        "強度の区間を75–77、77–80、80–81、81–82 MPaに分けると、"
        "各帯の面積は $2(7),3(6),1(4),1(1)$ となります。"
        f"Dを追加する前の集合に対して、Dは **{advanced['gain_d']:.0f} MPa·kWh** の面積を加えます。"
    ))
    write("ch11-context", (
        "Notebookでは状況0の二つの操作の効用を5と2、状況1では1と6とします。"
        "二つの状況を等確率とすると、状況ごとに操作を選ぶ場合の平均効用は "
        f"**{advanced['contextual_reward']:.1f}**、"
        f"先に一つの操作へ固定する場合の最良平均効用は **{advanced['fixed_reward']:.1f}** です。"
    ))
    write("ch11-causal", (
        "合成観測データ5,000件を単回帰した傾きは "
        f"**{advanced['observational_slope']:.3f}** でした。"
        "観測の傾きの理論値0.5と、構造方程式から計算した介入の傾き−1を比べます。"
    ))
    write("ch12-loss", (
        f"費用から決めた閾値は **{guidance['threshold']:.1f}** です。"
        "0.66の条件は不合格、0.91の条件は合格と判定します。"
        "二条件の等重み平均の期待損失は、閾値0.5の判定で "
        f"**{guidance['equal_weight_mean_default_loss']:.2f}**、"
        f"費用に基づく閾値では **{guidance['equal_weight_mean_optimal_loss']:.2f}** です。"
    ))
    write("ch12-budget", (
        f"たとえば、上限 **{guidance['total_budget']}回** に対し、"
        f"初期試験を{guidance['initial']}回、確認を{guidance['confirm']}回とすると、"
        f"適応的に選ぶ試験は最大 **{guidance['adaptive']}回** です。"
        "試料を消費した失敗も、この枠を1回使います。"
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notebook", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.notebook:
        run_notebook(args.notebook)
        return
    directory = Path(__file__).resolve().parent
    for path in sorted(directory.glob("ch[0-9][0-9]_*.ipynb")):
        start = perf_counter()
        subprocess.run(
            [sys.executable, "-Xfrozen_modules=off", __file__, "--notebook", path.name],
            cwd=directory,
            check=True,
        )
        print(f"{path.name}: {perf_counter() - start:.2f} s", flush=True)
    quality = directory.parent / "quality"
    write_foundation_numbers(quality)
    write_book_numbers(quality)
    write_practice_numbers(quality)
    write_active_learning_numbers(quality)
    write_application_numbers(quality)


if __name__ == "__main__":
    main()
