function proxyon
    if test (count $argv) -gt 1
        echo "Usage: proxyon [host:port]" >&2
        return 2
    end

    set -l proxy_addr 127.0.0.1:7890
    if test (count $argv) -eq 1
        set proxy_addr $argv[1]
    end

    set -gx HTTP_PROXY http://$proxy_addr
    set -gx HTTPS_PROXY http://$proxy_addr
    set -gx ALL_PROXY socks5://$proxy_addr

    set -gx NO_PROXY localhost,127.0.0.1

    set -gx http_proxy $HTTP_PROXY
    set -gx https_proxy $HTTPS_PROXY
    set -gx all_proxy $ALL_PROXY

    echo "Proxy enabled: $HTTP_PROXY"
end
