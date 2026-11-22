# Pythonで学ぶベイズ最適化と能動学習 第1巻の教材

第1版（v1.0.0）の実行済みNotebook全12本、合成CSVと補助コードです。章番号順に `notebooks/` を開くと、本文に対応する実行結果を確認できます。

## 実行環境を作る

Python 3.11、Git、Noto Sans CJK JPを準備します。作業フォルダをこのREADMEのある場所にして、CPU版の依存関係をインストールします。

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch==2.9.1"
python -m pip install -r requirements.txt
jupyter lab
~~~

Windows PowerShellで仮想環境を有効にするコマンドは `.venv\Scripts\Activate.ps1` です。再現検証はLinuxのCPU環境で行いました。

Notebookは最初のセルから実行します。全Notebookをまとめて実行する場合は、仮想環境を有効にして `python notebooks/run.py` を実行します。合成CSVは `data/`、図は `figures/`、数値の記録は `quality/` に出力します。第10章は同梱の合成CSVを再生成します。実データを扱うときは別のパスを使ってください。

robotorchanの実行版は `requirements.txt` のコミットで固定しています。合成CSVとサンプルコードの利用条件は同梱の [LICENSE.md](LICENSE.md) を参照してください。
