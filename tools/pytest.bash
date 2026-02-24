_() {
    echo "$1"
    local _RYS_LLM=http://192.168.0.25
    # local _RYS_LLM=http://192.168.32.67
    # local _RYS_LLM=http://192.168.32.86
    RYS_LLM_HOST=${_RYS_LLM} ./rys/main.bash "$1" --from=5,6 --auto
}

_ "1～2000 までの素数を教えて"
    # task1: 1-2000までの素数計算をする
    # Job1: task1

_ "234314121 を素因数分解して"
    # task1: 234314121を素因数分解する
    # Job1: task1
