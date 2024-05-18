# ImageTranscoder

## 動作イメージ
![tk-2024-05-18-10-49-46-imageonline co-7839603](https://github.com/Yoohei1116/test/assets/164162238/f382d6da-b45b-46d9-9a24-fefb39b94b41)


### データセット
本デモンストレーションで用いる画像は以下の関数で作成しています:

$$ y=\frac{50}{x_1}+ε,&emsp;ε\sim N(0,x_{2}/500)$$ 

ここで誤差項は正規分布に従いますが、その分散は $x_2$ に比例するとします。このモデルから値を独立に抽出し、使用する画像を作成します。

![2020-01-01](https://github.com/Yoohei1116/test/assets/164162238/5112cadf-4d0c-4192-9585-d1596a1a288f)

このような画像を複数作成し、ダミー用の画像と合わせて一つのフォルダに保存しておきます。

<img width="831" alt="一覧" src="https://github.com/Yoohei1116/test/assets/164162238/e386d965-fdbc-4944-848b-1b51196b0696">
