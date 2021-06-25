#!/usr/bin/env bash

DATA_DIR=data/train-dev

TBIDS=`ls ${DATA_DIR}/*/*ud-train.conllu | cut -d/ -f4 | cut -d- -f1`

# primarys
# https://github.com/nlp-uoregon/trankit/blob/master/trankit/utils/tbinfo.py
primary_tbids="ar_padt bg_btb cs_pdt nl_alpino en_ewt et_edt fi_tdt it_isdt lv_lvtb lt_alksnis pl_pdb ru_syntagrus sk_snk sv_talbanken ta_ttb uk_iu"

# set up array of primarys
declare -A primarys
for p in $primary_tbids
do
    primarys[$p]=1
done

for tbid in $TBIDS; do
   echo "** $tbid **"
   
   # do train/dev
   for ftype in train dev; do
      for gold_filepath in ${DATA_DIR}/UD_*/${tbid}-ud-${ftype}.conllu; do
        dir=`dirname ${gold_filepath}`        # e.g. /home/user/ud-treebanks-v2.2/UD_Afrikaans-AfriBooms
        tb_name=`basename ${dir}`        # e.g. UD_Afrikaans-AfriBooms

        if [[ ${primarys[$tbid]} ]]; then
            echo "primary tbid, language is the main string"
            language=`echo $tb_name | cut -d_ -f2 | cut -d- -f1 | awk '{print tolower($0)}'`

        else
            language=`echo $tb_name | cut -d_ -f2 | awk '{print tolower($0)}'`
        fi

        echo "using $language for trankit"

        # 1) convert gold conllu to plaintext
        python conllugraph/conllu_to_text.py -i ${gold_filepath} --mode gold-to-plainsen --skip-mwt

        # 2) predict with trankit
        python scripts/trankitpip.py data/train-dev-gold-to-plainsen/${tb_name}/${tbid}-ud-${ftype}.conllu $language trankit_predicted/${tbid}-ud-${ftype}.conllu

        # 3) copy pred annotations to gold file
        python conllugraph/conllu_to_text.py -i ${gold_filepath} -s trankit_predicted/${tbid}-ud-${ftype}.conllu --mode pred-to-misc

      done
    done

done



  
