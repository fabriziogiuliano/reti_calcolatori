#curl -w: scarica un file (~10 MB) e misura il throughput medio F/T, par. 1.4.4

curl -o /dev/null -w "bytes scaricati: %{size_download}\ntempo: %{time_total} s\nthroughput medio: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/100MB.zip #> output_throughput.txt
