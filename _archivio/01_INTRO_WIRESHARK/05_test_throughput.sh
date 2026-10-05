#curl -w: downloads a file (~10 MB) and measures the average throughput F/T, sec. 1.4.4

curl -o /dev/null -w "bytes downloaded: %{size_download}\ntime: %{time_total} s\naverage throughput: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/100MB.zip #> output_throughput.txt
