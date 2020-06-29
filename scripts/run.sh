#!/usr/bin/env bash

DATA_DIR=data/iwpt2020stdata

# ar_padt-bg_btb-cs_cac-cs_fictree-cs_pdt-en_ewt-et_edt-fi_tdt-fr_sequoia-it_isdt-nl_alpino-nl_lassysmall-lv_lvtb-lt_alksnis-pl_lfg-pl_pdb-ru_syntagrus-sk_snk-sv_talbanken-ta_ttb-uk_iu

test -z $1 && echo "Missing list of TBIDs (space or dash-separated)"
test -z $1 && exit 1
TBIDS=$(echo $1 | tr '-' ' ')

out_file=$1_log.txt

arr=(bg_btb nl_alpino nl_lassysmall en_ewt fr_sequoia it_isdt lv_lvtb pl_lfg sv_talbanken)

# tbids which attach morphological case
arr_mc=(ar_padt cs_cac cs_fictree cs_pdt et_edt fi_tdt  lt_alksnis pl_pdb ru_syntagrus sk_snk ta_ttb uk_iu)

if [ -e "$out_file" ]; then
    rm $out_file
else 
    touch $out_file
fi 

for tbid in $TBIDS ; do
  echo $tbid
  if [[ " ${arr[*]} " == *" $tbid "* ]]; then
    echo "not attaching morph case"
    extra_args=""
  elif [[ " ${arr_mc[*]} " == *" $tbid "* ]]; then
    echo "attaching morph case"
    extra_args="--attach_morphological_case"
  fi

  echo $'\n'"--------------------" >> ${out_file}
  echo "$tbid" >> ${out_file}
  echo "--------------------"$'\n' >> ${out_file}
  echo $'\n'"with extra args: ${extra_args}" >> ${out_file}
  
  for filepath in ${DATA_DIR}/UD_*/${tbid}-ud-train*.conllu; do
    dir=`dirname ${filepath}`        # e.g. /home/user/ud-treebanks-v2.2/UD_Afrikaans-AfriBooms
    tb_name=`basename ${dir}`        # e.g. UD_Afrikaans-AfriBooms

    GOLD=${DATA_DIR}/${tb_name}/${tbid}-ud-test.conllu
    SYSTEM=${DATA_DIR}/sysoutputs/adapt/test/pertreebank/$tbid-ud-test-sys.conllu

    if [ "$tbid" == "fr_sequoia" ]; then
      GOLD=${DATA_DIR}/${tb_name}/${tbid}-ud-test.fulldeps.conllu
    fi

    python run.py \
      -g ${GOLD} \
      -s ${SYSTEM} \
      ${extra_args} >> ${out_file}
  done
done
