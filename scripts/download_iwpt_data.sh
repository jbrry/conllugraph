#!/bin/bash

mkdir -p data
cd data

# download IWPT 2020 data
curl --remote-name-all https://lindat.mff.cuni.cz/repository/xmlui/bitstream/handle/11234/1-3238{/iwpt2020stdata.tgz}
tar -xf iwpt2020stdata.tgz

echo "done"
