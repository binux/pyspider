# for docker to auto get proxy from a interface 
# this shell should run in container with squid
# if the peers.conf be changed this shell will reload the squid

lastFile=""
while true
do
    nowFile=`cat /etc/squid/peers.conf`
    if [[ $lastFile == $nowFile ]]
    then
        echo "equid!"
    else
        squid -k reconfigure
        lastFile=$nowFile
    fi 
    sleep 1
done

