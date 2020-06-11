rm infoHashes.txt
rm zipHashes.txt

for i in CustomContent/*.info; do 
	md5sum $i >> infoHashes.txt; 
done;

for i in CustomContent/*.info; do
	fname="${i%.*}";
	zip -9 ${fname}.zip ${fname}.info ${fname}.content;
	
	md5sum ${fname}.zip >> zipHashes.txt;
done	


