# The Haven Engine v3

FastAPI backend for The Haven.

### Endpoints
- `/` service information (fixes the old Render root 404)
- `/health` Render health check
- `/capabilities` capability map
- `/chat` engineering assistant rules
- `/design/spec` deterministic UX/UI design specification
- `/projects/build` project scaffolding/build job
- `/projects/{id}/download` ZIP export
- `/uploads` asset upload

### Render storage
`DATA_DIR=/var/data`. Attach a Persistent Disk with mount path `/var/data`. The included Blueprint declares a 10 GB disk. Render currently requires a paid service plan for Persistent Disks.

### Scaling
A single persistent disk is single-instance storage. For multi-instance scaling, move metadata to Postgres and files to object storage rather than sharing local disk.
