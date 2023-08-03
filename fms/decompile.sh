#!/bin/bash
# By VP@23.08.02

for file in /tmp/itri-jar/*.jar
do
  echo $file
  filename=$(echo "$file" | awk -F "/" '{print $NF}')
  echo $filename
  mkdir "/tmp/output/$filename"
  java -jar jd-cli.jar $file --outputDir "/tmp/output/$filename"
done
