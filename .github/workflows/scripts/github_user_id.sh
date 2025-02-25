cat ~/.local/bin/ghnoreply 
#!/bin/bash

USERNAME=$1

function fetch_user() {
    user_id="$(curl -s https://api.github.com/users/"${USERNAME}" | jq '.id')"

    printf "%s+%s@users.noreply.github.com" "$user_id" "$USERNAME"
}

{
    fetch_user
} 2>&1