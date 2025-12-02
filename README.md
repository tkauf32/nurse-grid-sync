
1. Login to Nursegrid on a computer web browser. 
2. Click on "Calendar" tab on the left side
3. Click on "Options" button on the right side
4. Enable Calendar Sharing
5. Grab and save URL link under "Your Calendar URL"

make a .env file for your secrets ( the nursegrid calendar url, the secret token for your api server)

```sh
UPSTREAM_ICS_URL="https://app.nursegrid.com/calendars/unqiue-hash-here/unique-hash-here"
ICS_ACCESS_TOKEN="base64-encoded-unqiue-hash"
```

if you need to generate a unqiue hash for your access token, you can use openssl. Just remove any = or / chars

```sh
openssl rand -base64 32
```
