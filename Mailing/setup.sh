#!/bin/bash
sudo apt update
sudo apt install -y fetchmail procmail mutt

# ~/.fetchmailrc

cat <<EOF | tee ~/.fetchmailrc
poll pop.gmail.com with proto POP3 uidl user 'account' there with password 'password' keep ssl
mda "/usr/bin/procmail -d %T"
no fetchall
EOF

chmod 700 ~/.fetchmailrc


# ~/.procmailrc
cat <<EOF | tee ~/.procmailrc
VERBOSE=yes
DEFAULT=/var/spool/mail/$(whoami)
LOGFILE=$HOME/.procmail.log

:0: HBfw
* ^Subject:.*Verify email
| /bin/bash /home/$(whoami)/write.sh
EOF

sudo chown $(whoami) /var/spool/mail/

# write.sh
cat <<EOF | tee ~/write.sh
#!/bin/bash
# Check to see if a pipe exists on stdin.
if [ -p /dev/stdin ]; then
        rm 1mail.txt
        echo "Data was piped to this script!"
        # If we want to read the input line by line
        while IFS= read line
        do
                echo "\${line}"
                echo "\${line}" >> 1mail.txt
        done
else
        echo "No input was found on stdin, skipping!"
        # Checking to ensure a filename was specified and that it exists
        if [ -f "$1" ]; then
                echo "Filename specified: ${1}"
                echo "Doing things now.."
        else
                echo "No input given!"
        fi
fi
EOF
