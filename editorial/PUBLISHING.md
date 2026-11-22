# 第1巻 第1版の配信手順

書籍の指定先は `tanakakao/bo-al-book`、配信先は `https://tanakakao.github.io/bo-al-book/` です。ソースは `main`、配信用HTMLは `gh-pages` のルートに配置します。

## 同梱物

| パス | 内容 |
|---|---|
| `_quarto.yml`、`chapters/`、`appendices/` | 書籍設定、本文、解答、索引、奥付 |
| `notebooks/`、`data/`、`figures/`、`quality/` | 実行済み教材、合成データ、再生成用の図と数値、実行環境 |
| `CITATION.cff`、`LICENSE.md`、`LICENSES/` | 書籍の機械可読な引用情報と利用条件 |
| `html/` | 配布ZIP内の生成済みHTML、PDF、教材ZIP |
| `BO_AL_book_vol1_v1.0.0.bundle` | 配布ZIP内のGit履歴。ソース `main`、静的サイト `gh-pages`、タグ `v1.0.0` |

## 手元で確認する

`html/index.html` を開くか、展開先で `python -m http.server 8000 --directory html` を実行して `http://localhost:8000/` を開きます。オンライン版の数式表示にはMathJaxの読込みが必要です。オフラインでは同梱PDFを利用できます。

## 空の専用リポジトリへ配信する

GitHubで `tanakakao/bo-al-book` を空の公開リポジトリとして作成します。このリポジトリ名を使う前に、既存の別プロジェクトがないことを確認します。GitHubへの認証が済んだ環境で、配布ZIPの展開先から実行します。

~~~bash
git clone --branch main BO_AL_book_vol1_v1.0.0.bundle bo-al-book
git -C bo-al-book branch gh-pages origin/gh-pages
git -C bo-al-book remote set-url origin https://github.com/tanakakao/bo-al-book.git
git -C bo-al-book push -u origin main gh-pages
git -C bo-al-book push origin v1.0.0
~~~

リポジトリの **Settings → Pages** で **Deploy from a branch**、`gh-pages`、`/(root)` を指定します。配信後にトップ、索引、PDF、教材ZIPを実際のURLで開きます。GitHub Releaseを作成する場合はタグ `v1.0.0` を使い、同じ版のPDFを添付します。[GitHub Pagesの公開ソース設定](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

## 変更後に組み直す

~~~bash
python scripts/build_index.py
python scripts/package_materials.py
quarto render
~~~

`_book/` の出力を同じ配信構成で更新します。Quartoが生成する静的ファイルの利用条件は維持します。robotorchanは固定コミットからインストールする依存ライブラリです。[robotorchanのライセンス](https://github.com/tanakakao/robotorchan/blob/b1bb77087cd117d83ed21a226a6fce39ccd5b497/LICENSE)
