OpenClaw Gmail via gog

Files
- /etc/openclaw/credentials/gog-keyring-password
  Root-only password used to decrypt gog's file keyring at runtime.
- /root/.config/gogcli/credentials.json
  Google OAuth client credentials.
- /root/.config/gogcli/keyring/
  Encrypted gog OAuth tokens.

Runtime
- systemd unit: openclaw-gateway.service
- Credential injection: LoadCredential=gog_keyring_password:...

Checks
- systemctl status openclaw-gateway.service
- openclaw health

Recovery
1. Ensure /root/.config/gogcli/config.json still contains {"keyring_backend":"file"}.
2. Ensure the password file exists at /etc/openclaw/credentials/gog-keyring-password with mode 600.
3. Restart the service: systemctl restart openclaw-gateway.service
4. If Google auth expires, re-run gog auth add for Andyxlaer92@gmail.com.
