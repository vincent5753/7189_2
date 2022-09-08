subject=$(cat 1mail.txt | grep "Subject: " | awk -F "Subject: " '{print $2}')
echo 標題: \"$subject\"

boundary=$(cat 1mail.txt | grep "boundary=" | awk -F '"' '{print $2}')
echo 邊界: \"$boundary\"

delimiter="--$boundary"
echo 分隔符號: $delimiter

count=0
urlhead=0
urltail=0
rm tmp
while read line
do

  if [ "$line" = "$delimiter" ]
  then
    count=$(( $count + 1 ))
  fi
  if (( 2 > $count && $count > 0 ))
  then
#    echo $line

    if [[ $line == \<http* ]]
    then
      echo "開頭↓"
      partofurl=$(echo $line | sed 's/^<//g' | awk -F "=" '{NF--; print}' | sed 's/ /=/g')
      echo $partofurl
      echo -n $partofurl > tmp
      urlhead=1
      continue
    fi

    if [[ $line == *\> ]]
    then
      partofurl=$(echo -n $line\c | sed 's/>//g')
      echo $partofurl
      echo -n $partofurl >> tmp
      echo "結尾↑"
      urltail=1
    fi

    if [[ $urlhead == 1 && $urltail != 1  ]]
    then
      partofurl=$(echo -n $line\c | awk -F "=" '{NF--; print}' | sed 's/ /=/g')
      echo $partofurl
      echo -n $partofurl >> tmp
    fi

  fi

done < 1mail.txt

context=$(cat tmp)

echo ""
echo "<內容>"
echo $context
echo "<內容>"
echo ""
