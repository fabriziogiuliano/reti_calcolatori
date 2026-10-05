#curl --limit-rate: sets a maximum download speed (the client "tap",
#Rc in Fig. 1.19/1.20 of the Kurose). Here the bottleneck (sec. 1.4.4,
#bottleneck link = min(Rs, Rc)) is you, not the network: the measured throughput
#should get close to the imposed limit, not to the real speed of your connection.

curl --limit-rate 10M -o /dev/null -w "bytes downloaded: %{size_download}\ntime: %{time_total} s\naverage throughput: %{speed_download} B/s\n" http://ipv4.download.thinkbroadband.com/10MB.zip #> output_throughput_limited.txt
