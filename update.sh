cd /home/dvn-ss-06/
VERSION=`cat singularity/VERSION`
echo "Current Installed Version is $VERSION"
SERVER="ec2-52-14-235-150.us-east-2.compute.amazonaws.com"
UPDATE_FLAG=`curl "http://$SERVER/singularity-check?version=$VERSION"`
if [ "$UPDATE_FLAG" == "True" ]; then
        echo "Updatting"
        curl -o update.zip "http://$SERVER/update-ss?build=singularity"
        echo "Replacing old install"
        sudo unzip -o update.zip
        sudo rm update.zip
fi

cd singularity
sudo python3.7 app.py