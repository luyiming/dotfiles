function proxyoff
    set -e HTTP_PROXY
    set -e HTTPS_PROXY
    set -e ALL_PROXY

    set -e NO_PROXY

    set -e http_proxy
    set -e https_proxy
    set -e all_proxy

    echo "Proxy disabled"
end
