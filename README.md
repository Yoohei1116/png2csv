# ImageTranscoder

## 動作イメージ
![tk-2024-05-18-10-49-46-imageonline co-7839603](https://github.com/Yoohei1116/test/assets/164162238/f382d6da-b45b-46d9-9a24-fefb39b94b41)


## データセット
本デモンストレーションで用いた画像は以下のような棒グラフで作成しています:

![2020-01-01](https://github.com/Yoohei1116/test/assets/164162238/5112cadf-4d0c-4192-9585-d1596a1a288f)

$x$軸は測定位置、$y$軸は品質の値に対応します。赤線は品質のしきい値であり、この赤線を境にして製品品質のOK/NGの判定を行います。このような画像を複数作成し、ダミー用の画像と合わせて一つのフォルダに保存しました。

<img width="831" alt="一覧" src="https://github.com/Yoohei1116/test/assets/164162238/e386d965-fdbc-4944-848b-1b51196b0696">

デモでは、このフォルダ内のグラフ画像を値に変換しcsvファイルとして出力しています。


## 統計情報の取得
作成したcsvファイルから以下の可視化を行うことができます。

- 基準値を超えるデータ数の割合
- 基本統計量(max,min,mean,std)
- 基本統計量の推移と分布

<img width="521" alt="スクリーンショット 2024-05-18 111510" src="https://github.com/Yoohei1116/test/assets/164162238/1b3ec5d5-4e41-4e51-867f-5e28007a51c5">
