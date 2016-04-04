for a in wxtextview/*.py ; do echo $a; sed 's/import ..textmodel/import textmodel/g' $a |sed 's/from ..textmodel/from textmodel/g' > tmp.txt; mv tmp.txt $a; done
 
