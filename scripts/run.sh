#!/usr/bin/env bash

DATA_DIR=data/iwpt2020stdata

# ar_padt:bg_btb:cs_cac:cs_fictree:cs_pdt:en_ewt:et_edt:fi_tdt:fr_sequoia:it_isdt:lt_alksnis:lv_lvtb:nl_alpino:nl_lassysmall:nl_lassysmall:pl_lfg:pl_pdb:ru_syntagrus:sk_snk:sv_talbanken:ta_ttb:uk_iu

test -z $1 && echo "Missing list of TBIDs (space or colon-separated)"
test -z $1 && exit 1
TBIDS=$(echo $1 | tr ':' ' ')


out_file=log.txt

if [ -e "$out_file" ]; then
    rm $out_file
else 
    touch $out_file
fi 

for tbid in $TBIDS ; do

  if [ "$tbid" = "ar_padt" ] || [ "$tbid" = "cs_cac" ] || [ "$tbid" = "cs_fictree" ] || [ "$tbid" = "cs_pdt" ]; then
    extra_args="--attach_morphological_case"
  else
    extra_args=""
  fi

  echo "" >> $out_file
  echo "==== $tbid ====" >> $out_file
  for filepath in ${DATA_DIR}/UD_*/${tbid}-ud-train.conllu; do
  dir=`dirname ${filepath}`        # e.g. /home/user/ud-treebanks-v2.2/UD_Afrikaans-AfriBooms
  tb_name=`basename ${dir}`        # e.g. UD_Afrikaans-AfriBooms

  python run.py \
  -g ${DATA_DIR}/${tb_name}/${tbid}-ud-test.conllu \
  -s ${DATA_DIR}/sysoutputs/adapt/test/pertreebank/$tbid-ud-test-sys.conllu \
  ${extra_args} \
  >> $out_file

  echo "" >> $out_file
  echo "==========" >> $out_file
  done
done
