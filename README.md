## Launched with Docker

```bash
docker run \
  --detach \
  --name homeassistant \
  --privileged \
  --restart unless-stopped \
  --env TZ=America/New_York \
  --volume /mnt/crucial-x9/apps/homeassistant:/config \
  --volume /run/dbus:/run/dbus:ro \
  --network host \
  ghcr.io/home-assistant/home-assistant:stable
```

## Upgrade

```bash
docker pull ghcr.io/home-assistant/home-assistant:stable
docker stop homeassistant
docker rm homeassistant
# run launch command
```

## Matter Server (Docker)

```bash
docker run \
  --detach \
  --name matter-server \
  --privileged \
  --restart unless-stopped \
  --volume /mnt/crucial-x9/apps/homeassistant-matter:/data \
  --network host \
  ghcr.io/matter-js/python-matter-server:stable
```

## HACS

```bash
docker exec -it homeassistant bash
wget -O - https://get.hacs.xyz | bash -
exit
docker restart homeassistant
```
