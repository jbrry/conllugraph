#!/usr/bin/env bash

DATA_DIR=data/iwpt2020stdata

test -z $1 && echo "Missing list of TBIDs (space or colon-separated)"
test -z $1 && exit 1
TBIDS=$(echo $1 | tr ':' ' ')

for tbid in $TBIDS ; do
  echo
  echo "== $tbid =="
  echo
  for filepath in ${DATA_DIR}/UD_*/${tbid}-ud-train.conllu; do
  dir=`dirname $filepath`        # e.g. /home/user/ud-treebanks-v2.2/UD_Afrikaans-AfriBooms
  tb_name=`basename $dir`        # e.g. UD_Afrikaans-AfriBooms

  python run.py \
  -g $DATA_DIR/${tb_name}/${tbid}-ud-test.conllu \
  -s $DATA_DIR/sysoutputs/adapt/test/pertreebank/$tbid-ud-test-sys.conllu
  done
done
