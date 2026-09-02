#curl --limit-rate: impone un tetto massimo alla velocità di download (il "rubinetto"
#del client, Rc nella Fig. 1.19/1.20 del Kurose). Qui il collo di bottiglia (par. 1.4.4,
#bottleneck link = min(Rs, Rc)) siete voi stessi, non la rete: il throughput misurato si
#dovrebbe avvicinare al limite imposto, non alla velocità reale della vostra connessione.

curl --limit-rate 10M -o /dev/null -w "bytes scaricati: %{size_download}\ntempo: %{time_total} s\nthroughput medio: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/10MB.zip #> output_throughput_limited.txt
