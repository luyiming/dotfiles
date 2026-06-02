function proxyon
    set -gx HTTP_PROXY http://127.0.0.1:7890
    set -gx HTTPS_PROXY http://127.0.0.1:7890
    set -gx ALL_PROXY socks5://127.0.0.1:7890

    set -gx NO_PROXY localhost,127.0.0.1

    set -gx http_proxy $HTTP_PROXY
    set -gx https_proxy $HTTPS_PROXY
    set -gx all_proxy $ALL_PROXY

    echo "Proxy enabled: $HTTP_PROXY"
end
