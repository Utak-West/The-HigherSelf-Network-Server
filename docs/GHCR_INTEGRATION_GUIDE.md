# GitHub Container Registry Integration Guide

## Overview

This guide covers the complete GitHub Container Registry (GHCR) integration for The HigherSelf Network Server, including automated builds, multi-platform support, security scanning, and deployment workflows.

## Table of Contents

1. [Quick Start](#quick-start)
2. [GHCR Setup](#ghcr-setup)
3. [Automated Builds](#automated-builds)
4. [Image Management](#image-management)
5. [Deployment with GHCR](#deployment-with-ghcr)
6. [Security and Compliance](#security-and-compliance)
7. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Pull and Run from GHCR

```bash
# Pull the latest stable image
docker pull ghcr.io/utak-west/higherself-network-server:stable

# Run with Docker Compose using GHCR
docker-compose -f docker-compose.yml -f docker-compose.ghcr.yml up -d

# Or use the GHCR manager script
./scripts/ghcr-manager.sh pull stable
./scripts/ghcr-manager.sh deploy development
```

### 2. Build and Push to GHCR

```bash
# Login to GHCR
export GITHUB_TOKEN="your_github_token"
./scripts/ghcr-manager.sh login

# Build and push
./scripts/ghcr-manager.sh build v1.0.0

# Test the image
./scripts/ghcr-manager.sh test v1.0.0
```

## GHCR Setup

### Prerequisites

1. **GitHub Personal Access Token**
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Create token with `write:packages` and `read:packages` scopes
   - Store as `GITHUB_TOKEN` environment variable

2. **Docker Configuration**
   ```bash
   # Login to GHCR
   echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
   ```

### Repository Configuration

1. **Enable GitHub Packages**
   - Go to repository Settings → Actions → General
   - Enable "Read and write permissions" for GITHUB_TOKEN

2. **Configure Secrets**
   ```bash
   # Required secrets in GitHub repository:
   GITHUB_TOKEN          # Automatically provided
   TERMIUS_WEBHOOK_URL   # For notifications (optional)
   ```

## Automated Builds

### Workflow Triggers

The GHCR integration includes multiple automated build triggers:

1. **Push to main/develop branches**
   ```yaml
   on:
     push:
       branches: [ main, develop ]
   ```

2. **Version tags**
   ```yaml
   on:
     push:
       tags: [ 'v*' ]
   ```

3. **Scheduled builds (nightly)**
   ```yaml
   on:
     schedule:
       - cron: '0 2 * * *'  # 2 AM UTC daily
   ```

4. **Manual dispatch**
   ```yaml
   on:
     workflow_dispatch:
       inputs:
         build_type:
           type: choice
           options: [standard, multi-arch, security-scan, performance-test]
   ```

### Build Matrix

The system builds multiple image variants:

| Variant | Purpose | Platforms | Tags |
|---------|---------|-----------|------|
| **main** | Production ready | linux/amd64, linux/arm64 | `latest`, `stable`, `main` |
| **dev** | Development | linux/amd64 | `dev`, `develop` |
| **nightly** | Nightly builds | linux/amd64, linux/arm64 | `nightly` |

### Image Tags

| Tag Pattern | Description | Example |
|-------------|-------------|---------|
| `latest` | Latest stable release | `ghcr.io/utak-west/higherself-network-server:latest` |
| `stable` | Promoted stable build | `ghcr.io/utak-west/higherself-network-server:stable` |
| `main` | Main branch build | `ghcr.io/utak-west/higherself-network-server:main` |
| `v*` | Version tags | `ghcr.io/utak-west/higherself-network-server:v1.0.0` |
| `sha-*` | Commit-specific | `ghcr.io/utak-west/higherself-network-server:sha-abc123` |
| `nightly` | Nightly builds | `ghcr.io/utak-west/higherself-network-server:nightly` |

## Image Management

### Using the GHCR Manager Script

```bash
# Show status and available images
./scripts/ghcr-manager.sh status

# List all available tags
./scripts/ghcr-manager.sh list

# Pull specific image
./scripts/ghcr-manager.sh pull v1.0.0

# Build and push new image
./scripts/ghcr-manager.sh build v1.1.0

# Inspect image details
./scripts/ghcr-manager.sh inspect latest

# Test image functionality
./scripts/ghcr-manager.sh test stable

# Clean up old local images
./scripts/ghcr-manager.sh cleanup
```

### Manual Docker Commands

```bash
# Pull images
docker pull ghcr.io/utak-west/higherself-network-server:latest
docker pull ghcr.io/utak-west/thehigherselfnetworkserver:latest

# Build with GHCR tags
docker build -t ghcr.io/utak-west/higherself-network-server:custom .

# Push to GHCR
docker push ghcr.io/utak-west/higherself-network-server:custom

# Multi-platform build
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/utak-west/higherself-network-server:multi \
  --push .
```

## Deployment with GHCR

### Environment-Specific Deployment

#### Development
```bash
# Use development image
export DOCKER_IMAGE="ghcr.io/utak-west/higherself-network-server:dev"
docker-compose -f docker-compose.yml -f docker-compose.ghcr.yml up -d

# Or use the deployment script
./scripts/ghcr-manager.sh deploy development dev
```

#### Staging
```bash
# Use main branch image
export DOCKER_IMAGE="ghcr.io/utak-west/higherself-network-server:main"
./scripts/docker-terragrunt-deploy.sh staging deploy containers

# Or use GHCR manager
./scripts/ghcr-manager.sh deploy staging main
```

#### Production
```bash
# Use stable image
export DOCKER_IMAGE="ghcr.io/utak-west/higherself-network-server:stable"
./scripts/docker-terragrunt-deploy.sh production deploy containers

# Or use GHCR manager
./scripts/ghcr-manager.sh deploy production stable
```

### Docker Compose Integration

The `docker-compose.ghcr.yml` file provides GHCR-specific overrides:

```yaml
# Use GHCR image
services:
  higherself-server:
    image: ${DOCKER_IMAGE:-ghcr.io/utak-west/higherself-network-server:latest}
    environment:
      - CONTAINER_REGISTRY=ghcr.io
      - IMAGE_SOURCE=ghcr
      - DEPLOYMENT_METHOD=ghcr
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCKER_IMAGE` | Full GHCR image name and tag | `ghcr.io/utak-west/higherself-network-server:latest` |
| `DOCKER_IMAGE_TAG` | Image tag only | `latest` |
| `GITHUB_TOKEN` | GitHub authentication token | Required for private repos |
| `CONTAINER_REGISTRY` | Registry hostname | `ghcr.io` |

## Security and Compliance

### Security Scanning

Automated security scanning is integrated into the build process:

1. **Trivy Scanner**
   - Vulnerability scanning
   - SARIF output to GitHub Security tab
   - Critical/High severity blocking

2. **Grype Scanner**
   - Additional vulnerability detection
   - Comprehensive CVE database
   - Supply chain security

3. **SBOM Generation**
   - Software Bill of Materials
   - SPDX format
   - Attestation and signing

### Image Attestation

All images include cryptographic attestations:

```bash
# Verify image attestation
gh attestation verify oci://ghcr.io/utak-west/higherself-network-server:latest \
  --owner utak-west
```

### Access Control

GHCR images support fine-grained access control:

1. **Public Images**: Available to everyone
2. **Private Images**: Require authentication
3. **Organization Access**: Team-based permissions

## Troubleshooting

### Common Issues

#### 1. Authentication Failures

```bash
# Error: unauthorized: authentication required
# Solution: Login to GHCR
export GITHUB_TOKEN="your_token"
echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
```

#### 2. Image Not Found

```bash
# Error: pull access denied
# Check if image exists
./scripts/ghcr-manager.sh list

# Verify image name and tag
docker pull ghcr.io/utak-west/higherself-network-server:latest
```

#### 3. Build Failures

```bash
# Check GitHub Actions logs
# Verify Dockerfile syntax
docker build --no-cache -t test-image .

# Check build context
./scripts/ghcr-manager.sh build test-tag
```

#### 4. Multi-platform Issues

```bash
# Setup buildx for multi-platform
docker buildx create --use --name multiplatform
docker buildx inspect --bootstrap

# Build for specific platform
docker buildx build --platform linux/amd64 -t test-image .
```

### Debug Commands

```bash
# Check GHCR status
./scripts/ghcr-manager.sh status

# Test image functionality
./scripts/ghcr-manager.sh test latest

# Inspect image details
docker inspect ghcr.io/utak-west/higherself-network-server:latest

# Check image layers
docker history ghcr.io/utak-west/higherself-network-server:latest

# Verify image signatures
cosign verify ghcr.io/utak-west/higherself-network-server:latest
```

### Performance Optimization

1. **Layer Caching**
   ```dockerfile
   # Optimize Dockerfile for better caching
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   ```

2. **Multi-stage Builds**
   ```dockerfile
   FROM python:3.11-slim as builder
   # Build dependencies
   
   FROM python:3.11-slim as runtime
   # Runtime image
   ```

3. **Registry Caching**
   ```yaml
   cache-from: |
     type=registry,ref=ghcr.io/utak-west/higherself-network-server:cache
   cache-to: |
     type=registry,ref=ghcr.io/utak-west/higherself-network-server:cache,mode=max
   ```

## Best Practices

### 1. Image Tagging Strategy

- Use semantic versioning for releases (`v1.0.0`)
- Tag stable builds as `stable`
- Use branch names for development (`main`, `develop`)
- Include commit SHA for traceability

### 2. Security

- Scan all images before deployment
- Use minimal base images
- Keep dependencies updated
- Implement image signing

### 3. Performance

- Optimize Dockerfile for layer caching
- Use multi-stage builds
- Implement registry caching
- Monitor image sizes

### 4. Monitoring

- Track image pull metrics
- Monitor vulnerability scan results
- Set up alerts for failed builds
- Review SBOM reports regularly

## Integration with CI/CD

The GHCR integration works seamlessly with the existing CI/CD pipeline:

1. **Enhanced CI/CD** (`enhanced-cicd.yml`)
   - Main deployment pipeline
   - Includes GHCR builds
   - Production deployments

2. **GHCR Integration** (`ghcr-integration.yml`)
   - Dedicated GHCR workflows
   - Multi-platform builds
   - Security scanning

3. **Manual Management**
   - GHCR manager script
   - Local development
   - Testing and debugging

## Next Steps

1. **Configure GitHub Token** with appropriate permissions
2. **Set up automated builds** by pushing to main branch
3. **Test deployment** using GHCR images
4. **Monitor security scans** in GitHub Security tab
5. **Optimize build performance** with caching strategies

For additional support, refer to the [Comprehensive Deployment Guide](./COMPREHENSIVE_DEPLOYMENT_GUIDE.md) and [Docker Deployment Guide](./deployment/DOCKER_DEPLOYMENT.md).
