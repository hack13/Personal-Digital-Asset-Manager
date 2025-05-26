# Assets Site

A digital asset management system built with Flask and S3-compatible storage.

## Features

- Digital asset management with metadata
- S3-compatible storage backend (works with MinIO, public buckets only atm)
- Automatic WebP conversion for images
- License key management
- Docker container support

## Screenshots
<details>
  <summary>Home Page</summary>
  <p>
    <img src="https://git.hack13.dev/hack13/Personal-Digital-Asset-Manager/raw/branch/main/repo-images/list-of-assets.webp" />
  </p>
</details>
<details>
  <summary>Asset View</summary>
  <p>
    <img src="https://git.hack13.dev/hack13/Personal-Digital-Asset-Manager/raw/branch/main/repo-images/asset-view.webp" />
  </p>
</details>
<details>
  <summary>Edit Page</summary>
  <p>
    <img src="https://git.hack13.dev/hack13/Personal-Digital-Asset-Manager/raw/branch/main/repo-images/edit-view.webp" />
  </p>
</details>

## Installation

You can use [this docker compose file](docker-compose.yml) to install this project using docker.

## Container Registry

This project includes automated container builds using Forgejo CI/CD. The container images are published to the project's container registry.

### Using the Container Image

To pull the latest image:

```bash
docker pull git.hack13.dev/hack13/personal-digital-asset-manager:latest
```

For a specific version:

```bash
docker pull git.hack13.dev/hack13/personal-digital-asset-manager:v1.0.0
```

### CI/CD Setup

The project uses Forgejo CI/CD to automatically build and publish container images. To set up the CI/CD pipeline:

1. Configure the following variables in your Forgejo repository settings (Settings > Variables):
   - `FORGEJO_REGISTRY`: Your Forgejo registry URL (e.g., forgejo.yourdomain.com)
   - `FORGEJO_OWNER`: Your Forgejo username or organization name
   - `FORGEJO_USER`: Username for registry authentication

2. Add the following secret in your Forgejo repository settings (Settings > Secrets):
   - `FORGEJO_TOKEN`: Access token for Forgejo registry authentication

3. Enable Forgejo Actions in your repository settings

### Container Tags

The following tags are automatically generated:
- `latest`: Latest build from the main branch
- `v*`: Release tags (e.g., v1.0.0)
- `sha-*`: Build for specific commit

## Development

### Local Setup

1. Clone the repository
2. Create and activate a virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Set up environment variables (see `.env.example`)
5. Run migrations: `flask db upgrade`
6. Start the server: `flask run`

### Database Migrations

This project uses Flask-Migrate (Alembic) for database migrations. The migrations folder is version controlled and should be included in your commits.

#### Working with Migrations

1. Create a new migration after model changes:
   ```bash
   flask db migrate -m "Description of changes"
   ```

2. Review the generated migration in `migrations/versions/`

3. Apply migrations:
   ```bash
   flask db upgrade
   ```

4. Rollback migrations:
   ```bash
   flask db downgrade
   ```

#### First-time Setup

When cloning the repository:
1. Initialize the database: `flask db upgrade`
2. This will apply all existing migrations in order

### Docker Development

Build the container:
```bash
docker build -t personal-digital-asset-manager .
```

Run the container:
```bash
docker run -p 5000:5000 \
  -v $(pwd)/static/uploads:/app/static/uploads \
  personal-digital-asset-manager
```