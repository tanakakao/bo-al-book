# Pythonで学ぶベイズ最適化と能動学習

tanakakao 編著。第1巻「基礎理論と実践」第1版（v1.0.0、2026年）です。仮想材料試験を使い、候補提案、確率とカーネル、ガウス過程の事後予測、獲得関数から能動学習と二値GP分類、実験表を使う材料試験の運用、発展手法までを順に学びます。第1章は決定論的な測定、第2章は確率の小例、第4・5章は共通のノイズ付き観測を使用します。

| 内容 | ファイル |
|---|---|
| 編集原稿 | `chapters/` の章別原稿12本 |
| 索引と奥付 | `appendices/term-index.qmd`、`appendices/colophon.qmd` |
| 章末演習の解答 | `appendices/exercises.qmd` |
| 実行済み教材 | `notebooks/` の章別Notebook12本 |
| HTML版 | `html/index.html`。フォルダ単位で開く |
| 書籍紹介・公開手順 | `editorial/BOOK_DESCRIPTION.md`、`editorial/PUBLISHING.md` |
| 引用と利用条件 | `CITATION.cff`、`LICENSE.md` |
| 文献・検証結果 | `references.bib`、`quality/environment-linux.txt`、`quality/ch*_metrics.json` |

## 教材を再実行する

Python 3.11、Git、Noto Sans CJK JPを準備します。CPU版PyTorchと、教材で確認した版のパッケージを仮想環境に入れます。Windows PowerShellでは有効化に `.venv\Scripts\Activate.ps1` を使います。

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.9.1"
python -m pip install -r requirements.txt
python notebooks/run.py
```

JupyterLabから試す場合は、同じ仮想環境で `jupyter lab` を起動し、各Notebookを先頭から実行してください。章のコードから利用する `experiment.py` と `classification_experiment.py` は `notebooks/` 内にあります。基準シードは2026で、CPU・倍精度を使用します。各比較のシードは検証記録に記載しました。

`notebooks/run.py` は章ごとに独立したプロセスのIPythonカーネルで全コードセルを順に実行し、出力とセル番号を保存します。図は `figures/` にPDFとSVG、検算結果は `quality/` にJSONで生成されます。書籍の数値表も同じJSONから更新されます。

## 書籍を組版する

Quarto 1.11.9、XeLaTeX、互換版のxeCJK、Noto Serif CJK JP、Noto Serif、Noto Sans、DejaVu Sans Monoを使用しました。Quartoが認識できるTeX環境を用意し、プロジェクト直下で実行します。

```bash
python scripts/build_index.py
python scripts/package_materials.py
quarto render
```

`_book/` にHTMLとPDFが生成されます。HTMLの数式はMathJaxを使います。配布用HTMLをローカルで見るときもMathJaxの読込みにネット接続が必要です。オフラインではPDFを利用できます。

実行結果の再現に使ったコミットは [robotorchanの固定コミット](https://github.com/tanakakao/robotorchan/tree/b1bb77087cd117d83ed21a226a6fce39ccd5b497) です。理論と実装の出典は本文の参考文献と `references.bib` にあります。

本文の代表値はNotebookの再実行で更新されます。第3章の共分散行列と第4章の固定例、第4章と第5章の共通する事後予測を数値で照合します。

第6章は連続入力での決定論的な試験です。手動とStudyは同じ初期4点と追加4回の予算で動かします。第7章の入力変換・測定ノイズ比較はseed 2026〜2029を使います。結果に含む候補計算時間は実行環境に依存します。

第8章では初期4件と追加6件の合否試験を5シードで比較します。第9章では別の120点の評価ラベルを使い、確率予測と判定の指標を算出します。合否の生成器とGP分類器の共通の学習設定は `notebooks/classification_experiment.py` にあります。

第10章で使う過去ログは `data/ch10_historical_log.csv` に同梱しています。Notebookを実行すると、同じログと `ch10_trial_log.csv`、`ch10_confirmation.csv` を合成データから再生成します。取込とモデル設定は `notebooks/production_experiment.py` にあります。第11章では既知の目的値や構造方程式を用い、第12章では費用と予算の数値例を実行します。

[オンライン版](https://tanakakao.github.io/bo-al-book/)からPDFと教材を読めます。書籍の引用例は巻末の「奥付・引用方法」にあります。配信手順は `editorial/PUBLISHING.md` を参照してください。
