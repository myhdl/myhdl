if [ "$CI_TARGET" == "iverilog" ]; then
  sudo apt-get -qq update
  sudo apt-get install iverilog
elif [ "$CI_TARGET" == "ghdl" ]; then
  url=$(curl -s https://api.github.com/repos/ghdl/ghdl/releases/tags/v0.33 | jq -r ".assets[] | select (.name | test (\"ubuntu1_amd64\"))| .browser_download_url")
  curl -Lo ghdl.deb $url
  sudo dpkg -i ghdl.deb
  sudo apt-get install -f
fi
