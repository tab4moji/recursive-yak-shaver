_() {
    echo "$1"
    local _RYS_LLM=http://192.168.0.25
    # local _RYS_LLM=http://192.168.32.67
    # local _RYS_LLM=http://192.168.32.86
    RYS_LLM_HOST=${_RYS_LLM} ./rys/main.bash "$1" --auto
}

_ "このディレクトリのフルパスを調べて."
    # task1: ディレクトリのフルパスを調べる
    # Job1: task1

_ "今の時間を教えて。"
    # task1: 時刻を調べる
    # Job1: task1

_ "このディレクトリで一番大きい python ファイルに対して pylint を実行して。"
    # task1: ディレクトリの python ファイル一覧を調べる
    # task2: task2 の結果の中で一番大きいファイルを調べる
    # task3: task3 の結果に対して pylint を実行する
    # Job1: task1, task2, task3

_ "このディレクトリのフルパスを調べて."
    # task1: ディレクトリのフルパスを調べる
    # Job1: task1

_ "今の時間を教えて。"
    # task1: 時刻を調べる
    # Job1: task1

_ "今、何時？"
    # task1: 時刻を調べる
    # Job1: task1

_ "明日の天気を教えて。あと、このディレクトリのファイルの中で一番大きいファイルを知りたい 。そして、一番小さいファイルの中身を表示して。それと、1～2000 までの素数を教えて。あ、それと美味しいケーキ屋さんを探して。"
    # task1: 明日の天気を調べる
    # task2: ディレクトリのファイル一覧を調べる
    # task3: task2 の結果の中で一番大きいファイルを調べる
    # task4: task2 の結果の中で一番小さいファイルを調べる
    # task5: task4 の結果のファイルを cat する
    # task6: 1-2000までの素数計算をする
    # task7: 美味しいケーキ屋さんを調べる
    # Job1: task2, task3
    # Job2: task2, task4, task5
    # Job3: task6
    # IDONTKNOW: task1, task7

